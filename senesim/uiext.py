from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

class QSliderD(QSlider):
    def __init__(self, *args, **kwargs):
        self.divisor = kwargs.pop('divisor', 100)
        super(QSliderD, self).__init__(*args, **kwargs)

    def setValue(self, val):
        super(QSliderD, self).setValue(int(val * self.divisor))

    def setMinimum(self, val):
        super(QSliderD, self).setMinimum(int(val * self.divisor))

    def setMaximum(self, val):
        super(QSliderD, self).setMaximum(int(val * self.divisor))

    def setPageStep(self, val):
        super(QSliderD, self).setPageStep(int(val * self.divisor))

    def setSingleStep(self, val):
        super(QSliderD, self).setSingleStep(int(val * self.divisor))

    def setSliderPosition(self, val):
        super(QSliderD, self).setSliderPosition(int(val * self.divisor))

    def setTickInterval(self, val):
        super(QSliderD, self).setTickInterval(int(val * self.divisor))

    def value(self):
        return super(QSliderD, self).value() / self.divisor

    def minimum(self):
        return super(QSliderD, self).minimum() / self.divisor

    def maximum(self):
        return super(QSliderD, self).maximum() / self.divisor

    def pageStep(self):
        return super(QSliderD, self).pageStep() / self.divisor

    def singleStep(self):
        return super(QSliderD, self).singleStep() / self.divisor

    def sliderPosition(self):
        return super(QSliderD, self).sliderPosition() / self.divisor

    def tickInterval(self):
        return super(QSliderD, self).tickInterval() / self.divisor

    def setLimits(self, min, max):
        self.setMinimum(min)
        self.setMaximum(max)

    # Pane full of sliders - don't want to adjust slider instead of scrolling
    def wheelEvent(self, e):
        pass
