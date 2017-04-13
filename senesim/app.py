from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim.scene import *
from senesim.config import *
from senesim import *


class Window(QWidget):

    def clear(self):
        for constraint in self.constraints:
            constraint.cleanup()
        self.constraints.clear()
        for body in self.world.bodies:
            body.userData.cleanup()
        self.mouseDrag = None
        self.mouseJoint = None
        self.mouseItem = None

    def reset(self):
        '''Generates the world, including all bodies, joints, and elastics.'''
        self.clear()

        # Ground body
        self.groundBody = Body(self.world, self.scene)
        self.groundBody.initBox((0, -4), 10, 3, static=True)
        leftWall = Body(self.world, self.scene)
        leftWall.initBox((-10, 5), 1, 10, static=True)
        rightWall = Body(self.world, self.scene)
        rightWall.initBox((10, 5), 1, 10, static=True)

        # Label(self.scene, QPoint(10, 30), 'Arm')

        # elastic-supported arm
        arm_color = QColor.fromRgbF(0.8, 0.8, 1)
        A = Body(self.world, self.scene)
        A.initBox(
            (0, 1.5),
            0.2, 1.5,
            label='A',
            color=arm_color)
        self.world.CreateRevoluteJoint(
            bodyA=self.groundBody.body,
            bodyB=A.body,
            anchor=(0, 0),
            enableLimit=True,
            lowerAngle=-0.3 * b2_pi,
            upperAngle=0.2 * b2_pi)

        B = Body(self.world, self.scene)
        B.initBox((1, 3), 2, 0.1, label='B', color=arm_color)
        self.world.CreateRevoluteJoint(
            bodyA=A.body,
            bodyB=B.body,
            anchor=(0, 3),
            enableLimit=True,
            lowerAngle=-0.4 * b2_pi,
            upperAngle=0.1 * b2_pi)

        # Body A tendons
        k = 400
        a1 = Elastic(self.world, self.scene)
        a1.initElastic(self.groundBody.body, A.body, (0, -1), (-1.0, 0), k)
        a1.addContact(self.groundBody.body, (-0.6,-0.7))
        self.addConstraint(a1)
        a2 = Elastic(self.world, self.scene)
        a2.initElastic(self.groundBody.body, A.body, (0, -1), (1.0, 0), k)
        a2.addContact(self.groundBody.body, (0.6,-0.7))
        self.addConstraint(a2)

        # Body B tendons
        b1 = Elastic(self.world, self.scene)
        b1.initElastic(self.groundBody.body, B.body, (-1, -1), (-0.6, 3), k)
        b1.addContact(A.body, (-0.6, 0.5))
        self.addConstraint(b1)
        b2 = Elastic(self.world, self.scene)
        b2.initElastic(self.groundBody.body, B.body, (1, -1), (0.6, 3), k)
        b2.addContact(A.body, (0.6, 0.5))
        self.addConstraint(b2)

        # Arm load
        self.load = Load(self.world, self.scene, B.body, (3, 3))
        self.addConstraint(self.load)

        # extras
        for i in range(10):
            body = Body(self.world, self.scene)
            body.initBox((-2, i + 1), 0.4, 0.4)

        leftPole = Body(self.world, self.scene)
        leftPole.initBox((-3, 7), 0.2, 0.2, static=True)
        rightPole = Body(self.world, self.scene)
        rightPole.initBox((1, 5), 0.2, 0.2, static=True)
        ball = Body(self.world, self.scene)
        ball.initCircle((0, 4.85), 0.2)
        rope = Elastic(self.world, self.scene)
        rope.initElastic(leftPole.body, rightPole.body, (-3,7), (1,5), 1)
        rope.addContact(ball.body, (0,5))
        self.addConstraint(rope)

        # mouse logic
        self.mouseDrag = MouseDrag(self)

    def __init__(self):
        QWidget.__init__(self)
        root_layout = QHBoxLayout(self)
        self.controlPane = ControlPane()
        root_layout.addWidget(self.controlPane)
        layout = QVBoxLayout()
        root_layout.addLayout(layout)
        # Reset button - resets the scene
        buttonsLayout = QHBoxLayout()
        self.pauseButton = QPushButton('Toggle Pause', self)
        self.pauseButton.clicked.connect(self.togglePause)
        buttonsLayout.addWidget(self.pauseButton)
        self.resetButton = QPushButton('Reset', self)
        self.resetButton.clicked.connect(self.reset)
        buttonsLayout.addWidget(self.resetButton)
        self.label = QLabel('Not started', self)
        buttonsLayout.addWidget(self.label)
        layout.addLayout(buttonsLayout)
        # Loading slider
        sliderLayout = QHBoxLayout()
        self.loadSlider = QSlider(Qt.Horizontal)
        self.loadSlider.setMinimum(0)
        self.loadSlider.setMaximum(300)
        self.loadSlider.setValue(0)
        self.loadSlider.setTickPosition(QSlider.TicksBelow)
        self.loadSlider.setTickInterval(10)
        self.loadSlider.valueChanged.connect(self.sliderChange)
        sliderLayout.addWidget(QLabel('Load (N):'))
        sliderLayout.addWidget(self.loadSlider)
        self.loadInput = QLineEdit()
        self.loadInput.setMaximumWidth(80)
        self.loadInput.setText('0')
        self.loadInput.textChanged.connect(self.textChange)
        sliderLayout.addWidget(self.loadInput)
        layout.addLayout(sliderLayout)
        # begin ticking
        self._active = True
        self.paused = False
        QTimer.singleShot(0, self.runLoop)
        self.frame_n = 0

        # graphics
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(
            QPainter.Antialiasing)
        # correct orientation
        self.view.scale(1, -1)
        self.scene.addEllipse(0, 0, 5, 5)
        layout.addWidget(self.view)
        self.view.viewport().installEventFilter(self)

        # physics
        self.world = b2World(warmStarting=world_warm_start)
        self.constraints = []

        # Generate scene
        self.reset()

    def sliderChange(self):
        self.changeLoad(self.loadSlider.value())

    def textChange(self):
        try:
            val = int(self.loadInput.text())
            self.changeLoad(int(self.loadInput.text()))
        except:
            pass

    def changeLoad(self, value):
        self.load.setForce((0, -value))
        self.loadSlider.setValue(value)
        self.loadInput.setText(str(value))

    def eventFilter(self, source, event):
        """Event filter for graphicsview interaction"""
        if event.type() == QEvent.MouseMove:
            # if event.buttons() == Qt.NoButton:
            #     print("Simple mouse motion")
            if event.buttons() == Qt.LeftButton:
                self.mouseDrag.mouseMove(event.pos())
            # elif event.buttons() == Qt.RightButton:
            #     print("Right click drag")
        elif event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.mouseDrag.mouseDown(event.pos())
        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.mouseDrag.mouseUp(event.pos())
        return super(Window, self).eventFilter(source, event)

    def closeEvent(self, event):
        self._active = False

    def addConstraint(self, constraint):
        self.constraints.append(constraint)

    def togglePause(self):
        self.paused = not self.paused

    def runLoop(self):
        from time import sleep
        self.frame_n = 0
        while True:
            sleep(0.01)
            if not self.paused:
                self.frame_n = self.frame_n + 1
                self.label.setText('Frame %d' % self.frame_n)
                # physics update
                for i in range(world_outer_iterations):
                    for constraint in self.constraints:
                        constraint.updateForces(1 / world_fps)
                    self.world.Step(
                        1 / world_fps,
                        world_iterations,
                        world_iterations)
                    if world_clear_forces:
                        self.world.ClearForces()
                # graphics update
                self.mouseDrag.updateGraphics()
                for body in self.world.bodies:
                    if body.userData:
                        body.userData.updateGraphics()
                for constraint in self.constraints:
                    constraint.updateGraphics()
            # Keep the app running
            qApp.processEvents()
            if not self._active:
                break

    def viewToWorld(self, p):
        pScene = self.view.mapToScene(p)
        return (pScene.x() / world_scale, pScene.y() / world_scale)

    def viewToScene(self, p):
        return self.view.mapToScene(p)

    def sizeHint(self):
        return QSize(1024, 800)
