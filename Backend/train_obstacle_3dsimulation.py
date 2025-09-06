# two_train_api.py
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

# ==== Panda3D Offscreen Mode ====
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "win-size 1280 720")

globalClock = ClockObject.getGlobalClock()
VIDEO_PATH = "output/two_train_simulation.mp4"

class TwoTrainSafetyDemo(ShowBase):
    def __init__(self, record=False):
        # Disable Panda3D's signal hook
        signal.signal = lambda *a, **k: None
        ShowBase.__init__(self)

        self.record = record
        self.frames = []
        self.finished = False
        self.sim_time = 0.0
        self._post_stop_hold = 1.5
        self._stop_time = None

        # Log overlay
        self.log_lines = []
        self.log_label = OnscreenText(
            text="", pos=(-1.3, 0.9), scale=0.05,
            fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True
        )

        # Camera
        self.disableMouse()
        self.camera.setPos(0, -250, 120)
        self.camera.lookAt(0, 0, 0)

        # Lights + Track
        self._setup_lights()
        self._create_track()

        # Trains (opposite directions)
        self.north_train = self._spawn_train("Northbound Train", (0.2, 0.7, 1, 1), (0, 200, 0))
        self.south_train = self._spawn_train("Southbound Train", (1, 0.3, 0.3, 1), (0, -200, 0))

        # Velocities
        self.vel_north = -3.0
        self.vel_south = 3.0

        # Braking flags
        self.brake_north = False
        self.brake_south = False
        self.min_gap = 60.0

        self.taskMgr.add(self._update, "UpdateTask")

    def _log(self, msg):
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
        size = 6
        train = NodePath(name)
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

        # Move trains
        if self.vel_north < 0:
            self.north_train.setY(self.north_train.getY() + self.vel_north * dt)
        if self.vel_south > 0:
            self.south_train.setY(self.south_train.getY() + self.vel_south * dt)

        # Distance and stopping distances
        dist = abs(self.north_train.getY() - self.south_train.getY())
        stop_north = (abs(self.vel_north)**2) / (2*0.5)
        stop_south = (abs(self.vel_south)**2) / (2*0.5)

        # Detection and braking
        if dist < 300 and not self.brake_north:
            self._log("📸 Camera(North) sees train ahead")
            if dist < stop_north + self.min_gap:
                self._log("🛑 Decision: Northbound Train brakes!")
                self.brake_north = True

        if dist < 300 and not self.brake_south:
            self._log("📸 Camera(South) sees train ahead")
            if dist < stop_south + self.min_gap:
                self._log("🛑 Decision: Southbound Train brakes!")
                self.brake_south = True

        # Smooth braking
        if self.brake_north and self.vel_north < 0:
            self.vel_north = min(0.0, self.vel_north + 0.4 * dt)
            if self.vel_north == 0:
                self._log("✅ Northbound Train stopped safely.")

        if self.brake_south and self.vel_south > 0:
            self.vel_south = max(0.0, self.vel_south - 0.4 * dt)
            if self.vel_south == 0:
                self._log("✅ Southbound Train stopped safely.")

        # If both stopped, end sim after hold time
        if self.vel_north == 0 and self.vel_south == 0 and not self.finished:
            if self._stop_time is None:
                self._stop_time = self.sim_time
            elif self.sim_time - self._stop_time >= self._post_stop_hold:
                self._finalize_video()
                self.finished = True
                return Task.done

        # Record frame
        if self.record and self.win is not None:
            tex = self.win.getScreenshot()
            arr = np.frombuffer(tex.getRamImageAs("RGB"), dtype=np.uint8)
            arr = arr.reshape((tex.getYSize(), tex.getXSize(), 3))
            arr = np.flipud(arr).copy()
            self.frames.append(arr)

        return Task.cont

    def _finalize_video(self):
        if not self.record or not self.frames:
            return
        os.makedirs("output", exist_ok=True)
        h, w, _ = self.frames[0].shape

        tmp_path = "output/tmp.avi"
        out = cv2.VideoWriter(tmp_path, cv2.VideoWriter_fourcc(*"XVID"), 30, (w, h))
        for f in self.frames:
            out.write(f)
        out.release()

        if shutil.which("ffmpeg"):
            os.system(f'ffmpeg -y -i {tmp_path} -vcodec libx264 -crf 28 -preset fast {VIDEO_PATH}')
            os.remove(tmp_path)
        else:
            os.rename(tmp_path, VIDEO_PATH)

# ==== FastAPI App ====
app = FastAPI()

@app.post("/run_simulation")
async def run_simulation():
    demo = TwoTrainSafetyDemo(record=True)
    while not demo.finished:
        demo.taskMgr.step()
        time.sleep(1/60)
    return FileResponse(VIDEO_PATH, media_type="video/mp4", filename="two_train_simulation.mp4")