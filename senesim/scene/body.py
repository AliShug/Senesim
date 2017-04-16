import math

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *



class Body(object):

    def __init__(self, world, scene):
        self.world = world
        self.scene = scene
        self._initialized = False

    def initBox(self, pos, width, height,
                static=False, color=default_color,
                label=None, density=default_density,
                friction=default_friction,
                restitution=default_restitution):
        if self._initialized:
            raise Exception("Body already initialized")

        pos = b2Vec2(pos)
        self.graphics = self.scene.addRect(
            (-width) * world_scale,
            (-height) * world_scale,
            width * world_scale * 2,
            height * world_scale * 2,
            brush=QBrush(QColor.fromRgbF(color[0], color[1], color[2])))
        self.graphics.setData(0, self)
        self.static = static

        if label:
            self.label = self.scene.addText(
                label, QFont('Arial', pointSize=8))
            self.label.setPos(pos.x * world_scale, pos.y * world_scale)
            self.label.setTransform(QTransform.fromScale(1, -1), True)
        else:
            self.label = None

        if static:
            self.body = self.world.CreateStaticBody(
                position=pos,
                shapes=b2PolygonShape(box=(width, height)),
                userData=self)
        else:
            self.body = self.world.CreateDynamicBody(
                position=pos,
                userData=self,
                linearDamping=default_damp_linear,
                angularDamping=default_damp_angular)
            self.box = self.body.CreatePolygonFixture(
                box=(width, height),
                density=density,
                friction=friction,
                restitution=restitution)

    def initCircle(self, pos, radius,
                   static=False, color=default_color,
                   label=None, density=default_density,
                   friction=default_friction,
                   restitution=default_restitution):
        if self._initialized:
            raise Exception("Body already initilized")

        self.graphics = self.scene.addEllipse(
            (-radius) * world_scale,
            (-radius) * world_scale,
            radius * world_scale * 2,
            radius * world_scale * 2,
            brush=QBrush(QColor.fromRgbF(color[0], color[1], color[2])))
        self.graphics.setData(0, self)
        self.static = static

        if label:
            self.label = self.scene.addText(
                label, QFont('Arial', pointSize=8))
            self.label.setPos(pos.x * world_scale, pos.y * world_scale)
            self.label.setTransform(QTransform.fromScale(1, -1), True)
        else:
            self.label = None

        if static:
            self.body = self.world.CreateStaticBody(
                position=pos,
                shapes=b2CircleShape(radius=radius),
                userData=self)
        else:
            self.body = self.world.CreateDynamicBody(
                position=pos,
                userData=self,
                linearDamping=default_damp_linear,
                angularDamping=default_damp_angular)
            self.circle = self.body.CreateFixture(
                shape=b2CircleShape(radius=radius),
                density=density,
                friction=friction,
                restitution=restitution)

    def updateGraphics(self):
        pos = self.body.position
        if self.label:
            rect = self.label.boundingRect()
            self.label.setPos(pos.x * world_scale - rect.width() / 2,
                              pos.y * world_scale + rect.height() / 2)
        self.graphics.setRotation(math.degrees(self.body.angle))
        self.graphics.setPos(QPoint(pos.x * world_scale, pos.y * world_scale))

    def cleanup(self):
        if self.label:
            self.scene.removeItem(self.label)
        self.scene.removeItem(self.graphics)
        self.world.DestroyBody(self.body)
