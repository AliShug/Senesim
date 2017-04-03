from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *


class Load(object):
    def __init__(self, world, scene, body, anchor):
        self.world = world
        self.scene = scene
        self.body = body
        self.anchor = body.GetLocalPoint(anchor)
        self.force = b2Vec2(0, 0)
        self.line = self.scene.addLine(
            self.getLineDef(),
            QPen(Qt.green, 4))

    def setForce(self, force):
        self.force = b2Vec2(force)

    def getLineDef(self):
        a = self.body.GetWorldPoint(self.anchor)
        b = (a + self.force/100) * world_scale
        a = a * world_scale
        return QLineF(a.x, a.y, b.x, b.y)

    def updateGraphics(self):
        self.line.setLine(self.getLineDef())

    def updateForces(self, delta_t):
        a = self.body.GetWorldPoint(self.anchor)
        self.body.ApplyForce(self.force, a, True)

    def cleanup(self):
        if self.line:
            self.scene.removeItem(self.line)
            self.line = None
