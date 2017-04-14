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
        self.label = 'Unnamed'

    def initElastic(self, bodyA, bodyB, anchorA, anchorB, elastic_k, restLength=None):
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.localAnchorA = bodyA.GetLocalPoint(anchorA)
        self.localAnchorB = bodyB.GetLocalPoint(anchorB)
        self.k = elastic_k
        self.graphics = [self.scene.addLine(0,0,0,0)]
        self.forceLineA = self.scene.addLine(0,0,0,0, QPen(Qt.red, 3))
        self.forceLineB = self.scene.addLine(0,0,0,0, QPen(Qt.blue, 3))
        self.contactForceLines = []
        if restLength:
            self.restLength = restLength
            self.calculatedRestLength = False
        else:
            self.restLength = self.getLength()
            self.calculatedRestLength = True
        self.last_extension = 0

    def setRestLength(self, length):
        self.restLength = length
        self.calculatedRestLength = False

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
        self.contactForceLines.append(self.scene.addLine(0,0,0,0, QPen(Qt.green, 3)))
        if self.calculatedRestLength:
            self.restLength = self.getLength()

    def updateForces(self, delta_t):
        # Forces model simple elastic stress, and dependent on strain
        a = self.bodyA.GetWorldPoint(self.localAnchorA)
        b = self.bodyB.GetWorldPoint(self.localAnchorB)
        extension = self.getLength() - self.restLength
        extension_rate = (extension - self.last_extension) / delta_t
        if extension > 0:
            resistance = self.k * extension_rate * 0.01
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
        # Contact forces
        last_p = a
        cl_itr = iter(self.contactForceLines)
        for i, contact in enumerate(self.contacts):
            c_p = contact['body'].GetWorldPoint(contact['point'])
            if i == len(self.contacts) - 1:
                next_p = b
            else:
                contact_next = self.contacts[i+1]
                next_p = contact_next['body'].GetWorldPoint(contact_next['point'])
            # Decompose directions between contact point, and the previous and
            # next points in the chain.
            dir_ca = last_p - c_p
            dir_ca.Normalize()
            dir_cb = next_p - c_p
            dir_cb.Normalize()
            dir_c = (dir_ca + dir_cb) / 2
            dir_c.Normalize()
            force_ca = f*dir_ca
            force_c = dir_c * b2Dot(dir_c, force_ca)
            contact['body'].ApplyForce(force=force_c, point = c_p, wake=True)
            # Display
            force_line = next(cl_itr)
            force_line.setLine(
                c_p.x * world_scale, c_p.y * world_scale,
                c_p.x * world_scale + force_c.x/self.k,
                c_p.y * world_scale + force_c.y/self.k)
            last_p = c_p

        # Display
        self.forceLineA.setLine(
            a.x * world_scale, a.y * world_scale,
            a.x * world_scale + force_a.x/self.k,
            a.y * world_scale + force_a.y/self.k)
        self.forceLineB.setLine(
            b.x * world_scale, b.y * world_scale,
            b.x * world_scale + force_b.x/self.k,
            b.y * world_scale + force_b.y/self.k)
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

    def setLabel(self, label):
        self.label = label
