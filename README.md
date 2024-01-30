# qtinteract

A library for building fast interactive plots in Jupyter notebooks using Qt Widgets.

## Installation

    pip install qtinteract

## Usage

```python
    %gui qt5    

    from math import pi
    from qtinteract import iplot

    def f(x, a):
        return np.sin(a*x)

    x = np.linspace(0, 2*pi, 101)

    iplot(x, f, a=(1., 5.))
```
![image](https://github.com/axil/qtinteract/assets/170910/c36fe65e-f0bd-49f5-a6f5-44abdb09a037)

## Troubleshooting

* "Kernel died": you forgot to run `%gui qt5`.

* The window with the plot and the slider does not appear. Look at the taskbar, it might appear behind the browser.
