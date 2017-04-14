from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import QSliderD

class ElasticSliderBox(QWidget):
    def __init__(self, elastic):
        super(ElasticSliderBox, self).__init__()
        # Slider box
        self.elastic = elastic
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumWidth(160)
        self.setMinimumHeight(40)
        box_layout = QHBoxLayout(self)
        box_layout.addWidget(QLabel(elastic.label))
        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=1)
        slider.setLimits(-100, 100)
        rest = elastic.restLength
        def valChange():
            elastic.setRestLength(rest + slider.value())
        slider.valueChanged.connect(valChange)
        box_layout.addWidget(slider)

class ComboSliderBox(QWidget):
    def __init__(self, label, elastic_a, elastic_b):
        super(ComboSliderBox, self).__init__()
        # Slider box
        self.elastic_a = elastic_a
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumWidth(160)
        self.setMinimumHeight(40)
        box_layout = QHBoxLayout(self)
        box_layout.addWidget(QLabel(label))
        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=1)
        slider.setLimits(-100, 100)
        rest_a = elastic_a.restLength
        rest_b = elastic_b.restLength
        def valChange():
            elastic_a.setRestLength(rest_a + slider.value())
            elastic_b.setRestLength(rest_b - slider.value())
        slider.valueChanged.connect(valChange)
        box_layout.addWidget(slider)

class ControlPane(QScrollArea):
    def __init__(self):
        QScrollArea.__init__(self)
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.myWidget = QWidget()
        self.setWidget(self.myWidget)
        self.layout = QBoxLayout(QBoxLayout.BottomToTop, self.myWidget)
        self.myWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.layout.addStretch(1)

        self.elastics = []

    def minimumSizeHint(self):
        return QSize(200,0)

    def addElastic(self, elastic):
        '''Adds controls for an elastic thread'''
        slider_box = ElasticSliderBox(elastic)
        self.layout.addWidget(slider_box)

    def addComboControl(self, label, elastic_a, elastic_b):
        self.layout.addWidget(ComboSliderBox(label, elastic_a, elastic_b))
