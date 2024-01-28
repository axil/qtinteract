from traceback import print_exc
from math import pi
import inspect

import numpy as np

from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QDoubleSpinBox, QVBoxLayout, QGridLayout
from PyQt5.QtCore import Qt
import pyqtgraph
import pyqtgraph as pg 
from PyQt5 import QtWidgets

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

def spin2slider(v, vmin, vmax, n):
    return round((v-vmin)/(vmax-vmin)*n)

#def slider2spin(x, vmin, vmax):
#    return vmin + (x/100)*(vmax-vmin)

class SimpleWindow(QWidget):
    def add_param(self, name, vmin=None, vmax=None, vstep=None, v=None):
        if vstep is None:
            vstep = 0.1
        if v is None:
            v = vmin + (vmax-vmin)//vstep//2*vstep
        elif vmin is None and vmax is None:
            vmin, vmax = -v, v*2
        assert vstep != 0
        n = round((vmax-vmin)/vstep)
        label = QLabel(text=name)
        slider = QSlider()
        slider.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(0, round((vmax-vmin)/vstep)+1)
        slider.setValue(spin2slider(v, vmin, vmax, n))
        setattr(self, name+'_slider', slider)
        spinbox = QDoubleSpinBox()
        spinbox.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        spinbox.setRange(vmin, vmax)
        spinbox.setSingleStep(vstep)
        spinbox.setValue(v)
        setattr(self, name+'_spinbox', spinbox)
        slider.valueChanged['int'].connect(self.slider_changed(name, spinbox, vmin, vmax, n)) # type: ignore
        spinbox.valueChanged['double'].connect(self.spinbox_changed(name, slider, vmin, vmax, n)) # type: ignore
        self.grid.addWidget(label, self.grid_row, 0, 1, 1)
        self.grid.addWidget(slider, self.grid_row, 2, 1, 1)
        self.grid.addWidget(spinbox, self.grid_row, 3, 1, 1)
        self.grid_row += 1
        self.arg_names.append(name)

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(parent=None)

            self.setGeometry(300, 300, 400, 300)
            self.setWindowTitle('QtInteract')
            if len(args) == 1:
                y = args[0]
                x = np.arange(len(y))
            elif len(args) == 2:
                x, y = args
            else:
                raise ValueError('There should be either one (y) or two (x, y) positional arguments, not {len(args})).')
            if isinstance(y, (tuple, list)):
                self.funcs = y
            else:
                self.funcs = [y]
            self.nfuncs = len(self.funcs)

            self.layout = QVBoxLayout(self)

            self.canvas = pg.PlotWidget()
            for i, f in enumerate(self.funcs):
                self.plots.append(self.canvas.plot([], [], pen='b', name=f'f{i}'))
            self.layout.addWidget(self.canvas)

            self.arg_names = []
            self.grid_row = 0
            self.grid = QGridLayout()
            if isinstance(x, (tuple, list)):
                if len(x) == 2:
                    xmin, xmax = kwargs.pop('x')
                    xstep = (xmax-xmin)/100
                elif len(x) == 3:
                    xmin, xmax, xstep = kwargs.pop('x')
            self.x = np.linspace(xmin, xmax, round((xmax-xmin)/xstep))
            for k, v in kwargs.items():
                if isinstance(v, (tuple, list)):
                    default = inspect.signature(f).parameters[k].default
                    if default is inspect._empty:
                        default = None
                    if len(v) == 2:
                        self.add_param(k, vmin=v[0], vmax=v[1], v=default)
                    elif len(v) == 3:
                        self.add_param(k, vmin=v[0], vmax=v[1], vstep=v[2], v=default)
                    else:
                        raise ValueError('tuple/list is expected to be 2 or 3 items long')
                elif isinstance(v, (int, float)):
                    self.add_param(k, v=v)
            self.layout.addLayout(self.grid)
            self.update()
        except:
            print_exc()
            
    def slider_changed(self, name, spin, vmin, vmax, n):
        def wrapped(x):
            try:
                v = vmin + x/n*(vmax-vmin)
                spin.blockSignals(True)
                spin.setValue(v)
                spin.blockSignals(False)
                self.update(name, v)
            except:
                print_exc()
        return wrapped

    def spinbox_changed(self, name, slider, vmin, vmax, n):
        def wrapped(v):
            try:
                slider.blockSignals(True)
                slider.setValue(round((v-vmin)/(vmax-vmin)*n))
                slider.blockSignals(False)
                self.update(name, v)
            except:
                print_exc()
        return wrapped
    
    def update(self, name=None, value=None):
        try:
            kwargs = {}
            for k in self.arg_names:
                if k != name:
                    kwargs[k] = getattr(self, k+'_spinbox').value()
                else:
                    kwargs[k] = value
            for i, p in enumerate(self.plots):
                kw = inspect.signature(self.funcs[i]).parameters.keys()
                p.setData({'x': self.x, 'y': self.funcs[i](self.x, **kwargs)})
        except:
            print_exc()
        
def interact(f, **kwargs):
    sw = SimpleWindow(f, **kwargs)
    sw.show()
    return sw

def test_interact():
    def f(x, a, b):
        return np.exp(-a/100.*x) * np.sin(b*x)

    interact(f, a=(1, 100, 1), b=(1, 10, 1))

