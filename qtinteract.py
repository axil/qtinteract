from traceback import print_exc
from math import pi
import inspect
from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit

from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QDoubleSpinBox, QVBoxLayout, \
     QGridLayout, QPushButton, QHBoxLayout, QTabWidget, QLineEdit
from PyQt5.QtCore import Qt
import pyqtgraph
import pyqtgraph as pg
from PyQt5 import QtWidgets

__version__ = '0.2'

try:
    ipython = get_ipython()
    ipython.run_line_magic('gui', 'qt')
except:
    pass

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('imageAxisOrder', 'row-major')

def set_value_nc(objs, v):
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    for obj in objs:
        obj.blockSignals(True)
        obj.setValue(v)
        obj.blockSignals(False)

def spin2slider(v, vmin, vmax, n):
    return round((v-vmin)/(vmax-vmin)*n)

#def slider2spin(x, vmin, vmax):
#    return vmin + (x/100)*(vmax-vmin)

@dataclass
class Limits:
    vmin: float
    vmax: float
    vstep: float

    @property
    def nsteps(self):
        return round((self.vmax-self.vmin)/self.vstep)

    def k2v(self, k):
        return self.vmin + k/self.nsteps*(self.vmax-self.vmin)

    def v2k(self, v):
        return round((v-self.vmin)/(self.vmax-self.vmin)*self.nsteps)


class SimpleWindow(QWidget):
    def add_param(self, name, vmin=None, vmax=None, vstep=None, v=None):
        if vstep is None:
            if any(isinstance(var, float) for var in (vmin, vmax, vstep, v)):
                vstep = 0.1
            else:
                vstep = 1
        if v is None:
            assert vmin is not None and vmin is not None and vmin < vmax, name
            v = vmin + round((vmax-vmin)/vstep)//2*vstep
        elif vmin is None and vmax is None:
            if v == 0:
                vmin, vmax = 0, 1
            else:
                vmin, vmax = -v, v*2
        assert vstep != 0
        lim = Limits(vmin, vmax, vstep)
        self.limits[name] = lim
        n = lim.nsteps
        label = QLabel(text=name)
        slider = QSlider()
        slider.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(0, n)
        slider.setValue(spin2slider(v, vmin, vmax, n))
        setattr(self, name+'_slider', slider)
        spinbox = QDoubleSpinBox()
        spinbox.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        spinbox.setRange(vmin, vmax)
        spinbox.setSingleStep(vstep)
        spinbox.setValue(v)
        setattr(self, name+'_spinbox', spinbox)
        spinbox_min = QLineEdit()
        spinbox_min.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        spinbox_min.setText(str(vmin))
        spinbox_min.setMaximumWidth(75)
        setattr(self, name+'_spinbox_min', spinbox_min)
        spinbox_max = QLineEdit()
        spinbox_max.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        spinbox_max.setText(str(vmax))
        spinbox_max.setMaximumWidth(75)
        setattr(self, name+'_spinbox_max', spinbox_max)
        spinbox_step = QLineEdit()
        spinbox_step.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        spinbox_step.setText(str(vstep))
        spinbox_step.setMaximumWidth(75)
        setattr(self, name+'_spinbox_step', spinbox_step)
        slider.valueChanged['int'].connect(self.slider_changed(name, spinbox)) # type: ignore
        spinbox.valueChanged['double'].connect(self.spinbox_changed(name, slider)) # type: ignore
        spinbox_min.editingFinished.connect(self.spinbox_min_changed(spinbox_min, name, slider, spinbox)) # type: ignore
        spinbox_max.editingFinished.connect(self.spinbox_max_changed(spinbox_max, name, slider, spinbox)) # type: ignore
        spinbox_step.editingFinished.connect(self.spinbox_step_changed(spinbox_step, name, slider, spinbox)) # type: ignore
        self.grid.addWidget(label, self.grid_row, 0, 1, 1)
        self.grid.addWidget(slider, self.grid_row, 2, 1, 1)
        self.grid.addWidget(spinbox, self.grid_row, 3, 1, 1)
        self.grid.addWidget(QLabel('min:'), self.grid_row, 4, 1, 1)
        self.grid.addWidget(spinbox_min, self.grid_row, 5, 1, 1)
        self.grid.addWidget(QLabel('max:'), self.grid_row, 6, 1, 1)
        self.grid.addWidget(spinbox_max, self.grid_row, 7, 1, 1)
        self.grid.addWidget(QLabel('step:'), self.grid_row, 8, 1, 1)
        self.grid.addWidget(spinbox_step, self.grid_row, 9, 1, 1)
        self.grid_row += 1
        self.param_names.append(name)

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(parent=None)

            self.setGeometry(300, 300, 400, 300)
            self.setWindowTitle('QtInteract')
            if len(args) == 1:
                y = args[0]
                x, style = None, None
            elif len(args) == 2:
                if isinstance(args[1], str) or isinstance(args[1], (tuple, list)) and len(args[1]) > 0 and \
                   isinstance(args[1][0], str):
                    x = None
                    y, style = args
                else:
                    x, y = args
                    style = None
            elif len(args) == 3:
                x, y, style = args
            else:
                raise ValueError(f'There should be either one (y), two (x, y) positional arguments, not {len(args)}.')
            if isinstance(y, (tuple, list)):
                pass
            else:
                y = [y]

            self.layout = QVBoxLayout(self)

            if isinstance(x, (tuple, list)):
                assert len(x) == len(y), 'The number of x arrays should either be 1 or match the number of funcs'
                assert isinstance(x[0], np.ndarray) or x[0] is None
                self.x = x
            elif isinstance(x, np.ndarray) or x is None:
                self.x = [x] * len(y)
            else:
                raise ValueError('First argument x must either be a numpy array or a list of numpy arrays')

            if isinstance(style, (tuple, list)):
                assert len(style) == len(y), 'The number of style elements should either be 1 or match the number of funcs'
                assert isinstance(style[0], str)
                pass
            elif isinstance(style, str) or style is None:
                style = [style] * len(y)
            else:
                raise ValueError('Third argument style must either be a str or a list of strs')

            self.canvas = pg.PlotWidget()
            self.plots = []
            self.static_plots = []
            self.y = []        # for stem plot
            self.static_y = []
            self.funcs = []
            self.funcs_x = []
            default_args = {}
            for i, f in enumerate(y):
                kw = {}
                kw['name'] = f'f{i}'
                if style[i] in ('-', None):
                    kw['pen'] = 'b'
                elif style[i] == '.':
                    kw['pen'] = None
                    kw['symbol'] = 'o'
                    kw['symbolSize'] = 7
                elif style[i] == '.-':
                    kw['pen'] = 'b'
                    kw['symbol'] = 'o'
                    kw['symbolSize'] = 7
                elif style[i] == 'o':
                    kw.update({
                        'pen': None,
                        'symbol': 'o',
                        'symbolPen': 'b',
                        'symbolBrush': None,
                        'symbolSize': 7,
                    })
                else:
                    raise ValueError(f'Supported styles: ".", "-", ".-", got {style[i]}')
                if isinstance(f, np.ndarray):
                    if self.x[i] is None:
                        self.static_plots.append(self.canvas.plot(np.arange(len(f)), f, **kw))
                    else:
                        self.static_plots.append(self.canvas.plot(self.x[i], f, **kw))
                    self.static_y.append(f)
                else:
                    self.plots.append(self.canvas.plot([], [], **kw))
                    self.funcs.append(f)
                    self.funcs_x.append(self.x[i])
                    for k, v in inspect.signature(f).parameters.items():
                        default_args[k] = None if v.default is inspect._empty else v.default
                    self.y.append([])
            self.layout.addWidget(self.canvas)

            self.param_names = []
            self.grid_row = 0
            self.grid = QGridLayout()

            self.func_kw = [list(inspect.signature(f).parameters) for f in self.funcs]

            self.limits = {}

            processed = set()
            # parse function arguments
            for k, v in kwargs.items():
                if isinstance(v, (tuple, list)):
                    default = default_args[k]
                    if len(v) == 2:
                        self.add_param(k, vmin=v[0], vmax=v[1], v=default)
                    elif len(v) == 3:
                        self.add_param(k, vmin=v[0], vmax=v[1], vstep=v[2], v=default)
                    else:
                        raise ValueError('tuple/list is expected to be 2 or 3 items long')
                elif isinstance(v, (int, float)):
                    self.add_param(k, v=v)
                processed.add(k)

            for k, v in default_args.items():
                if v is not None and k not in processed:
                    self.add_param(k, v=v)
            self.layout.addLayout(self.grid)
            self.post_create_widgets()
            self.update()
        except:
            print_exc()

    def post_create_widgets(self):
        pass

    def get_param(self, name):
        return getattr(self, name+'_spinbox').value()

    def set_param(self, name, value):
        return getattr(self, name+'_spinbox').setValue(value)

    def slider_changed(self, name, spin):
        def wrapped(k):
            try:
                v = self.limits[name].k2v(k)
                set_value_nc(spin, v)
                self.update(name, v)
            except:
                print_exc()
        return wrapped

    def spinbox_changed(self, name, slider):
        def wrapped(v):
            try:
                k = self.limits[name].v2k(v)
                set_value_nc(slider, k)
                self.update(name, v)
            except:
                print_exc()
        return wrapped

    def spinbox_min_changed(self, obj, name, slider, spinbox):
        def wrapped():
            try:
                vmin = float(obj.text())
                spinbox.setMinimum(vmin)
                lim = self.limits[name]
                lim.vmin = vmin
                v = spinbox.value()
                k = self.limits[name].v2k(v)
                slider.setMaximum(lim.nsteps)
                set_value_nc(slider, k)
            except:
                print_exc()
        return wrapped
    
    def spinbox_max_changed(self, obj, name, slider, spinbox):
        def wrapped():
            try:
                vmax = float(obj.text())
                spinbox.setMaximum(vmax)
                lim = self.limits[name]
                lim.vmax = vmax
                v = spinbox.value()
                k = self.limits[name].v2k(v)
                slider.setMaximum(lim.nsteps)
                set_value_nc(slider, k)
            except:
                print_exc()
        return wrapped

    def spinbox_step_changed(self, obj, name, slider, spinbox):
        def wrapped():
            try:
                vstep = float(obj.text())
                spinbox.setSingleStep(vstep)
                if vstep >= 0.1:
                    spinbox.setDecimals(1)
                elif vstep >= 0.01:
                    spinbox.setDecimals(2)
                elif vstep >= 0.001:
                    spinbox.setDecimals(3)
                elif vstep >= 0.0001:
                    spinbox.setDecimals(4)
                elif vstep >= 0.00001:
                    spinbox.setDecimals(5)
                else:
                    spinbox.setDecimals(2)
                lim = self.limits[name]
                lim.vstep = vstep
                v = spinbox.value()
                k = self.limits[name].v2k(v)
                slider.setMaximum(lim.nsteps)
                set_value_nc(slider, k)
            except:
                print_exc()
        return wrapped

    def get_all_plots(self):
        yield from self.static_plots
        yield from self.plots

    def update(self, name=None, value=None):
        try:
            current = {}
            for k in self.param_names:
                if k != name:
                    current[k] = getattr(self, k+'_spinbox').value()
                else:
                    current[k] = value
            for i, p in enumerate(self.plots):
                if self.funcs_x[i] is None:
                    kw = {k: current[k] for k in self.func_kw[i]}
                    self.y[i] = self.funcs[i](**kw)
                    p.setData({'y': self.y[i]})
                else:
                    kw = {k: current[k] for k in self.func_kw[i] if k != 'x'}
                    self.y[i] = self.funcs[i](self.funcs_x[i], **kw)
                    p.setData({'x': self.funcs_x[i], 'y': self.y[i]})
        except:
            print_exc()

class FitTool(SimpleWindow):
    def post_create_widgets(self):
        self.fit_button = QPushButton('Fit')
        self.fit_button.clicked.connect(self.fit_button_clicked)
        hbox = QHBoxLayout()
        hbox.addWidget(self.fit_button)
        hbox.addStretch()
        hbox.insertStretch(0)
        self.layout.addLayout(hbox)

        self.line1 = pg.InfiniteLine(0, movable=True, angle=90, pen='pink')
        self.line1.sigDragged.connect(self.line1_dragged)
        self.canvas.addItem(self.line1)

        self.line2 = pg.InfiniteLine(1, movable=True, angle=90, pen='pink')
        self.line2.sigDragged.connect(self.line2_dragged)
        self.canvas.addItem(self.line2)

        self.line1pos = None
        self.line2pos = None

        self.canvas2 = pg.PlotWidget()
        self.stem1 = self.canvas2.plot([], [], symbolPen='b', symbolBrush=None, pen=None)
        self.stem2 = self.canvas2.plot([], [], connect='pairs', pen='b')
        self.hline = pg.InfiniteLine(0, angle=0, pen='pink')
        self.canvas2.addItem(self.hline)
#        self.canvas.plotItem.vb.setLimits(yMin=0)
        self.layout.addWidget(self.canvas2)
        self.canvas2.setXLink(self.canvas)


    def fit_button_clicked(self):
        try:
            p0 = [self.get_param(name) for name in self.param_names]
            x1 = self.line1.value()
            i1 = np.searchsorted(self.x[0], x1)
            x2 = self.line2.value()
            i2 = np.searchsorted(self.x[0], x2)
            p, _ = curve_fit(self.funcs[0], self.x[0][i1:i2+1], self.static_y[0][i1:i2+1], p0=p0)
            for name, value in zip(self.param_names, p):
                self.set_param(name, value)
        except:
            print_exc()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if self.line1pos is None:
            self.line1pos = min(p.dataBounds(0)[0] for p in self.get_all_plots())
            self.line2pos = max(p.dataBounds(0)[1] for p in self.get_all_plots())
#                (self.line1pos, self.line2pos), _ = self.canvas.getViewBox().viewRange()
            print(self.line1pos, self.line2pos)
            self.line1.setValue(self.line1pos)
            self.line2.setValue(self.line2pos)
        x, y = self.x[0], self.y[0]-self.static_y[0]
        self.stem1.setData(x=x, y=y)
        self.stem2.setData(x=np.repeat(x, 2), y=np.dstack((np.zeros(y.shape[0]), y)).flatten())

    def line1_dragged(self, line):
        self.fit_button_clicked()
#        print(line.value())

    def line2_dragged(self, line):
        self.fit_button_clicked()
#        print(line.value())


class IShow(QWidget):
    def __init__(self, arr=None):
        super().__init__()#parent=parent)

        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle('ishow')
#        self.layout = QVBoxLayout(self)
        self.canvas0 = pg.PlotWidget()
        self.canvas0.addLegend()
        self.image = arr
        self.im = pg.ImageItem(self.image)
        self.im.setColorMap(pg.colormap.get('viridis'))
#        self.im.hoverEvent = self.update_profile
        self.canvas0.addItem(self.im)
#        self.layout.addWidget(self.canvas0)
        self.hline = HLine(pos=self.image.shape[0]//2, bounds=(0, self.image.shape[0]), on_drag=self.update_profile)
        self.vline = VLine(pos=self.image.shape[1]//2, bounds=(0, self.image.shape[1]), on_drag=self.update_profile)
        self.canvas0.addItem(self.hline)
        self.canvas0.addItem(self.vline)

#        self.tabs = QTabWidget()

        self.canvas_below = pg.PlotWidget()
        self.p_below = self.canvas_below.plot([], pen='b', name='p0')
#        self.tabs.addTab(self.canvas1, 'horizontal')
        self.vline_below = VLine(pos=self.image.shape[1]//2, bounds=(0, self.image.shape[1]), 
                                 on_drag=self.vline_below_dragged)
        self.canvas_below.addItem(self.vline_below)
        self.canvas_below.setXLink(self.canvas0)

        self.canvas_right = pg.PlotWidget()
        self.p_right = self.canvas_right.plot([], pen='b', name='p0')
#        self.tabs.addTab(self.canvas_right, 'vertical')
        self.hline_right = HLine(pos=self.image.shape[0]//2, bounds=(0, self.image.shape[0]), 
                                 on_drag=self.hline_right_dragged)
#        self.canvas0.sigRangeChanged.connect(self.updateRange)
        self.canvas_right.addItem(self.hline_right)
        self.canvas_right.setYLink(self.canvas0)

        self.layout = vStack(
                hStack(self.canvas0, self.canvas_right, ratio=(4,1)), 
                hStack(self.canvas_below, None, ratio=(4,1)),
            parent=self,
            ratio=(4,1),
        )
        self.update_profile()

    def vline_below_dragged(self, obj):
        pass

    def hline_right_dragged(self, obj):
        pass

    def update_profile(self, event=None):
        try:
            y, x = round(self.hline.pos().y()), round(self.vline.pos().x())
#             image_pos = self.im.mapFromScene(self.hline.pos().y(), self.vline.pos().x())
#             print(image_pos)
#             x, y = round(image_pos.y()), round(image_pos.x())
            y = max(y, 0)
            y = min(y, self.image.shape[0]-1)
            self.p_below.setData(self.image[y, :])
            self.hline_right.setPos(y)

            x = max(x, 0)
            x = min(x, self.image.shape[1]-1)
            self.p_right.setData(self.image[:, x], np.arange(len(self.image)))
            self.vline_below.setPos(x)
        except:
            print_exc()
            raise

def iplot(*args, **kwargs):
    sw = SimpleWindow(*args, **kwargs)
    sw.show()
    return sw

def test_iplot():
    def f(x, a, b):
        return np.exp(-a/100.*x) * np.sin(b*x)

    iplot(f, a=(1, 100, 1), b=(1, 10, 1))

def ifit(x, funcs, **kwargs):
    sw = FitTool(x, funcs, ['.', '-'], **kwargs)
    sw.show()
    return sw

def test_ifit():
    def f0(x):
        return 1/(1+np.exp(-x))

    def f(x, a, b):
        return a*x+b

    x = np.arange(-5, 5, 0.1)
    y = f0(x)
    return ifit(x, [y, f], a=(-5., 5.), b=(-5., 5.))

def ishow(im):
    sw = IShow(im)
    sw.show()
    return sw    

def test_ishow():
    im = np.load('peaks2d.npy')
    ishow(im)

class Stretch():
    pass

def _stack(box, *args, ratio=None):
    for arg in args:
        if isinstance(arg, QtWidgets.QLayout):
            box.addLayout(arg)
        elif isinstance(arg, QWidget):
            box.addWidget(arg)
        elif arg is None or isinstance(arg, Stretch):
            box.addStretch()
        else:
            raise ValueError(f'Widget or layout is expected, got {type(arg)}')
    if ratio is not None:
        for i, v in enumerate(ratio):
            box.setStretch(i, v)
    return box

def hStack(*args, parent=None, ratio=None):
    return _stack(QHBoxLayout(parent), *args, ratio=ratio)

def vStack(*args, parent=None, ratio=None):
    return _stack(QVBoxLayout(parent), *args, ratio=ratio)

def hTabs(**kwargs):
    tabs = QTabWidget()
    for k, v in kwargs.items():
        tabs.addTab(v, k)
    return tabs

class HLine(pg.InfiniteLine):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('objectName', None)
        parent = kwargs.pop('parent', None)
        if 'on_drag' in kwargs:
            on_drag = kwargs.pop('on_drag', None)
        else:
            on_drag = kwargs.pop('dragged', None)
        
        kw = dict(movable=True, angle=0, pen='pink')
        kw.update(kwargs)
        super().__init__(*args, **kw)
        if name is not None:
            self.setObjectName(name)
        if parent is not None:
            self.setParent(parent)
        if on_drag is not None:
            self.sigDragged.connect(on_drag)

class VLine(pg.InfiniteLine):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('objectName', None)
        parent = kwargs.pop('parent', None)
        if 'on_drag' in kwargs:
            on_drag = kwargs.pop('on_drag', None)
        else:
            on_drag = kwargs.pop('dragged', None)
        
        kw = dict(movable=True, angle=90, pen='pink')
        kw.update(kwargs)
        super().__init__(*args, **kw)
        if name is not None:
            self.setObjectName(name)
        if parent is not None:
            self.setParent(parent)
        if on_drag is not None:
            self.sigDragged.connect(on_drag)


if __name__ == '__main__':
    from PyQt5.Qt import QApplication

    # start qt event loop
    _instance = QApplication.instance()
    if not _instance:
        _instance = QApplication([])
    app = _instance
    #win = test_iplot()
    win = test_ifit()
    app.exec_()  # и запускаем приложение
