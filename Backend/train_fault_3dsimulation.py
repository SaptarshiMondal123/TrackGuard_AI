# train_sim_api.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
import time, os, cv2, numpy as np, signal, shutil

from panda3d.core import (
    loadPrcFileData, AmbientLight, DirectionalLight, Vec4, LineSegs,
    ClockObject, CardMaker, NodePath, TextNode
)
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.OnscreenText import OnscreenText

# === Panda3D offscreen settings ===
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
# keep a fixed window size so video frame size stays consistent
loadPrcFileData("", "win-size 1280 720")

globalClock = ClockObject.getGlobalClock()
VIDEO_PATH = "output/simulation.mp4"

class TrainSafetyDemo(ShowBase):
    def __init__(self, record=False):
        # avoid Panda3D trying to install signal handlers (helpful when called from server)
        signal.signal = lambda *a, **k: None
        ShowBase.__init__(self)

        self.record = record
        self.frames = []
        self.finished = False

        # ===== simulation state =====
        self.sim_time = 0.0
        self._last_status_log_t = 0.0
        self._status_interval = 0.25  # seconds between telemetry logs
        self._fault_logged = False
        self._brake_logged = False
        self._stopped_logged = False
        self._post_stop_hold = 1.5  # seconds to hold overlay after stop
        self._stop_time = None

        # === visual overlay (OnscreenText) - will be included in offscreen renders
        self.log_lines = []
        self.log_label = OnscreenText(
            text="", pos=(-1.3, 0.9), scale=0.05,
            fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True
        )

        # camera
        self.disableMouse()
        self.camera.setPos(0, -250, 120)
        self.camera.lookAt(0, 0, 0)

        # lights and track
        self._setup_lights()
        self._create_track()

        # track fault marker (bright red bar)
        self.fault_y = 50
        cm = CardMaker("fault_marker")
        cm.setFrame(-6, 6, -0.5, 0.5)
        fault_marker = self.render.attachNewNode(cm.generate())
        fault_marker.setPos(0, self.fault_y, -6.5)
        fault_marker.setColor(1, 0, 0, 1)

        # train
        self.south_train = self._spawn_train("Southbound Train", (1, 0.3, 0.3, 1), (0, -200, 0))
        self.vel_south = 3.0
        self.brake_south = False
        self.min_gap = 60.0

        # add the update task
        self.taskMgr.add(self._update, "UpdateTask")

    def _log(self, msg):
        """Add a message to the overlay and print it (console)."""
        print(msg)
        self.log_lines.append(msg)
        if len(self.log_lines) > 12:
            self.log_lines.pop(0)
        self.log_label.setText("\n".join(self.log_lines))

    def _setup_lights(self):
        dlight = DirectionalLight("dlight")
        dlight.setColor(Vec4(0.9, 0.9, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight("alight")
        alight.setColor(Vec4(0.4, 0.4, 0.45, 1))
        self.render.setLight(self.render.attachNewNode(alight))

    def _create_track(self):
        ls = LineSegs()
        ls.setThickness(4.0)
        ls.setColor(0.8, 0.8, 0.8, 1)
        ls.moveTo(-4, -250, -6.5); ls.drawTo(-4, 250, -6.5)
        ls.moveTo(4, -250, -6.5); ls.drawTo(4, 250, -6.5)
        self.render.attachNewNode(ls.create())

    def _spawn_train(self, name, color, pos):
        train = NodePath(name)
        size = 6
        cm = CardMaker("side")
        cm.setFrame(-size, size, -size/2, size/2)
        for h in [0, 90, 180, 270]:
            card = train.attachNewNode(cm.generate())
            card.setHpr(h, 0, 0)
            card.setColor(color)
        tb = CardMaker("tb"); tb.setFrame(-size, size, -size, size)
        top = train.attachNewNode(tb.generate()); top.setHpr(0,90,0); top.setZ(size/2); top.setColor(color)
        bot = train.attachNewNode(tb.generate()); bot.setHpr(0,-90,0); bot.setZ(-size/2); bot.setColor(color)
        train.reparentTo(self.render)
        train.setPos(pos)
        return train

    def _update(self, task):
        dt = globalClock.getDt()
        self.sim_time += dt

        # move the train if not fully stopped
        if self.vel_south > 0.0:
            self.south_train.setY(self.south_train.getY() + self.vel_south * dt)

        # compute distance and stopping distance
        train_y = self.south_train.getY()
        dist_fault = abs(train_y - self.fault_y)
        stopping_south = (abs(self.vel_south) ** 2) / (2 * 0.5)  # a = 0.5

        # continuous detection while approaching (periodic to avoid spam)
        if dist_fault < 300 and self.vel_south > 0:
            if self.sim_time - self._last_status_log_t >= self._status_interval:
                self._last_status_log_t = self.sim_time
                # show the same short message repeatedly (as requested)
                self._log(f"📸 Camera detects TRACK FAULT ahead at y={self.fault_y}")

        # one-time braking decision (when we are within stopping_south + min_gap)
        if dist_fault < stopping_south + self.min_gap and not self.brake_south:
            self._log("🛑 Decision: Train brakes due to TRACK FAULT!")
            self.brake_south = True

        # smooth braking when brake engaged
        if self.brake_south and self.vel_south > 0:
            self.vel_south = max(0.0, self.vel_south - 0.4 * dt)
            if self.vel_south == 0.0 and not self._stopped_logged:
                self._log("✅ Train stopped safely before TRACK FAULT.")
                self._stopped_logged = True
                self._stop_time = self.sim_time

        # after stop, hold overlay for a short while so message is visible in the video
        if self._stopped_logged and (self.sim_time - self._stop_time) >= self._post_stop_hold:
            # finalize video and end
            self._finalize_video()
            self.finished = True
            return Task.done

        # record frame (grab offscreen buffer). Convert to contiguous array for OpenCV.
        if self.record and self.win is not None:
            tex = self.win.getScreenshot()
            # getRamImageAs returns bytes in row-major, we reshape accordingly
            arr = np.frombuffer(tex.getRamImageAs("RGB"), dtype=np.uint8)
            try:
                arr = arr.reshape((tex.getYSize(), tex.getXSize(), 3))
            except Exception:
                # fail-safe: try swapped shape
                arr = arr.reshape((tex.getXSize(), tex.getYSize(), 3))
            arr = np.flipud(arr).copy()  # flip vertical and make contiguous copy
            self.frames.append(arr)

        return Task.cont

    def _finalize_video(self):
        """Write frames to a temp AVI then compress with ffmpeg if present."""
        if not self.record or not self.frames:
            return
        os.makedirs("output", exist_ok=True)
        h, w, _ = self.frames[0].shape

        tmp_path = "output/tmp.avi"
        out = cv2.VideoWriter(tmp_path, cv2.VideoWriter_fourcc(*"XVID"), 30, (w, h))
        for f in self.frames:
            out.write(f)
        out.release()

        ffmpeg_exists = shutil.which("ffmpeg") is not None
        if ffmpeg_exists:
            # compress & convert to MP4 H.264
            cmd = f'ffmpeg -hide_banner -loglevel error -y -i "{tmp_path}" -vcodec libx264 -crf 28 -preset fast "{VIDEO_PATH}"'
            os.system(cmd)
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            self._log(f"🎥 Compressed video saved to {VIDEO_PATH}")
        else:
            # fallback: write MP4 using mp4v codec (less efficient)
            fallback_path = "output/simulation_fallback.mp4"
            out2 = cv2.VideoWriter(fallback_path, cv2.VideoWriter_fourcc(*"mp4v"), 30, (w, h))
            for f in self.frames:
                out2.write(f)
            out2.release()
            try:
                os.replace(fallback_path, VIDEO_PATH)
                os.remove(tmp_path)
            except OSError:
                pass
            self._log(f"🎥 Video saved (fallback encoder) to {VIDEO_PATH}")

# FastAPI app
app = FastAPI()

@app.post("/run_simulation")
async def run_simulation():
    """
    Run an offscreen Panda3D simulation, record frames and return the produced MP4.
    This endpoint runs the simulation synchronously (blocks until done) and returns the final file.
    """
    # create demo and step the Panda3D task manager until demo.finished is True
    demo = TrainSafetyDemo(record=True)
    # step loop -- this runs inside the server process, synchronous
    while not demo.finished:
        demo.taskMgr.step()
        time.sleep(1 / 60.0)  # step at ~60Hz
    # at this point VIDEO_PATH should exist
    if os.path.exists(VIDEO_PATH):
        return FileResponse(VIDEO_PATH, media_type="video/mp4", filename="simulation.mp4")
    return {"error": "Simulation finished but video file not found."}
