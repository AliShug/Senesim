import sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

import yaml

from senesim.scene import *
from senesim.config import *
from senesim import *


class Window(QWidget):

    def clear(self):
        for constraint in self.constraints:
            constraint.cleanup()
        self.constraints.clear()
        self.controllers.clear()
        for body in self.world.bodies:
            body.userData.cleanup()
        self.mouseDrag = None
        self.mouseJoint = None
        self.mouseItem = None
        self.controlPane.clear()

    def reset(self):
        '''Generates the world, including all bodies, joints, and elastics.'''
        self.clear()

        # Ground body
        self.groundBody = Body(self.world, self.scene)
        self.groundBody.initBox((0, -4), 10, 3, static=True)

        try:
            print('Loading {0}'.format(self.filePath))
            with open(self.filePath) as f:
                parsed = yaml.load(f.read())
        except IOError as e:
            print(e)

        bodies = {'_ground': self.groundBody}
        elastics = {}
        controllers = {}

        for body in parsed.get('bodies', []):
            new_body = Body(self.world, self.scene)
            density = body.get('density', default_density)
            friction = body.get('friction', default_friction)
            restitution = body.get('restitution', default_restitution)
            type = body.get('type', 'box')
            static = body.get('static', False)
            color = body.get('color', default_color)
            label = body.get('label', None)

            mass = body.get('mass', None)
            inertia = body.get('inertia', None)
            cog = body.get('cog', None)

            if type == 'box':
                new_body.initBox(body['pos'], body['width'], body['height'],
                                 density=density, restitution=restitution,
                                 friction=friction, static=static,
                                 label=label, color=color)
            elif type == 'circle':
                new_body.initCircle(body['pos'], body['radius'],
                                    density=density, restitution=restitution,
                                    friction=friction, static=static,
                                    label=label, color=color)
            else:
                raise Exception('Unknown body type {0}'.format(type))
            # Set mass properties, if provided
            if mass is not None:
                new_body.body.mass = mass
            if inertia is not None:
                new_body.body.inertia = inertia
            if cog is not None:
                new_body.body.localCenter = cog
            # Allows retrieval by ID for joints etc
            if 'id' in body:
                bodies[body['id']] = new_body

        for joint in parsed.get('joints', []):
            type = joint['type']
            if type == 'revolute':
                enableLimit = joint.get('enableLimit', False)
                lowerAngle = joint.get('lowerAngle', 0.0) * b2_pi
                upperAngle = joint.get('upperAngle', 0.0) * b2_pi
                collideConnected = joint.get('collideConnected', False)
                maxMotorTorque = joint.get('maxMotorTorque', 0.0)
                motorSpeed = joint.get('motorSpeed', 0.0)
                enableMotor = joint.get('enableMotor', False)
                referenceAngle = joint.get('referenceAngle', 0.0) * b2_pi

                self.world.CreateRevoluteJoint(
                    bodyA=bodies[joint['bodyA']].body,
                    bodyB=bodies[joint['bodyB']].body,
                    anchor=joint['anchor'],
                    enableLimit=enableLimit,
                    lowerAngle=lowerAngle,
                    upperAngle=upperAngle,
                    collideConnected=collideConnected,
                    maxMotorTorque=maxMotorTorque,
                    motorSpeed=motorSpeed,
                    enableMotor=enableMotor,
                    referenceAngle=referenceAngle)
            else:
                raise Exception('Unknown joint type {0}'.format(type))

        for elastic in parsed.get('elastics', []):
            new_elastic = Elastic(self.world, self.scene)
            k = elastic.get('k', 1)
            damp = elastic.get('damping', 1)
            new_elastic.initElastic(
                bodies[elastic['bodyA']].body,
                bodies[elastic['bodyB']].body,
                elastic['anchorA'],
                elastic['anchorB'],
                k, damping=damp)
            for contact in elastic.get('contacts', []):
                new_elastic.addContact(bodies[contact['body']].body,
                                       contact['point'])
            self.addConstraint(new_elastic)
            if 'id' in elastic:
                elastics[elastic['id']] = new_elastic

        for load in parsed.get('loads', []):
            body = bodies[load['body']].body
            anchor = load['anchor']
            max = load.get('max', 500)
            new_load = Load(self.world, self.scene, body, anchor, max)
            label = load.get('label', 'Unnamed Load')
            self.controlPane.addLoad(label, new_load)
            self.addConstraint(new_load)

        for controller in parsed.get('tendon-controllers', []):
            limit = controller.get('limit', 100)
            max_speed = controller.get('max-speed', 50)
            max_force = controller.get('max-force', 5000)
            new_controller = TendonController(elastics[controller['elastic']],
                                              controller['label'],
                                              limit=limit, max_force=max_force,
                                              max_speed=max_speed)
            self.addTendonController(new_controller)
            controllers[controller['elastic']] = new_controller

        for coupled_controller in parsed.get('coupled-controllers', []):
            extensor = controllers[coupled_controller['extensor']]
            flexor = controllers[coupled_controller['flexor']]
            new_controller = CoupledTendonController(extensor, flexor)
            label = coupled_controller['label']
            self.controlPane.addComboController(label, new_controller)

        for label in parsed.get('labels', []):
            pos = label['pos']
            text = label['text']
            new_label = Label(self.scene,
                              QPoint(pos[0]*world_scale, pos[1]*world_scale),
                              text)

        # mouse logic
        self.mouseDrag = MouseDrag(self)

    def __init__(self):
        QWidget.__init__(self)
        root_layout = QHBoxLayout(self)
        self.controlPane = ControlPane()
        root_layout.addWidget(self.controlPane)
        layout = QVBoxLayout()
        root_layout.addLayout(layout)
        buttonsLayout = QHBoxLayout()
        # Pause button stops physics calculations, but leaves application
        # responsive
        self.pauseButton = QPushButton('Toggle Pause', self)
        self.pauseButton.clicked.connect(self.togglePause)
        buttonsLayout.addWidget(self.pauseButton)
        # Reset button - resets the scene
        self.resetButton = QPushButton('Reset', self)
        self.resetButton.clicked.connect(self.reset)
        buttonsLayout.addWidget(self.resetButton)
        # Forces button - toggles force visibility
        self.forcesVisible = True
        self.forceButton = QPushButton('Toggle Force Display', self)
        self.forceButton.clicked.connect(self.toggleForces)
        buttonsLayout.addWidget(self.forceButton)
        # Label shows frame progression
        self.label = QLabel('Not started', self)
        buttonsLayout.addWidget(self.label)
        layout.addLayout(buttonsLayout)

        # begin ticking
        self._active = True
        self.paused = False
        QTimer.singleShot(0, self.runLoop)
        self.frame_n = 0

        # graphics
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.viewport().setFocusProxy(None)
        self.view.setRenderHints(
            QPainter.Antialiasing)
        # correct orientation
        self.view.scale(1, -1)
        layout.addWidget(self.view)
        self.view.viewport().installEventFilter(self)

        # physics
        self.world = b2World(warmStarting=world_warm_start)
        self.constraints = []
        self.controllers = []

        # File loading
        if len(sys.argv) > 1:
            self.filePath = sys.argv[1]
        else:
            self.filePath = 'default.yml'

        # Generate scene
        self.reset()

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
        elif event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                self.togglePause()
        return super(Window, self).eventFilter(source, event)

    def closeEvent(self, event):
        self._active = False

    def addConstraint(self, constraint):
        self.constraints.append(constraint)

    def addTendonController(self, controller):
        self.controlPane.addElasticController(controller)
        self.controllers.append(controller)

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
                    for controller in self.controllers:
                        controller.update(1 / world_fps)
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

    def toggleForces(self):
        if self.forcesVisible:
            self.forcesVisible = False
            for constraint in self.constraints:
                constraint.hideForces()
        else:
            self.forcesVisible = True
            for constraint in self.constraints:
                constraint.showForces()


    def viewToWorld(self, p):
        pScene = self.view.mapToScene(p)
        return (pScene.x() / world_scale, pScene.y() / world_scale)

    def viewToScene(self, p):
        return self.view.mapToScene(p)

    def sizeHint(self):
        return QSize(1024, 800)
