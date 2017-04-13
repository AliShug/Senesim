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
        self.contacts = []

    def initElastic(self, bodyA, bodyB, anchorA, anchorB, elastic_k, restLength=None):
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.localAnchorA = bodyA.GetLocalPoint(anchorA)
        self.localAnchorB = bodyB.GetLocalPoint(anchorB)
        self.k = elastic_k
        self.graphics = [self.scene.addLine(0,0,0,0)]
        self.forceLineA = self.scene.addLine(0,0,0,0, QPen(Qt.red, 3))
        self.forceLineB = self.scene.addLine(0,0,0,0, QPen(Qt.blue, 3))
        if restLength:
            self.restLength = restLength
            self.calculatedRestLength = False
        else:
            self.restLength = self.getLength()
            self.calculatedRestLength = True
        self.last_extension = 0

    def addContact(self, body, point):
        '''Adds a frictionless contact point. Points must be added in order,
        from bodyA/anchorA to bodyB/anchorB. Contacts route the elastic through
        different bodies, and (DON'T) apply forces to those bodies according to
        the elastic tension. If no rest length was provided at init, this
        recalculates the resting length at the current position.'''
        pointLocal = body.GetLocalPoint(point)
        self.contacts.append({
            'body': body,
            'point': pointLocal
        })
        self.graphics.append(self.scene.addLine(0,0,0,0))
        if self.calculatedRestLength:
            self.restLength = self.getLength()

    def updateForces(self, delta_t):
        # Forces model simple elastic stress, and dependent on strain
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
        if len(self.contacts) > 0:
            contact = self.contacts[0]
            c0 = contact['body'].GetWorldPoint(contact['point'])
            contact = self.contacts[-1]
            ci = contact['body'].GetWorldPoint(contact['point'])
        else:
            c0 = b
            ci = a
        dir_a = c0 - a
        dir_a.Normalize()
        force_a = dir_a * f
        dir_b = ci - b
        dir_b.Normalize()
        force_b = dir_b * f
        # Apply Forces
        self.bodyA.ApplyForce(force=force_a, point=a, wake=True)
        self.bodyB.ApplyForce(force=force_b, point=b, wake=True)
        # TODO: Contact forces
        # Display
        self.forceLineA.setLine(
            a.x * world_scale, a.y * world_scale,
            a.x * world_scale + force_a.x/10,
            a.y * world_scale + force_a.y/10)
        self.forceLineB.setLine(
            b.x * world_scale, b.y * world_scale,
            b.x * world_scale + force_b.x/10,
            b.y * world_scale + force_b.y/10)
        self.last_extension = extension

    def getStartPoint(self):
        return self.bodyA.GetWorldPoint(self.localAnchorA) * world_scale

    def getEndPoint(self):
        return self.bodyB.GetWorldPoint(self.localAnchorB) * world_scale

    def getLineDefs(self):
        '''Returns a list of QLineF segments which describe the elastic element
        (its shape) in physical space.'''
        # Build line segments
        p_start = self.getStartPoint()
        p_end = self.getEndPoint()
        segments = []
        last_p = p_start
        for contact in self.contacts:
            c = contact['body'].GetWorldPoint(contact['point']) * world_scale
            segments.append(QLineF(last_p.x, last_p.y, c.x, c.y))
            last_p = c
        segments.append(QLineF(last_p.x, last_p.y, p_end.x, p_end.y))
        return segments

    def updateGraphics(self):
        segments = self.getLineDefs()
        graphics_itr = iter(self.graphics)
        for line in segments:
            graphics_line = next(graphics_itr)
            graphics_line.setLine(line)

    def getLength(self):
        length = 0
        for line in self.getLineDefs():
            length += line.length()
        return length

    def cleanup(self):
        for graphics_line in self.graphics:
            self.scene.removeItem(graphics_line)
        self.scene.removeItem(self.forceLineA)
        self.scene.removeItem(self.forceLineB)
        del self.bodyA
        del self.bodyB
