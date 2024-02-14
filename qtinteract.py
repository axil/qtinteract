from traceback import print_exc
from math import pi
import inspect

import numpy as np
from scipy.optimize import curve_fit

from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QDoubleSpinBox, QVBoxLayout, \
     QGridLayout, QPushButton, QHBoxLayout, QTabWidget
from PyQt5.QtCore import Qt
import pyqtgraph
import pyqtgraph as pg 
from PyQt5 import QtWidgets

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('imageAxisOrder', 'row-major')

def spin2slider(v, vmin, vmax, n):
    return round((v-vmin)/(vmax-vmin)*n)

#def slider2spin(x, vmin, vmax):
#    return vmin + (x/100)*(vmax-vmin)

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
        self.layout = QVBoxLayout(self)
        self.canvas0 = pg.PlotWidget()
        self.canvas0.addLegend()
        self.image = arr
        self.im = pg.ImageItem(self.image)
        self.im.setColorMap(pg.colormap.get('viridis'))
        self.im.hoverEvent = self.update_profile
        self.canvas0.addItem(self.im)
        self.layout.addWidget(self.canvas0)
        
        self.tabs = QTabWidget()
        
        self.canvas1 = pg.PlotWidget()
        self.p1 = self.canvas1.plot([], pen='b', name='p0')
        self.tabs.addTab(self.canvas1, 'horizontal')

        self.canvas2 = pg.PlotWidget()
        self.p2 = self.canvas2.plot([], pen='b', name='p0')
        self.tabs.addTab(self.canvas2, 'vertical')
        
        self.layout.addWidget(self.tabs)
        
    def update_profile(self, event):
        try:
            if hasattr(event, '_scenePos'):
                image_pos = self.im.mapFromScene(event.scenePos())
                x, y = round(image_pos.x()), round(image_pos.y())
                if self.tabs.currentIndex() == 0:
                    y = max(y, 0)
                    y = min(y, self.image.shape[0]-1)
                    self.p1.setData(self.image[y, :])
                else:
                    x = max(x, 0)
                    x = min(x, self.image.shape[1]-1)
                    self.p2.setData(self.image[:, x])
        except:
            print_exc()
            raise
        
class ITransform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setGeometry(300, 300, 400, 300)
        self.setWindowTitle('Hello World')

        self.layout = QVBoxLayout(self)
        self.canvas = pg.PlotWidget()
        self.canvas.addLegend()
        self.im = pg.ImageItem(np.asarray(im))
        self.im.setColorMap(pg.colormap.get('viridis'))
        self.canvas.addItem(self.im)

        self.layout.addWidget(self.canvas)
        
        self.slider1 = QSlider()
        self.slider1.setOrientation(Qt.Horizontal)
        self.slider1.setObjectName("myslider1")
        self.slider1.setRange(-90, 90)
        self.layout.addWidget(self.slider1)

        self.slider2 = QSlider()
        self.slider2.setOrientation(Qt.Horizontal)
        self.slider2.setObjectName("myslider2")
        self.slider2.setRange(-1000, 1000)
        self.layout.addWidget(self.slider2)
        
        
        QMetaObject.connectSlotsByName(self)
#        self.slider1.sliderMoved.connect(self.go)
        
    @slot(int)
    def on_myslider1_sliderMoved(self, alpha):
#    def go(self, x):
#        print(x)
        x = self.slider2.value()
        #im = Image.fromarray(a)
        self.im.setImage(np.roll(np.asarray(im.rotate(alpha)), 3*x))

    @slot(int)
    def on_myslider2_sliderMoved(self, x):
#    def go(self, x):
#        print(x)
        try:
            alpha = self.slider1.value()
            
            self.im.setImage(np.roll(np.asarray(im.rotate(alpha)), 3*x))
        except:
            print_exc()
    

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
        

def test_ishow():
    im = np.load('peaks2d.npy')
    ishow(im)

def itransform():
    sh = ITransform()
    sh.show()

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
