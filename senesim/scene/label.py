from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import *
from senesim.config import *


class Label(object):

    def __init__(self, scene, pos, text="", size=8, offset=QPoint(20, -10)):
        self.scene = scene
        self.item = self.scene.addText(text, QFont('Arial', pointSize=size))
        self.item.setPos(pos + offset)
        self.offset = offset
        self.item.setTransform(QTransform.fromScale(1, -1), True)

    def setText(self, text):
        self.item.setPlainText(text)

    def setPos(self, pos):
        self.item.setPos(pos + self.offset)

    def cleanup(self):
        if self.item:
            self.scene.removeItem(self.item)
        self.item = None
        self.offset = None
