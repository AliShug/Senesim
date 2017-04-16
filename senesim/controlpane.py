from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim import QSliderD

length_str = '{0:.1f}'
k_str = '{0:.1f}'
force_str = '{0:.1f}'
speed_str = '{0:.1f}'
length_range = 100

class ElasticSliderBox(QGroupBox):
    def __init__(self, elastic_controller):
        self.minHeight = 40
        self.expandHeight = 90
        super(ElasticSliderBox, self).__init__(elastic_controller.label)
        # Slider box
        self.elastic_controller = elastic_controller
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(170)
        self.setMinimumHeight(self.minHeight)
        expander_stack = QVBoxLayout(self)
        expander_stack.setContentsMargins(0,0,0,0)
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(5,5,5,5)
        expander_stack.addLayout(box_layout)
        box_layout.addWidget(QLabel('Rest Length'))

        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=10)
        slider.setLimits(-length_range, length_range)
        def valChange():
            elastic_controller.setTarget(slider.value())
            self.textBox.setText(length_str.format(slider.value()))
        def valExternalChange():
            slider.blockSignals(True)
            slider.setValue(elastic_controller.getTarget())
            slider.blockSignals(False)
            self.textBox.setText(length_str.format(elastic_controller.getTarget()))
        slider.valueChanged.connect(valChange)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        elastic_controller.subscribeChange(valExternalChange)
        expander_stack.addWidget(slider)

        # Text readout
        self.textBox = QLineEdit(length_str.format(0))
        self.textBox.setMaximumWidth(80)
        def lengthTextChange():
            try:
                val = float(self.textBox.text())
            except:
                return
            elastic_controller.setTarget(val)
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)
        self.textBox.textChanged.connect(lengthTextChange)
        box_layout.addWidget(self.textBox)

        # Expand button
        self.expanded = False
        self.expander = QPushButton('+')
        self.expander.setMaximumWidth(20)
        self.expander.clicked.connect(self.toggleExpand)
        box_layout.addWidget(self.expander)

        # Expand content - additional controls
        self.expandWidget = QWidget()
        expander_stack.addWidget(self.expandWidget)
        expanded_layout = QFormLayout(self.expandWidget)
        range_box = QLineEdit(length_str.format(length_range))
        def rangeTextChange():
            try:
                val = float(range_box.text())
            except:
                return
            elastic_controller.setLimit(val)
            slider.blockSignals(True)
            slider.setLimits(-val, val)
            try:
                len = elastic_controller.getTarget()
                slider.setValue(len)
            except:
                pass
            slider.blockSignals(False)
        range_box.textEdited.connect(rangeTextChange)
        expanded_layout.addRow(QLabel('Slider range'), range_box)

        k_box = QLineEdit(k_str.format(elastic_controller.elastic.k))
        def kTextChange():
            try:
                val = float(k_box.text())
            except:
                return
            if abs(val) > 0.001:
                elastic_controller.elastic.k = val
        k_box.textEdited.connect(kTextChange)
        expanded_layout.addRow(QLabel('Elastic K'), k_box)

        force_box = QLineEdit(force_str.format(elastic_controller.maxForce))
        def forceTextChange():
            try:
                val = float(force_box.text())
            except:
                return
            elastic_controller.maxForce = val
        force_box.textEdited.connect(forceTextChange)
        expanded_layout.addRow(QLabel('Motor Force'), force_box)

        speed_box = QLineEdit(speed_str.format(elastic_controller.maxSpeed))
        def speedTextChange():
            try:
                val = float(speed_box.text())
            except:
                return
            elastic_controller.maxSpeed = val
        speed_box.textEdited.connect(speedTextChange)
        expanded_layout.addRow(QLabel('Motor Speed'), speed_box)


        # Start contracted by default
        self.contract()

    def toggleExpand(self):
        if self.expanded:
            self.contract()
        else:
            self.expand()

    def expand(self):
        self.expander.setText('-')
        # self.setMinimumHeight(self.expandHeight)
        self.expanded = True
        self.expandWidget.show()

    def contract(self):
        self.expander.setText('+')
        # self.setMinimumHeight(self.minHeight)
        self.expanded = False
        self.expandWidget.hide()

class ComboSliderBox(QWidget):
    def __init__(self, label, coupledController):
        super(ComboSliderBox, self).__init__()
        # Slider box
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setMinimumWidth(170)
        self.setMinimumHeight(40)
        box_layout = QHBoxLayout(self)
        box_layout.addWidget(QLabel(label))
        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=100)
        slider.setLimits(-1, 1)
        def valChange():
            coupledController.setTarget(slider.value())
        slider.valueChanged.connect(valChange)
        box_layout.addWidget(slider)

class LoadSliderBox(QGroupBox):
    def __init__(self, label, load):
        super(LoadSliderBox, self).__init__(label)
        # Slider box
        self.load = load
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setFixedWidth(170)
        self.setMinimumHeight(40)
        expander_stack = QVBoxLayout(self)
        expander_stack.setContentsMargins(0,0,0,0)
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(5,5,5,5)
        expander_stack.addLayout(box_layout)
        box_layout.addWidget(QLabel('Load (N)'))

        # The actual slider
        slider = QSliderD(Qt.Horizontal, divisor=10)
        slider.setLimits(0, load.max)
        def valChange():
            load.setForce([0, -slider.value()])
            self.textBox.setText(force_str.format(slider.value()))
        slider.valueChanged.connect(valChange)
        slider.setTickInterval(10)
        slider.setTickPosition(QSlider.TicksBelow)
        expander_stack.addWidget(slider)

        # Text readout
        self.textBox = QLineEdit(force_str.format(0))
        self.textBox.setMaximumWidth(80)
        def textChange():
            try:
                val = float(self.textBox.text())
            except:
                return
            load.setForce([0, -val])
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)
        self.textBox.textChanged.connect(textChange)
        box_layout.addWidget(self.textBox)

        # Expand button
        self.expanded = False
        self.expander = QPushButton('+')
        self.expander.setMaximumWidth(20)
        self.expander.clicked.connect(self.toggleExpand)
        box_layout.addWidget(self.expander)

        # Expand content - additional controls
        self.expandWidget = QWidget()
        expander_stack.addWidget(self.expandWidget)
        expanded_layout = QFormLayout(self.expandWidget)
        range_box = QLineEdit(length_str.format(load.max))
        def rangeTextChange():
            try:
                val = float(range_box.text())
            except:
                return
            load.max = val
            slider.blockSignals(True)
            slider.setLimits(0, load.max)
            try:
                f = -load.force.y
                slider.setValue(f)
            except:
                pass
            slider.blockSignals(False)
        range_box.textEdited.connect(rangeTextChange)
        expanded_layout.addRow(QLabel('Max Load (N)'), range_box)

        # Start contracted by default
        self.contract()

    def toggleExpand(self):
        if self.expanded:
            self.contract()
        else:
            self.expand()

    def expand(self):
        self.expander.setText('-')
        # self.setMinimumHeight(self.expandHeight)
        self.expanded = True
        self.expandWidget.show()

    def contract(self):
        self.expander.setText('+')
        # self.setMinimumHeight(self.minHeight)
        self.expanded = False
        self.expandWidget.hide()

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

    def addElasticController(self, elastic):
        '''Adds controls for an elastic thread'''
        slider_box = ElasticSliderBox(elastic)
        self.layout.addWidget(slider_box)

    def addComboController(self, label, coupledController):
        self.layout.addWidget(ComboSliderBox(label, coupledController))

    def addLoad(self, label, load):
        self.layout.addWidget(LoadSliderBox(label, load))

    def clear(self):
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            if not item:
                continue
            w = item.widget()
            if w:
                w.deleteLater()
        self.layout.addStretch(1)
