from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *
from senesim.scene import *


class MouseDrag(object):

    def __init__(self, app):
        self.app = app
        self.world = app.world
        self.view = app.view
        self.scene = app.scene
        self.groundBody = app.groundBody
        self.label = None
        self.joint = None
        self.target = None
        self.line = None
        self.p = None
        self.mouseDrag = False
        self.body = None


    def mouseDown(self, p):
        self.target = self.view.itemAt(p)
        if self.target and not self.target == self.groundBody.graphics:
            data = self.target.data(0)
            if data:
                self.body = data.body
                self.mouseDrag = True
                # map point
                scene_pt = self.app.viewToWorld(p)
                self.joint = self.world.CreateMouseJoint(
                    bodyA=self.groundBody.body,
                    bodyB=self.body,
                    target=scene_pt,
                    maxForce=8000,
                    collideConnected=True)
                self.body.awake = True
                self.p = p
                self.startPt = self.body.GetLocalPoint(scene_pt)
                self.createGraphics()

    def mouseUp(self, p):
        if self.joint:
            self.world.DestroyJoint(self.joint)
            self.joint = None
        self.mouseDrag = False
        self.target = None
        self.destroyGraphics()

    def mouseMove(self, p):
        if self.mouseDrag and self.joint:
            self.joint.target = self.app.viewToWorld(p)
            self.p = p
            self.updateGraphics()
        else:
            self.mouseDown(p)

    def createGraphics(self):
        self.label = Label(self.scene, self.p)
        self.line = self.scene.addLine(
            self.p.x(), self.p.y(),
            self.p.x(), self.p.y(),
            QPen(Qt.yellow, 3))

    def updateGraphics(self):
        if not self.joint:
            return
        scene_mouse = self.app.viewToScene(self.p)
        if self.label:
            self.label.setPos(scene_mouse)
            force = self.joint.GetReactionForce(world_fps)
            self.label.setText(
                '[{0:.2f}N,{1:.2f}N]'.format(force.x, force.y))
        if self.line:
            worldPt = self.body.GetWorldPoint(self.startPt)
            self.line.setLine(
                worldPt.x*world_scale,
                worldPt.y*world_scale,
                scene_mouse.x(), scene_mouse.y()
            )

    def destroyGraphics(self):
        if self.label:
            self.label.cleanup()
            self.label = None
        if self.line:
            self.scene.removeItem(self.line)
            self.line = None

    def cleanup(self):
        self.mouseUp()
