from commonfunctions import *
import time
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Wedge, Polygon, Ellipse, Rectangle
from matplotlib.ticker import AutoMinorLocator
from matplotlib import font_manager as FontManager
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import scipy.optimize as optimize
import os
from PyQt5 import QtGui #, QtCore, QtWidgets

MPL_COLOR = '#555555'
matplotlib.rcParams['text.color'] = MPL_COLOR
matplotlib.rcParams['axes.labelcolor'] = MPL_COLOR
matplotlib.rcParams['xtick.color'] = MPL_COLOR
matplotlib.rcParams['ytick.color'] = MPL_COLOR
matplotlib.rcParams['mathtext.fontset'] = 'cm'
MPL_FONTS = {}
NO_SUBPLOT_MARGINS = {
	"left":0,
	"right":1,
	"bottom":0,
	"top":1,
	"wspace":0,
	"hspace":0
}

def getFont(font, size):
	if font not in MPL_FONTS:
		MPL_FONTS[font] = {}
	if size not in MPL_FONTS[font]:
		MPL_FONTS[font][size] = FontManager.FontProperties(fname=os.path.join(PACKAGEDIR, "fonts", "%s.ttf" % font), size=size)
	return MPL_FONTS[font][size]

def wrapTex(tex):
	return r"$ %s $" % tex

def setAxesFont(font, size, *axes):
	fontproperties = getFont(font, size)
	for ax in axes:
		for label in ax.get_xticklabels():
			label.set_fontproperties(fontproperties)
		for label in ax.get_yticklabels():
			label.set_fontproperties(fontproperties)
class TexWidget(FigureCanvas):
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

