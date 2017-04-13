from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

class ControlPane(QScrollArea):
    def __init__(self):
        QScrollArea.__init__(self)
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        self.myWidget = QWidget()
        self.setWidget(self.myWidget)
        layout = QVBoxLayout(self.myWidget)
        self.myWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        for i in range(4):
            # Slider box
            slider_box = QWidget()
            layout.addWidget(slider_box)
            slider_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            slider_box.setMinimumWidth(200)
            slider_box.setFixedHeight(60)
            box_layout = QHBoxLayout(slider_box)
            box_layout.addWidget(QLabel('Hello'))
            box_layout.addWidget(QLabel('World'))
        layout.addStretch(1)

    def minimumSizeHint(self):
        return QSize(200,0)
