from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import QSliderD

class ElasticSliderBox(QWidget):
    def __init__(self, elastic):
        self.minHeight = 40
        self.expandHeight = 90
        super(ElasticSliderBox, self).__init__()
        # Slider box
        self.elastic = elastic
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumWidth(160)
        self.setMinimumHeight(self.minHeight)
        expander_stack = QVBoxLayout(self)
        expander_stack.setContentsMargins(0,0,0,0)
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(5,5,5,5)
        expander_stack.addLayout(box_layout)
        box_layout.addWidget(QLabel(elastic.label))

        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=1)
        slider.setLimits(-100, 100)
        rest = elastic.restLength
        def valChange():
            elastic.setRestLength(rest + slider.value())
        slider.valueChanged.connect(valChange)
        expander_stack.addWidget(slider)

        # Expand button
        self.expanded = False
        self.expander = QPushButton('+')
        self.expander.setMaximumWidth(20)
        self.expander.clicked.connect(self.toggleExpand)
        box_layout.addWidget(self.expander)

        self.expandWidget = QWidget()
        expander_stack.addWidget(self.expandWidget)
        expanded_layout = QFormLayout(self.expandWidget)
        expanded_layout.addRow(QLabel('Hello'), QLabel('World'))
        self.contract()

    def toggleExpand(self):
        if self.expanded:
            self.contract()
        else:
            self.expand()

    def expand(self):
        self.expander.setText('-')
        self.setMinimumHeight(self.expandHeight)
        self.expanded = True
        self.expandWidget.show()

    def contract(self):
        self.expander.setText('+')
        self.setMinimumHeight(self.minHeight)
        self.expanded = False
        self.expandWidget.hide()

class ComboSliderBox(QWidget):
    def __init__(self, label, elastic_a, elastic_b):
        super(ComboSliderBox, self).__init__()
        # Slider box
        self.elastic_a = elastic_a
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumWidth(170)
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
        self.layout.setContentsMargins(5,5,5,5)

        self.elastics = []

    def minimumSizeHint(self):
        return QSize(200,0)

    def addElastic(self, elastic):
        '''Adds controls for an elastic thread'''
        slider_box = ElasticSliderBox(elastic)
        self.layout.addWidget(slider_box)

    def addComboControl(self, label, elastic_a, elastic_b):
        self.layout.addWidget(ComboSliderBox(label, elastic_a, elastic_b))
