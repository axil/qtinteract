from traceback import print_exc
from math import pi
import inspect

import numpy as np
from scipy.optimize import curve_fit

from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QDoubleSpinBox, QVBoxLayout, \
     QGridLayout, QPushButton, QHBoxLayout, QTabWidget
from PyQt5.QtCore import Qt, pyqtSlot as slot, QMetaObject
import pyqtgraph
import pyqtgraph as pg 
from PyQt5 import QtWidgets

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('imageAxisOrder', 'row-major')

ipython = get_ipython()
ipython.run_line_magic('gui', 'qt')

class SimpleWindow(QWidget):
    def __init__(self, *args, **kwargs):
        try:
            super().__init__(parent=None)

            self.setGeometry(300, 300, 400, 300)
            self.setWindowTitle('QtInteract')
            self.layout = QVBoxLayout(self)

            self.canvas0 = pg.PlotWidget()
            self.p0 = self.canvas0.plot([], [], pen='b')
            self.canvas0.addItem(self.p0)
            self.layout.addWidget(self.canvas0)

            self.canvas1 = pg.PlotWidget()
            self.p1 = self.canvas1.plot([], [], pen='b')
            self.canvas1.addItem(self.p1)
            self.p1a = self.canvas1.plot([], [], pen='g')
            self.canvas1.addItem(self.p1a)
    #        self.canvas.plotItem.vb.setLimits(yMin=0)
    #        self.layout.addWidget(self.canvas1)
        
            self.canvas2 = pg.PlotWidget()
            self.p2 = self.canvas2.plot([], [], pen='b')
            self.canvas2.addItem(self.p2)
            self.p2a = self.canvas2.plot([], [], pen='g')
            self.canvas2.addItem(self.p2a)
    #        self.canvas.plotItem.vb.setLimits(yMin=0)
            self.layout.addWidget(self.canvas2)

            self.canvas3 = pg.PlotWidget()
            self.p3 = self.canvas3.plot([], [], pen='b')
            self.canvas3.addItem(self.p3)
            self.p3a = self.canvas3.plot([], [], pen='g')
            self.canvas3.addItem(self.p3a)
    #        self.canvas.plotItem.vb.setLimits(yMin=0)
            self.layout.addWidget(self.canvas3)

            self.slider1 = QSlider(objectName='slider1', orientation=Qt.Horizontal)
    #        self.slider1.setOrientation(Qt.Horizontal)
            self.slider1.setRange(0, 100)
            self.layout.addWidget(self.slider1)

            self.slider2 = QSlider(objectName='slider2', orientation=Qt.Horizontal)
    #        self.slider1.setOrientation(Qt.Horizontal)
            self.slider2.setRange(0, 100)
            self.layout.addWidget(self.slider2)

            self.slider3 = QSlider(objectName='slider3', orientation=Qt.Horizontal)
    #        self.slider1.setOrientation(Qt.Horizontal)
            self.slider3.setRange(-100, 100)
            self.layout.addWidget(self.slider3)

            self.slider4 = QSlider(objectName='slider4', orientation=Qt.Horizontal)
    #        self.slider1.setOrientation(Qt.Horizontal)
            self.slider4.setRange(0, 100)
            self.layout.addWidget(self.slider4)

            QMetaObject.connectSlotsByName(self)
            #self.y = np.roll(1/(x+10), 5)
            self.y = np.roll(x*np.exp(-x/3), 5)
            self.update()
        except:
            print_exc()
    
    def on_slider1_valueChanged(self, x):
        self.update(noise_level=x)

    def on_slider2_valueChanged(self, x):
        self.update(seed=x)

    def on_slider3_valueChanged(self, x):
        self.update(nroll=x)

    def on_slider4_valueChanged(self, x):
        self.update(nzeros=x)

    def update(self, noise_level=None, seed=None, nroll=None, nzeros=None):
        if noise_level is None:
            noise_level = self.slider1.value()
        if seed is None:
            seed = self.slider2.value()
        if nroll is None:
            nroll = self.slider3.value()
        if nzeros is None:
            nzeros = self.slider4.value()
        #plot(y)
        np.random.seed(seed)
        y = np.roll(self.y, nroll)
        a0 = y
        a1 = np.r_[y * (1 + np.random.randn(n)*noise_level/10000), np.zeros(nzeros)*10]
        #plot(a1)
        b0 = np.fft.fft(a0)
        b1 = np.fft.fft(a1) 
        #plot(np.abs(b))
        self.p0.setData(a1)
#        self.p1.setData(np.abs(b))
        c0 = np.angle(b0)    
        c1 = np.angle(b1)
        self.p2a.setData(c0[:n//2])
        self.p2.setData(c1[:n//2])
        u0 = np.unwrap(c0)
        u1 = np.unwrap(c1)
        self.p3a.setData(u0[:n//2])
        self.p3.setData(u1[:n//2])
        
win = SimpleWindow()
win.show()