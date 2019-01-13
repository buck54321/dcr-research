from commonfunctions import *
from qutilities import * # ThreadUtilities
from mplstuff import * # Figure
from PyQt5 import QtGui, QtCore, QtWidgets
from pydcrdata import DcrDataClient
import os
# import tracemalloc
import traceback
from appdirs import AppDirs
APPDIR = AppDirs("explorer", "DecredExplorer").user_data_dir
mkdir(APPDIR)

DCRDATA_URI = "http://localhost:7777/"
# NiceHash price for Decred $190 for 24hrs of 0.46 Ph/s on Jan 1 2019
NICEHASH_RATE = 190/(0.46e15*A_DAY)
TREASURY_TAKE = 0.1
SLIDER_TICKS = 100. # Used for continuous variables
POWER_RATE = 0.05 # Power rate in USD $/kWh

# A model device. Should be roughly the most efficient device on the market.
Device = MODEL_DEVICE

class DecredExplorer(QtCore.QObject, ThreadUtilities):
	def __init__(self, application):
		super().__init__()
		self.application = application
		self.dataClient = DcrDataClient(DCRDATA_URI)
		self.trackedCssItems = set()
		self.dummyWidget = QtWidgets.QWidget()
		self.loadSettings()


		self.mainWindow = DcrExplorerWindow(self)
		self.mainWindow.showMaximized()
	def loadSettings(self):
		"""
		Look for the settings file in ~/.dcrexplorer. If found load it, otherwise create it.
		"""
		self.loadFonts()
		self.settingsDir = os.path.join(APPDIR, "settings")
		mkdir(self.settingsDir)
		self.settingsPath = os.path.join(self.settingsDir, "settings.json")
		self.tempSettingsPath = os.path.join(self.settingsDir, "settings.json.tmp")
		self.settings = fetchSettingsFile(self.settingsPath)
		self.normalizeSettings()
		self.lastSave = time.time()
	def loadFonts(self):
		# see https://github.com/google/material-design-icons/blob/master/iconfont/codepoints
		# for conversions to unicode
		# http://zavoloklom.github.io/material-design-iconic-font/cheatsheet.html
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","MaterialIcons-Regular.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Black.ttf")) 
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-BlackItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Bold.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-BoldItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Italic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Light.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-LightItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Medium.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-MediumItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Regular.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-Thin.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","Roboto-ThinItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-Bold.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-BoldItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-ExtraBold.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-ExtraBoldItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-Italic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-Medium.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-MediumItalic.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-Regular.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-SemiBold.ttf"))
		QtGui.QFontDatabase.addApplicationFont(os.path.join(PACKAGEDIR,"fonts","EBGaramond-SemiBoldItalic.ttf"))
	def normalizeSettings(self):
		settings = self.settings
		self.makeSetting("version", "0.0.1")
		self.makeSetting("price", [0, 0])
		self.makeSetting("theme", "light")
	def makeSetting(self, key, value):
		if key not in self.settings:
			self.settings[key] = value
	def getSettings(self, key):
		if key not in self.settings:
			self.settings[key] = {}
		return self.settings[key]
	def saveSettings(self):
		'''
		Save current settings atomically
		# See https://stackoverflow.com/a/2333979
		'''
		with open(self.tempSettingsPath, 'w') as f:
			f.write(json.dumps(self.settings))
			f.flush()
			os.fsync(f.fileno())
		os.replace(self.tempSettingsPath, self.settingsPath)
		self.lastSave = time.time()
	def saveWithInterval(self, interval):
		tNow = time.time()
		remainder = max(interval - tNow + self.lastSave, 0)
		self.scheduleFunction("save.settings", self.saveSettings, tNow + remainder, noForce=True)
	def saveLowPriority(self):
		self.saveWithInterval(5)
	def saveHighPriority(self):
		self.saveWithInterval(0.5)
	def getPrice(self, maxAge=60):
		"""
		maxAge: Return cached data if age is < maxAge minutes.
		"""
		tNow = time.time()
		priceSettings = self.settings["price"]
		tPrice, price = priceSettings
		if (tNow - tPrice) / 60 < maxAge:
			return price
		try:
			price = float(getUriAsJson("https://api.coinmarketcap.com/v1/ticker/decred/")[0]["price_usd"])
			print("price: %r" % price)
			priceSettings[0] = tNow
			priceSettings[1] = price
			self.saveLowPriority()
			return price
		except Exception as e:
			logger.warning("Error encountered while fetching DCR price from CMC: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
	def getButton(self, size, text, tracked=True):
		"""
		Get a button of the requested size. 
		Size can be one of ["tiny", "small", "medium", "large"].
		The button is assigned a style in accordance with the current template.
		By default, the button is tracked and appropriately updated if the template is updated.

		:param str size: One of ["tiny", "small", "medium", "large"]
		:param str text: The text displayed on the button
		:param bool tracked: default True. Whether to track the button. If its a one time use button, i.e. for a dynamically generated dialog, the button should not be tracked.
		"""
		button = QtWidgets.QPushButton(text, self.dummyWidget)
		button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
		if self.settings["theme"] == "light":
			button.setProperty("button-style-class", "light")
		if size == "tiny":
			button.setProperty("button-size-class", "tiny")
		elif size == "small":
			button.setProperty("button-size-class", "small")
		elif size == "medium":
			button.setProperty("button-size-class", "medium")
		elif size == "large":
			button.setProperty("button-size-class", "large")
		if tracked:
			self.trackedCssItems.add(button)
		return button

class DcrExplorerWindow(QtWidgets.QMainWindow):
	def __init__(self, explorer):
		super().__init__()
		self.explorer = explorer
		explorer.mainWindow = self
		self.settings = explorer.getSettings(self.__class__.__name__)
		self.mainWidget = QtWidgets.QSplitter()
		self.setCentralWidget(self.mainWidget)
		self.resizeEvent = self.resizeSplitter
		self.splitterRatio = 0.7
		self.mainWidget.splitterMoved.connect(self.setSplitterRatio)
		self.plot = DcrAttackCapital(explorer)
		self.mainWidget.addWidget(self.plot)
		self.mainWidget.addWidget(self.plot.controls)
	def resizeSplitter(self, event):
		width = self.width()
		rightRatio = 1 - self.splitterRatio
		self.mainWidget.setSizes([width*self.splitterRatio, width*rightRatio])
	def setSplitterRatio(self, pos, idx):
		l, r = self.mainWidget.sizes()
		self.splitterRatio = l / (l + r)
		self.settings["slitter.ratio"] = self.splitterRatio
		self.explorer.saveLowPriority()

class DcrPlotControlRow(QtWidgets.QWidget):
	def __init__(self, params, callback):
		super().__init__()
		self.params = params
		self.callback = callback
		self.editFont = QtGui.QFont("Roboto", 12)

		self.setAutoFillBackground(True)
		self.setPalette(WHITE_PALETTE)
		self.setContentsMargins(5,5,5,5)
		mainLayout = QtWidgets.QVBoxLayout(self)
		mainLayout.setSpacing(15)
		top, topLayout = makeWidget(QtWidgets.QWidget, "horizontal")
		mainLayout.addWidget(top)

		def makelbl(s, y=15, align=QtCore.Qt.AlignRight):
			lbl = QtWidgets.QLabel(s)
			lbl.setFont(QtGui.QFont('Roboto', y))
			lbl.setAlignment(align)
			return lbl

		symbol = TexWidget(params.getTex(), 14) if params.tex else makelbl("")
		symbol.setToolTip(params.tooltip)
		symbol.setFixedSize(30, 20)
		topLayout.addWidget(symbol)

		valEdit = self.valEdit = self.getLineEdit(params.val)
		topLayout.addWidget(valEdit)
		valEdit.returnPressed.connect(self.valEntered)

		if params.unit:
			topLayout.addWidget(makelbl(params.unit, 12))

		title = makelbl(params.displayName)
		title.setToolTip(params.tooltip)
		title.setContentsMargins(0, 0, 15, 0)
		topLayout.addWidget(title, 1)

		controls, controlLayout = makeWidget(QtWidgets.QWidget, "horizontal", self)
		mainLayout.addWidget(controls)
		
		if params.isAdjustable:
			self.minEdit = self.getLineEdit(params.min)
			controlLayout.addWidget(self.minEdit, 1)
			self.minEdit.returnPressed.connect(self.minEntered)
		else:
			lbl = QtWidgets.QLabel(formatNumber(params.min))
			controlLayout.addWidget(lbl, 1)

		slider = self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, controls)
		slider.wheelEvent = lambda e: None
		controlLayout.addWidget(slider, 8)

		self.xMsg = makeLabel("current x-axis", 22, QALIGN_CENTER)
		self.xMsg.setVisible(False)
		controlLayout.addWidget(self.xMsg, 8)

		if params.isIntegral:
			slider.setRange(params.min, params.max)
		else:
			slider.setRange(0, SLIDER_TICKS)
		sliderPosition = self.normalizeValue(params.val)
		slider.setValue(sliderPosition)

		if params.isAdjustable:
			self.maxEdit = self.getLineEdit(params.max)
			controlLayout.addWidget(self.maxEdit, 1)
			self.maxEdit.returnPressed.connect(self.maxEntered)
		else:
			lbl = QtWidgets.QLabel(formatNumber(params.max))
			controlLayout.addWidget(lbl, 1)

		slider.sliderMoved.connect(self.sliderMoved)

	def getLineEdit(self, value):
		edit = QtWidgets.QLineEdit(formatNumber(value))
		edit.setFixedWidth(65)
		edit.setFont(self.editFont)
		edit.setAlignment(QtCore.Qt.AlignCenter)
		return edit
	def getLimits(self):
		params = self.params
		return params.min, params.max
	def normalizeValue(self, value):
		if self.params.isIntegral:
			return int(round(value))
		minVal, maxVal = self.getLimits()
		value = clamp(value, minVal, maxVal)
		return int(round((value - minVal)/(maxVal - minVal)*SLIDER_TICKS))
	def denormalizeValue(self, sliderVal):
		if self.params.isIntegral:
			return sliderVal
		minVal, maxVal = self.getLimits()
		valRange = maxVal - minVal
		return minVal + valRange*(sliderVal/SLIDER_TICKS)
	def sliderMoved(self, value):
		self.setVal(self.denormalizeValue(value))
	def paramsAndCaster(self):
		return self.params, int if self.params.isIntegral else float
	def valEntered(self):
		self.setVal(self.valEdit.text())
	def minEntered(self):
		proposal = self.minEdit.text()
		params, caster = self.paramsAndCaster()
		try:
			val = caster(proposal)
			if val < params.max:
				params.min = val
				params.val = clamp(params.val, params.min, params.max)
		except:
			self.minEdit.setText(params.min)
			print("Failed to translate min value input %s" % proposal)
	def maxEntered(self):
		proposal = self.maxEdit.text()
		params, caster = self.paramsAndCaster()
		try: 
			val = caster(proposal)
			if val > params.min:
				params.max = val
				params.val = clamp(params.val, params.min, params.max)
		except:
			self.maxEdit.setText(params.max)
			print("Failed to translate max value input %s" % proposal)
	def setVal(self, val):
		params, caster = self.paramsAndCaster()
		params.val = clamp(caster(val), params.min, params.max)
		self.valEdit.setText(formatNumber(params.val))
		self.slider.setValue(self.normalizeValue(params.val))
		self.callback(params.val)




class ParameterManager:
	"""
	ParameterManager manages the first level attributes of a standard python dict (`paramBox`). 
	The passed dict is modified in place, so as to be compatible with a json-serializable settings object. 
	This allows state to be stored and maintained across sessions. 
	"""
	def __init__(self, paramBox):
		self.__dict__["dcrParams"] = {}
		self.paramBox = paramBox
		self.keys = []
	def __getitem__(self, key):
		if key in self.dcrParams:
			return self.dcrParams[key]
		raise KeyError("%s not found in parameters for ParameterManager" % (key, ))
	def __getattr__(self, key):
		if key in self.dcrParams:
			return self.dcrParams[key]
		if key in self.__dict__:
			return self.__dict__[key]
		raise AttributeError("%s not found in parameters for ParameterManager" % (key, ))
	def __setattr__(self, key, val):
		if key in self.dcrParams:
			self.dcrParams[key] = val
			return
		self.__dict__[key] = val
	def __contains__(self, key):
		if key in self.dcrParams:
			return True
		return False
	def addParameter(self, name, minVal, maxVal, val, isIntegral, displayName, callback=None, isAdjustable=True, tex=None, unit=None, description=None, **kwargs):
		if name not in self.paramBox:
			self.paramBox[name] = {}
		params = self.paramBox[name]
		self.keys.append(name)
		self.dcrParams[name] = DcrParameter(name, params, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs)
		return self.dcrParams[name]
	def getParams(self):
		# generator
		for k in self.keys():
			yield self.dcrParams[k]
	def enableAll(self):
		for param in self.dcrParams.values():
			param.enable()

class DcrParameter:
	"""
	DcrParameter maintains the state of an object, as well as some common metadata.
	DcrParameter is careful not modify the object in place, or overwrite previously stored settings, so that a reference to a settings object attribute can be maintained.
	The three default subparameters + kwargs can be accessed as attributes, i.e. param.min, param.max, param.val, ..., or 
	"""
	def __init__(self, name, params, minVal, maxVal, val, isIntegral, displayName, callback=None, isAdjustable=True, tex=None, unit=None, description=None, **kwargs):
		# params should maybe be called subparams or something here
		self.__dict__["params"] = params
		self.name = name
		# Use addif to avoid overwriting user-set parameters from storage.
		def addif(k, v):
			if k not in params:
				params[k] = v
		addif("min", minVal)
		addif("max", maxVal)
		addif("val", val)
		for k, v in kwargs.items():
			addif(k, v)
		self.isIntegral = isIntegral
		self.displayName = displayName
		self.isAdjustable = isAdjustable
		self.tex = tex if tex else ""
		self.unit = unit if unit else ""
		self.description = description if description else ""
		self.callback = callback
		tooltipRows = [displayName]
		if unit:
			tooltipRows.append("units: %s" % unit)
		if description:
			tooltipRows.append(description)
		self.tooltip = "\n".join(tooltipRows)
		self.widget = DcrPlotControlRow(self, self.valChanged)
		self.setVal = self.widget.setVal
	def __setitem__(self, key, val):
		self.params[key] = val
	def __getitem__(self, key):
		if key in self.params:
			return self.params[key]
		raise KeyError("%s not found in sub-parameters for DcrParameter %s" % (key, self.name))
	def __getattr__(self, key):
		if key in self.params:
			return self.params[key]
		if key in self.__dict__:
			return self.__dict__[key]
		raise AttributeError("No sub-parameter %s in DcrParameter %s" % (key, self.name))
	def __setattr__(self, key, val):
		if key in self.params:
			self.params[key] = val
			return
		self.__dict__[key] = val
	def setSubParameter(self, key, val):
		self.params[key] = val
	def valChanged(self, val):
		self.val = val
		if self.callback: 
			self.callback(self.name, val)
	def getTex(self):
		if not self.tex:
			return ""
		return wrapTex(self.tex)
	def enable(self):
		self.widget.slider.setVisible(True)
		self.widget.xMsg.setVisible(False)
	def xDisable(self):
		self.widget.slider.setVisible(False)
		self.widget.xMsg.setVisible(True)

class DcrAttackCapital(QtWidgets.QWidget):
	def __init__(self, explorer):
		super().__init__()
		self.explorer = explorer
		self.settings = explorer.getSettings(self.__class__.__name__)
		self.x1 = None
		self.reportFetch = explorer.makeThreadSafeVersion(self._reportFetch)

		self.layout = QtWidgets.QVBoxLayout(self)

		controlRows, self.controlLayout = makeWidget(QtWidgets.QWidget, "vertical")
		self.controlLayout.setSpacing(20)
		controlRows.setAutoFillBackground(True)
		controlRows.setPalette(WHITE_PALETTE)
		
		sa = self.controls = QtWidgets.QScrollArea()
		# sa.setLineWidth(0)
		sa.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		sa.setAlignment(QtCore.Qt.AlignTop)
		sa.setWidgetResizable(True)
		sa.setWidget(controlRows)
		sa.setContentsMargins(0,0,0,0)
		# self.widgetsColumn.setSpacing(5)
		# self.widgetsColumnScrollbar = sa.verticalScrollBar()
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		# self.updateGeometry()

		def verticalbar():
			wgt, lyt = makeWidget(QtWidgets.QWidget, "horizontal")
			lyt.addStretch(1)
			line = QtWidgets.QFrame()
			setBackgroundColor(line, "#555555")
			line.setFixedWidth(1)
			line.setContentsMargins(0, 20, 0, 20)
			line.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding)
			lyt.addWidget(line)
			lyt.addStretch(1)
			return wgt

		topWgt, topLyt = makeWidget(QtWidgets.QWidget, "horizontal")
		topLyt.setSpacing(5)
		self.layout.addWidget(topWgt)
		topWgt.setMaximumHeight(175)
		setBackgroundColor(topWgt, "white")

		w, equations = makeWidget(QtWidgets.QWidget, "vertical")
		topLyt.addWidget(w)
		topLyt.addWidget(verticalbar(), 2)
		
		self.equation = TexWidget(r"$A(y) = ar_et_a +\left( H_a - a \right) \left(\rho + \frac{ c t_a }{ \eta } \right) + yZp_t$")
		equations.addWidget(self.equation, 1)

		self.subEquation = TexWidget(r"$ H_a = \frac{ 86400 s \sigma(y) R_{tot}(h) X }{ t_b (\alpha\rho + 0.24 c / \eta) } $")
		equations.addWidget(self.subEquation, 1)

		#defaults for price, ticketPrice, blockHeight, roi
		defaultLabels = self.defaultLabels = {}
		rowCounter = 0
		w, defaults = makeWidget(QtWidgets.QWidget, "grid")
		w.setContentsMargins(5, 5, 5, 5)
		topLyt.addWidget(w)
		defaults.addWidget(makeLabel("Network parameters", 18), rowCounter, 1, 1, 2)
		rowCounter += 1
		bttn = explorer.getButton("tiny", "fetch")
		bttn.clicked.connect(self.fetch)
		defaults.addWidget(bttn, rowCounter, 1)
		bttn = explorer.getButton("tiny", "use")
		bttn.clicked.connect(self.useFetch)
		defaults.addWidget(bttn, rowCounter, 2)
		rowCounter += 1
		def addDefault(name, text):
			defaults.addWidget(makeLabel(text, 15, QALIGN_LEFT), rowCounter, 1)
			lbl = defaultLabels[name] = makeLabel("fetching...", 15, QALIGN_LEFT)
			lbl.currentValue = None
			lbl.setMinimumWidth(75)
			defaults.addWidget(lbl,  rowCounter, 2)
		addDefault("price", "exchange rate (USD): ")
		rowCounter += 1
		addDefault("blockHeight", "block height: ")
		rowCounter += 1
		addDefault("ticketPrice", "ticket price (USD): ")
		rowCounter += 1
		addDefault("roi", "profitability: ")
		topLyt.addWidget(verticalbar(), 2)

		# Select the x axis(axes).
		w, selectors = makeWidget(QtWidgets.QWidget, "vertical")
		w.setContentsMargins(5, 5, 5, 5)
		topLyt.addWidget(w)
		topLyt.addStretch(1)

		selectors.addWidget(makeLabel("select x", 22))

		# populate = explorer.getButton("small", "get current values")
		# selectors.addWidget(populate)
		# populate.clicked.connect(lambda s: print("populating"))

		xGridWgt, self.xGrid = makeWidget(QtWidgets.QWidget, "grid")
		selectors.addWidget(xGridWgt)
		self.xGridColumns = 4
		self.dragWgt = None


		self.tickFont = getFont("EBGaramond-Regular", 16)
		self.axisFont = getFont("EBGaramond-Regular", 20)
		self.titleFont = getFont("EBGaramond-Regular", 22)
		self.figure2d = Figure()
		self.canvas2d = FigureCanvas(self.figure2d)
		ax = self.axes2d = self.figure2d.add_subplot("111")
		ax.set_ylabel(r"Attack Cost, $ A $ (billion USD)", fontproperties=self.axisFont)
		ax.set_xlabel(" ", fontproperties=self.axisFont)
		self.layout.addWidget(self.canvas2d)

		self.figure3d = Figure()
		self.canvas3d = FigureCanvas(self.figure3d)
		self.canvas3d.setVisible(False)
		self.axes3d = self.figure3d.add_subplot("111", projection="3d")
		# self.canvas3d.setVisible(False)
		self.layout.addWidget(self.canvas3d)

		self.normalizeSettings()
		self.fetch()
	def normalizeSettings(self):
		if "params" not in self.settings:
			self.settings["params"] = {}
		self.paramBox = self.settings["params"]
		params = self.params = ParameterManager(self.paramBox)
		callback = self.valChanged
		# addParameter: name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs
		self.registerParam("attackDuration", 0.5, 24, 12, False, "Attack duration", callback, True, r"t_a", "hours", "The total time of the attack.")
		self.registerParam("roi", -1., 5., 0.5, False, "Profitability", callback, True, r"\alpha", None, "POW profitability. Daily earnings as a fraction of device cost.")
		self.registerParam("price", 10, 30, 20, False, "Exchange rate", callback, True, r"X", "USD", "Exhange rate.")
		self.registerParam("N", 1, 10, 5, True, "Stake winners", callback, True,  r"N", "tickets", "POS validators per block.")
		self.registerParam("blockTime", 0.5, 15, 5, False, "Block time", callback, True, r"t_b", "minutes", "Block time. The network block time target.")
		self.registerParam("minerShare", 1., 99., 60., False, "POW reward share (%)", callback, True, r"s", None, "Fraction of total block reward given to POW miner.")
		self.registerParam("blockHeight", 3e5, 6e5, 305000, True, "Block height", callback, True, r"h", None, "Blockchain length.")
		self.registerParam("participation", 1., 100., 100., False, "Participation (%)", callback, True, r"p", None, "Participation level. Fraction of tickets which belong to an online stakeholder.")
		self.registerParam("poolSize", 1000, 100000, TICKETPOOL_SIZE, True, "Ticket pool size", callback, True, r"Z", "tickets", "Ticket pool size. A network parameter.")
		self.registerParam("ticketPrice", 10, 10000, 2000, False, "Ticket price (USD)", callback, True, r"p_t", "USD", "Ticket price.")
		self.registerParam("rentability", 0., 2e6, 1000, False, "Rentability", callback, True, r"a", "terahash/s", "Amount of hashing power available on the rental market")
		self.registerParam("rentalRate", NICEHASH_RATE*0.5, NICEHASH_RATE*1.5, NICEHASH_RATE, False, "Rental rate", callback, True, r"r_e", "USD/terahash", "Rental rate.")
	def registerParam(self, name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs):
		p = self.params.addParameter(name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs)
		self.controlLayout.addWidget(p.widget)
		texWgt = TexWidget(wrapTex(p.tex), 20)
		texWgt.setToolTip(p.tooltip)
		texWgt.setFixedSize(35, 35)
		texWgt.enterEvent = lambda e, w=texWgt: self.xGridEnter(w)
		texWgt.leaveEvent = lambda e, w=texWgt: self.xGridLeave(w)
		texWgt.mousePressEvent = lambda e, w=texWgt: self.xGridDown(w)
		texWgt.mouseReleaseEvent = lambda e, w=texWgt: self.xGridUp(w)
		texWgt.param = p
		xGrid = self.xGrid
		xCount = xGrid.count()
		cols = self.xGridColumns
		xGrid.addWidget(texWgt, int(xCount/cols), xCount%cols)
	def xGridEnter(self, widget):
		widget.setFacecolor("#ccffdd")
	def xGridLeave(self, widget):
		widget.setFacecolor()
	def xGridDown(self, widget):
		self.gridWgt = widget
	def xGridUp(self, widget):
		if widget == self.gridWgt:
			for w in layoutWidgets(self.xGrid):
				w.defaultColor = "white"
				w.setFacecolor()
			widget.defaultColor = "#ccddff"
			widget.setFacecolor()
			self.x1 = widget.param
			self.plot()
	def writeEquation(self):
		# H_a = \frac{ 86400 s \sigma(y) R_{tot}(h) X }{ t_b (\alpha\rho + 0.24 c / \eta) }
		return 
	def valChanged(self, key, val):
		print("%s val changed to %r" % (key, val))
		print("calc result: %r" % self.calc({}))
	def fetch(self):
		self.explorer.makeThread(self.reallyFetch)
	def reallyFetch(self):
		price = self.explorer.getPrice()
		self.reportFetch("price", price, formatNumber(price, isMoney=True))
		client = self.explorer.dataClient
		bestBlock = client.block.best()
		hBest = bestBlock["height"]
		self.reportFetch("blockHeight", hBest, str(hBest))
		self.reportFetch("ticketPrice", bestBlock["ticket_pool"]["valavg"]*price)
		bestBlockVerbose = client.block.best.verbose()
		dayBlocks = int(A_DAY / BLOCKTIME)
		dayOldBlock = client.block.verbose(hBest - dayBlocks)
		deltaH = hBest - dayOldBlock["height"]
		deltaT = bestBlock["time"] - dayOldBlock["time"]
		nethash = (int(bestBlockVerbose["chainwork"], 16) - int(dayOldBlock["chainwork"], 16))/(deltaT)
		blockTime = deltaT/deltaH
		roi = Device["hashrate"]/nethash*dailyPowRewards(hBest, blockTime)*price/Device["price"]*100
		self.reportFetch("roi", roi)
	def _reportFetch(self, k, v, text=None):
		if k not in self.defaultLabels or k not in self.params:
			return
		lbl = self.defaultLabels[k]
		lbl.currentValue = v
		lbl.setText(text if text else formatNumber(v))
	def useFetch(self):
		for k, lbl in self.defaultLabels.items():
			if not lbl.currentValue:
				continue
			self.params[k].setVal(lbl.currentValue)
	def calc(self, overrides):
		'''
		overrides will be used in place of native parameters
		'''
		params = self.params
		def resolve(k):
			if k in overrides:
				return overrides[k]
			return params[k].val
		attackDuration = resolve("attackDuration")*3600
		price = resolve("price")
		minerShare = resolve("minerShare")/100.
		participation = resolve("participation")/100.
		poolSize = resolve("poolSize")
		ticketPrice = resolve("ticketPrice")
		roi = resolve("roi")
		N = resolve("N")
		blockHeight = resolve("blockHeight")
		blockTime = resolve("blockTime")*60
		rentability = resolve("rentability")
		rentalRate = resolve("rentalRate")
		lowest = 1e16
		for poolPct in range(1, 100):	
			poolPortion = poolPct/100.
			hashPortion = hashportion(poolPortion, N, participation)
			ticketInvestment = poolPortion*poolSize*ticketPrice*price
			hashrate = networkHashrate(Device, price, roi, blockHeight, blockTime, minerShare)*hashPortion
			rentalPart = min(rentability, hashrate)
			retailPart = hashrate - rentalPart
			attackCost = rentalPart*rentalRate*attackDuration + ticketInvestment + retailPart*( Device["relative.price"] + ( PRIME_POWER_RATE*attackDuration/Device["power.efficiency"] ) )
			lowest = min(lowest, attackCost)
		return lowest
	def plot(self):
		self.explorer.scheduleFunction("plot", self.actuallyPlot, time.time()+1)
	def actuallyPlot(self):
		print("plotting with x1 = %s" % self.x1.name)
		variable = self.x1
		self.params.enableAll()
		variable.xDisable()
		if variable.isIntegral:
			X = range(variable.min, variable.max + 1)
		else:
			X = np.arange(variable.min, variable.max, (variable.max-variable.min)/100)
		Y = []
		for x in X:
			Y.append(self.calc({variable.name: x}))
		ax = self.axes2d
		lines = ax.get_lines()
		#scale Y
		Y = [y/1e9 for y in Y]
		if lines:
			lines[0].set_data(X, Y)
		else:
			ax.plot(X, Y)
		ax.set_xlim(left=min(X), right=max(X))
		ax.set_ylim(bottom=min(Y), top=max(Y))
		ax.set_title('Attack cost vs %s' % variable.displayName, fontproperties=self.titleFont)
		ax.set_xlabel(r"%s, $ %s $%s" % (variable.displayName, variable.tex, " (%s)" % variable.unit if variable.unit else ""))
		for label in ax.get_xticklabels():
			label.set_fontproperties(self.tickFont)
		for label in ax.get_yticklabels():
			label.set_fontproperties(self.tickFont)
		self.figure2d.canvas.draw()
	def plotAttackCost(self, rental=True, logScale=False):
		plt.subplots_adjust(0.25, 0.25, 0.90, 0.85, 0, 0.1)
		ax = self.axes3d
		# ax.semilogy()
		# best device available
		device = devices["asic"]["high"]
		# exchange rate
		x = np.arange(1, 100, 0.5)
		# ticket price
		y = np.arange(10, 500, 10)
		xcRates, tPrices = np.meshgrid(x, y)
		investments = np.array([investmentFunc(tPrice, xcRate) for xcRate, tPrice in zip(np.ravel(xcRates), np.ravel(tPrices))]).reshape(xcRates.shape)
		logFunc = np.log10 if logScale else lambda x: x
		zticks = np.arange(0, 26e6, 5e6)
		ax.set_zticks(logFunc(zticks))
		ax.set_zticklabels(["%.1f" % (z/1e6) for z in zticks])
		ax.set_zlim((0, 25e6))
		ax.set_xlabel('exchange rate (USD)')
		ax.set_ylabel('ticket price (DCR)')
		ax.set_zlabel('net capital (million USD)')
		ax.plot_surface(xcRates, tPrices, logFunc(investments), cmap="viridis")
		plt.show()

class DcrLoadingAnimation(QtWidgets.QGraphicsItem):
	""" A loading animation that covers a widget. """
	def __init__(self, *args, **kwargs):
		super(QStrataGraphicsItem, self).__init__(*args, **kwargs)
	def boundingRect(self):
		"""
		Any class that inherits QGraphicsItem must override this method. 
		It should probably be a little smarter
		"""
		return QtCore.QRectF(-10000, -10000, 20000, 20000)


def runDecredExplorer():
	QtWidgets.QApplication.setDesktopSettingsAware(False)
	QtWidgets.QApplication.setFont(QtGui.QFont("Roboto"));
	app = QtWidgets.QApplication(sys.argv)

	explorer = DecredExplorer(app)

	icon = QtGui.QIcon(os.path.join(PACKAGEDIR, "logo.svg"))
	app.setWindowIcon(icon)
	app.setStyleSheet(QUTILITY_STYLE)
	explorer.mainWindow.setWindowIcon(icon)
	try:
		app.exec_()
	except Exception as e:
		try:
			logger.warning("Error encountered: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
		except Exception as e2:
			pass
		finally:
			print("Error encountered: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
	app.deleteLater()
	return

if __name__ == '__main__':
	runDecredExplorer()
