from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *


class Elastic(object):

    def __init__(self, world, scene):
        self.world = world
        self.scene = scene

    def initElastic(self, bodyA, bodyB, anchorA, anchorB, elastic_k, restLength=None):
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.localAnchorA = bodyA.GetLocalPoint(anchorA)
        self.localAnchorB = bodyB.GetLocalPoint(anchorB)
        self.k = elastic_k
        self.graphics = self.scene.addLine(self.getLineDef())
        self.forceLineA = self.scene.addLine(
            self.getLineDef(), QPen(Qt.red, 3))
        self.forceLineB = self.scene.addLine(
            self.getLineDef(), QPen(Qt.blue, 3))
        if restLength:
            self.restLength = restLength
        else:
            self.restLength = self.getLength()
        self.last_extension = 0

    def getLineDef(self):
        a = self.bodyA.GetWorldPoint(self.localAnchorA) * world_scale
        b = self.bodyB.GetWorldPoint(self.localAnchorB) * world_scale
        return QLineF(a.x, a.y, b.x, b.y)

    def updateForces(self, delta_t):
        # Forces are symmetric, and dependent on extension
        a = self.bodyA.GetWorldPoint(self.localAnchorA)
        b = self.bodyB.GetWorldPoint(self.localAnchorB)
        extension = self.getLength() - self.restLength
        extension_rate = (extension - self.last_extension) / delta_t
        if extension > 0:
            resistance = self.k * extension_rate * 0.02
            elastic_force = self.k * extension
        else:
            resistance = 0
            elastic_force = 0

        f = resistance + elastic_force
        force_ab = b - a
        force_ab.Normalize()
        force_ab = force_ab * f
        force_ba = -force_ab
        # Apply Forces
        self.bodyA.ApplyForce(force=force_ab, point=a, wake=True)
        self.bodyB.ApplyForce(force=force_ba, point=b, wake=True)
        # Display
        self.forceLineA.setLine(
            a.x * world_scale, a.y * world_scale,
            a.x * world_scale + force_ab.x/10,
            a.y * world_scale + force_ab.y/10)
        self.forceLineB.setLine(
            b.x * world_scale, b.y * world_scale,
            b.x * world_scale + force_ba.x/10,
            b.y * world_scale + force_ba.y/10)
        self.last_extension = extension

    def updateGraphics(self):
        self.graphics.setLine(self.getLineDef())

    def getLength(self):
        line = self.getLineDef()
        return line.length()

    def cleanup(self):
        self.scene.removeItem(self.graphics)
        self.scene.removeItem(self.forceLineA)
        self.scene.removeItem(self.forceLineB)
        del self.bodyA
        del self.bodyB
