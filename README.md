# qtinteract

A library for building fast interactive plots in Jupyter notebooks using Qt Widgets.

## Installation

    pip install qtinteract

## Usage

    %gui qt5    

    from math import pi
    from qtinteract import iplot

    def f(x, a):
        return np.sin(a*x)

    x = np.linspace(0, 2*pi, 101)

    iplot(x, f, a=(1., 5.))
