from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *

elastic_pen = QPen(QBrush(Qt.black), 2)

class Elastic(object):

    def __init__(self, world, scene):
        self.world = world
        self.scene = scene
        self.contacts = []

    def initElastic(self,
                    bodyA,
                    bodyB,
                    anchorA,
                    anchorB,
                    elastic_k,
                    restLength=None,
                    damping=1):
        self.bodyA = bodyA
        self.bodyB = bodyB
        self.localAnchorA = bodyA.GetLocalPoint(anchorA)
        self.localAnchorB = bodyB.GetLocalPoint(anchorB)
        self.k = elastic_k
        self.damping = damping
        self.graphics_pen = QPen(elastic_pen)
        self.graphics = self.scene.addPath(QPainterPath(), pen=self.graphics_pen)
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
        different bodies, and apply forces to those bodies according to
        the elastic tension. If no rest length has been manually set, this
        recalculates the resting length at the current position.'''
        pointLocal = body.GetLocalPoint(point)
        self.contacts.append({
            'body': body,
            'point': pointLocal
        })
        self.contactForceLines.append(self.scene.addLine(0,0,0,0, QPen(Qt.green, 3)))
        if self.calculatedRestLength:
            self.restLength = self.getLength()

    def getExtension(self):
        return self.getLength() - self.restLength

    def getInternalForce(self, delta_t):
        # Forces model simple elastic stress, and is dependent on strain
        extension = self.getExtension()
        extension_rate = (extension - self.last_extension) / delta_t
        if extension > 0:
            elastic_force = self.k * extension
            damping = self.damping * extension_rate
        else:
            elastic_force = 0
            damping = 0

        return damping + elastic_force

    def updateForces(self, delta_t):
        a = self.bodyA.GetWorldPoint(self.localAnchorA)
        b = self.bodyB.GetWorldPoint(self.localAnchorB)
        f = self.getInternalForce(delta_t)
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
        self.last_extension = self.getExtension()

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
        new_path = QPainterPath()
        new_path.moveTo(segments[-1].p2())
        for line in reversed(segments):
            new_path.lineTo(line.p1())
        self.graphics.setPath(new_path)
        # Scale and move the pen's dash rendering
        scaling = self.getLength()/self.restLength
        self.graphics_pen.setDashPattern([5 * scaling, 2 * scaling])
        if scaling < 1:
            self.graphics_pen.setColor(QColor(100,100,100))
        else:
            self.graphics_pen.setColor(Qt.black)
        self.graphics.setPen(self.graphics_pen)


    def getLength(self):
        length = 0
        for line in self.getLineDefs():
            length += line.length()
        return length

    def cleanup(self):
        self.scene.removeItem(self.graphics)
        self.scene.removeItem(self.forceLineA)
        self.scene.removeItem(self.forceLineB)
        del self.bodyA
        del self.bodyB

    def hideForces(self):
        self.forceLineA.hide()
        self.forceLineB.hide()
        for line in self.contactForceLines:
            line.hide()

    def showForces(self):
        self.forceLineA.show()
        self.forceLineB.show()
        for line in self.contactForceLines:
            line.show()
