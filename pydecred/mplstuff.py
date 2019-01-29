from pydecred import helpers
import matplotlib
from matplotlib.figure import Figure
# from matplotlib.patches import Circle, Wedge, Polygon, Ellipse, Rectangle
# from matplotlib.ticker import AutoMinorLocator
from matplotlib import font_manager as FontManager
from mpl_toolkits.mplot3d import Axes3D # leave this even if the linter complains
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# import scipy.optimize as optimize
import os

MPL_COLOR = '#555555'
matplotlib.rcParams['mathtext.fontset'] = 'cm'
MPL_FONTS = {}
NO_SUBPLOT_MARGINS = {
    "left": 0,
    "right": 1,
    "bottom": 0,
    "top": 1,
    "wspace": 0,
    "hspace": 0
}


def setDefaultAxesColor(color):
    """
    Set the default color axes labels and lines.
    """
    matplotlib.rcParams['text.color'] = color
    matplotlib.rcParams['axes.labelcolor'] = color
    matplotlib.rcParams['xtick.color'] = color
    matplotlib.rcParams['ytick.color'] = color


setDefaultAxesColor(MPL_COLOR)


def getFont(font, size):
    """
    Create a `FontProperties` from a font in the /fonts directory.
    """
    if font not in MPL_FONTS:
        MPL_FONTS[font] = {}
    if size not in MPL_FONTS[font]:
        MPL_FONTS[font][size] = FontManager.FontProperties(
            fname=os.path.join(helpers.PACKAGEDIR, "fonts", "%s.ttf" % font), 
            size=size
        )
    return MPL_FONTS[font][size]


def wrapTex(tex):
    """ Wrap string in the Tex delimeter `$` """
    return r"$ %s $" % tex


def setAxesFont(font, size, *axes):
    """ Set the font for the `matplotlib.axes.Axes`"""
    fontproperties = getFont(font, size)
    for ax in axes:
        for label in ax.get_xticklabels():
            label.set_fontproperties(fontproperties)
        for label in ax.get_yticklabels():
            label.set_fontproperties(fontproperties)


class TexWidget(FigureCanvas):
    """A Qt5 compatible widget with a Tex equation"""
    def __init__(self, equation, fontSize=20):
        self.equation = equation    
        self.fig = Figure()
        self.fig.subplots_adjust(**NO_SUBPLOT_MARGINS)
        super().__init__(self.fig)
        ax = self.axes = self.fig.add_subplot("111")
        ax.axis("off")
        ax.set_xlim(left=0, right=1)
        ax.set_ylim(top=1, bottom=0)
        text = ax.text(0.5, 0.5, equation, fontsize=fontSize, horizontalalignment="center", verticalalignment="center")
        self.updateText = lambda s: text.set_text(s)
        self.defaultColor = "white"

    def setFacecolor(self, color=None):
        self.fig.set_facecolor(color if color else self.defaultColor)
        self.fig.canvas.draw()