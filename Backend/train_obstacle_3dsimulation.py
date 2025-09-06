from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, Vec4, Vec3, TextNode, LineSegs
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
import time
from panda3d.core import ClockObject
globalClock = ClockObject.getGlobalClock()

class TrainSafetyDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Logging UI
        self.log_lines = []
        self.log_label = OnscreenText(
            text="", pos=(-1.3, 0.9), scale=0.05,
            fg=(1, 1, 1, 1), align=TextNode.ALeft, mayChange=True
        )

        # Camera view
        self.disableMouse()
        self.camera.setPos(0, -250, 120)
        self.camera.lookAt(0, 0, 0)

        # Lights
        self._setup_lights()

        # Track
        self._create_track()

        # Trains (opposite ends of same track)
        self.north_train = self._spawn_train("Northbound Train", (0.2, 0.7, 1, 1), pos=(0, 200, 0))
        self.south_train = self._spawn_train("Southbound Train", (1, 0.3, 0.3, 1), pos=(0, -200, 0))

        # Velocities
        self.vel_north = -3.0
        self.vel_south = 3.0

        # Braking control
        self.brake_north = False
        self.brake_south = False

        self.min_gap = 60.0

        # Start loop
        self.taskMgr.add(self._update, "UpdateTask")

    # Logging
    def _log(self, msg):
        t = time.strftime("[%H:%M:%S] ")
        line = t + msg
        print(line)
        self.log_lines.append(line)
        if len(self.log_lines) > 12:
            self.log_lines.pop(0)
        self.log_label.setText("\n".join(self.log_lines))

    # Lights
    def _setup_lights(self):
        dlight = DirectionalLight("dlight")
        dlight.setColor(Vec4(0.9, 0.9, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -60, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight("alight")
        alight.setColor(Vec4(0.4, 0.4, 0.45, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
    
    def _create_track(self):
        ls = LineSegs()
        ls.setThickness(4.0)
        ls.setColor(0.8, 0.8, 0.8, 1)

        # left rail
        ls.moveTo(-4, -250, -6.5)
        ls.drawTo(-4, 250, -6.5)

        # right rail
        ls.moveTo(4, -250, -6.5)
        ls.drawTo(4, 250, -6.5)

        return self.render.attachNewNode(ls.create())

    # Train Cube
    def _spawn_train(self, name, color, pos):
        from panda3d.core import CardMaker, NodePath
        train = NodePath(name)
        size = 6
        cm = CardMaker("side")
        cm.setFrame(-size, size, -size/2, size/2)
        for h in [0, 90, 180, 270]:
            card = train.attachNewNode(cm.generate())
            card.setHpr(h, 0, 0)
            card.setColor(color)
        tb = CardMaker("tb")
        tb.setFrame(-size, size, -size, size)
        top = train.attachNewNode(tb.generate())
        top.setHpr(0, 90, 0); top.setZ(size/2); top.setColor(color)
        bot = train.attachNewNode(tb.generate())
        bot.setHpr(0, -90, 0); bot.setZ(-size/2); bot.setColor(color)

        train.reparentTo(self.render)
        train.setPos(pos)
        return train

    # Update Loop
    def _update(self, task):
        dt = globalClock.getDt()

        # move trains
        self.north_train.setY(self.north_train.getY() + self.vel_north * dt)
        self.south_train.setY(self.south_train.getY() + self.vel_south * dt)

        # compute distance
        dist = abs(self.north_train.getY() - self.south_train.getY())

        stopping_north = (abs(self.vel_north)**2) / (2*0.5)
        stopping_south = (abs(self.vel_south)**2) / (2*0.5)
        
        #if dist < 300 and (self.vel_north > 0.01 or self.vel_south > 0.01):
        #    self._log(f"🧠 AI inference: distance={dist:.1f} m | "
        #      f"North stop={stopping_north:.1f} m, South stop={stopping_south:.1f} m")
        
        if dist < 300 and not self.brake_north:
            self._log("📸 Camera(North) sees train ahead")
            if dist < stopping_north + self.min_gap:
                self._log("🛑 Decision: Northbound Train brakes!")
                self.brake_north = True
        
        if dist < 300 and not self.brake_south:
            self._log("📸 Camera(South) sees train ahead")
            if dist < stopping_south + self.min_gap:
                self._log("🛑 Decision: Southbound Train brakes!")
                self.brake_south = True

        # Smooth braking of northbound train
        if self.brake_north and self.vel_north < 0:
            self.vel_north += 0.4 * dt  # since negative
            if self.vel_north >= 0:
                self.vel_north = 0
                self._log("✅ Northbound Train stopped safely.")

        if self.brake_south and self.vel_south > 0:
            self.vel_south -= 0.4 * dt
            if self.vel_south <= 0:
                self.vel_south = 0
                self._log("✅ Southbound Train stopped safely.")

        return Task.cont

# Run
app = TrainSafetyDemo()
app.run()