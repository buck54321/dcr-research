from pydecred import helpers, mpl, calc, mainnet
from pydecred import constants as C
from pydecred.dcrdata import DcrDataClient, getPGArchivist
from pydecred.cmcapi import CMCClient
import qutilities as Q
from PyQt5 import QtGui, QtCore, QtWidgets
import os
import sys
import time
import json
# import tracemalloc
import traceback

# import matplotlib.pyplot as plt
import numpy as np

# from appdirs import AppDirs
# APPDIR = AppDirs("explorer", "DecredExplorer").user_data_dir
# mkdir(APPDIR)

APPDIR = helpers.appDataDir("DecredExplorer")
helpers.mkdir(APPDIR)
# NiceHash price for Decred 0.0751/PH/day
NICEHASH_RATE = 0.0751/1e12
DCRDATA_URI = "http://localhost:7777/"
dataClient = DcrDataClient(DCRDATA_URI)

cmcDir = os.path.join(APPDIR, "cmc")
helpers.mkdir(cmcDir)
cmcClient = CMCClient(cmcDir)

logger = helpers.ConsoleLogger

SLIDER_TICKS = 100.

PARAM_REG = 1
PARAM_REV = 2
PARAM_BOTH = PARAM_REG | PARAM_REV

# A model device. Should be roughly the most efficient device on the market.
Device = helpers.makeDevice(**C.MODEL_DEVICE)

DeviceRanges = {
    "asic": {},
    "gpu": {}
}

DeviceRanges["asic"]["low"] = helpers.makeDevice(
    "Baikal Giant B", 399, hashrate=160e9, power=410, release="2018-01-31")

DeviceRanges["asic"]["high"] = Device

DeviceRanges["gpu"]["low"] = helpers.makeDevice(
    "RX 480", 200, hashrate=575e6, power=140, release="2016-06-01")

DeviceRanges["gpu"]["high"] = helpers.makeDevice(
    "GTX 1080 Ti", 475, hashrate=3.8e9, power=216, release="2017-03-10")

# State-of-the-art devices for a range of algorithms.
DeviceParams = {}
DeviceParams["Blake256r14"] = Device

DeviceParams["Equihash <200,9>"] = helpers.makeDevice(
    "Bitmain Z9", 3300, hashrate=41e3, power=1150)

DeviceParams["Ethash"] = helpers.makeDevice(
    "Antminer E3", 3300, hashrate=41e3, power=1150)

DeviceParams["ProgPOW"] = helpers.makeDevice(
    "GeForce 1080 Ti", 475, hashrate=22e6, power=275)

DeviceParams["Cryptonight V8"] = helpers.makeDevice(
    "GeForce 1080 Ti", 475, hashrate=950, power=180)

DeviceParams["Cryptonight V8"] = helpers.makeDevice(
    "GeForce 1080 Ti", 475, hashrate=950, power=180)

DeviceParams["Sha256"] = helpers.makeDevice(
    "Antminer S15", 1475, hashrate=28e12, power=1596)


def getDbHeight():
    """
    Grab the best block height from a DCRData DB.
    """
    archivist = getPGArchivist()
    return archivist.getQueryResults("SELECT height FROM blocks ORDER BY height DESC LIMIT 1")[0][0]


def getDcrDataHashrate(height=None):
    """
    Get the network hashrate average for the last day-ish.
    """
    height = height if height else int(dataClient.block.best.height())
    block = dataClient.block.verbose(height)
    oldBlock = dataClient.block.verbose(int(height - C.DAY/mainnet.TargetTimePerBlock))
    return (int(block["chainwork"], 16) - int(oldBlock["chainwork"], 16))/(block["time"] - oldBlock["time"])


def getDcrDataProfitability(xcRate, height=None, device=None):
    """
    Get current mining profitability from DCRData.
    """
    device = device if device else C.MODEL_DEVICE
    height = height if height else int(dataClient.block.best.height())
    nethash = getDcrDataHashrate(height)
    gross = device["hashrate"]/nethash*calc.dailyPowRewards(height)*xcRate
    power = device["power"]*24/1000*C.PRIME_POWER_RATE
    return (gross - power)/device["price"]


def getDcrDataAPY(method="current", height=None):
    """
    Get current stake profitability from DCRData.

    dataClient.block.best()["ticket_pool"]["valavg"] is the average price of the
    tickets in the ticket pool

    dataClient.block.best()["sdiff"] is the current ticket price

    dataClient.tx(dataClient.block.best.verbose()["stx"][i])["vin"][0]["amountin"] is the price paid by winner i
    dataClient.tx(dataClient.block.best.verbose()["stx"][i])["vin"][1]["amountin"] is the reward for winner i (should be the same for all "stx")
    """
    if method == "this.block":
        block = dataClient.block.best.verbose()
        juice = principal = 0
        for txid in block["stx"]:
            vin = dataClient.tx(txid)["vin"]
            if "stakebase" in vin[0]:
                juice += vin[0]["amountin"]
                principal += vin[1]["amountin"]
    if method == "prospective":
        height = height if height else dataClient.block.best.height()
        principal = dataClient.block.best()["sdiff"]
        juice = calc.blockReward(height + int(mainnet.TicketPoolSize/2))*mainnet.STAKE_SPLIT/mainnet.TicketsPerBlock
    if method == "current":
        height = height if height else dataClient.block.best.height()
        principal = dataClient.block.best()["ticket_pool"]["valavg"]
        juice = calc.blockReward(height)*mainnet.STAKE_SPLIT/mainnet.TicketsPerBlock

    power = 365/28
    return (juice/principal + 1)**power - 1


def fetchCMCHistory():
    """
    Updates the coinmarketcap history file.
    """
    cmcClient.fetchHistory(C.CMC_TOKEN)


def fetchCMCPrice():
    """
    Grabs the current DCR-USD exchange rate from coinmarketcap.
    """
    return float(cmcClient.fetchPrice(C.CMC_TOKEN)[0]["price_usd"])


class DecredExplorer(QtCore.QObject, Q.ThreadUtilities):
    def __init__(self, application):
        super().__init__()
        self.application = application
        self.trackedCssItems = set()
        self.dummyWidget = QtWidgets.QWidget()
        self.loadSettings()
        self.mainWindow = DcrExplorerWindow(self)
        self.mainWindow.showMaximized()

    def loadSettings(self):
        """
        Look for the settings file in ~/.dcrexplorer. If found load it, otherwise create it.
        """
        self.settingsDir = os.path.join(APPDIR, "settings")
        helpers.mkdir(self.settingsDir)
        self.settingsPath = os.path.join(self.settingsDir, "settings.json")
        self.tempSettingsPath = os.path.join(self.settingsDir, "settings.json.tmp")
        self.settings = helpers.fetchSettingsFile(self.settingsPath)
        self.normalizeSettings()
        self.lastSave = time.time()

    def normalizeSettings(self):
        self.makeSetting("version", "0.0.1")
        self.makeSetting("xcRate", [0, 0])
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
        self.activeWidget = None
        explorer.mainWindow = self
        Q.setBackgroundColor(self, "white")
        self.mainWidget, self.mainLayout = Q.makeWidget(QtWidgets.QWidget, "vertical")
        self.setCentralWidget(self.mainWidget)
        self.activeWidget = None

        self.settings = explorer.getSettings(self.__class__.__name__)
        self.windowSelector = select = QtWidgets.QComboBox(self.mainWidget)
        select.setItemDelegate(QtWidgets.QStyledItemDelegate()) # this is needed for the qlistview items to obey stylesheet settings
        select.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        select.currentTextChanged.connect(self.activateWidget)        

        self.widgetMap = {}
        self.widgetMap["Attack cost calculator"] = self.attackCapital = DcrAttackCapital(explorer, self)

        select.addItems(self.widgetMap.keys())
        self.activateWidget("Attack cost calculator")

    def resizeEvent(self, e):
        if self.activeWidget:
            self.activeWidget.resized(e)

    def activateWidget(self, key):
        self.activeWidget = widget = self.widgetMap[key]
        Q.clearLayout(self.mainLayout)
        self.mainLayout.addWidget(widget.windowWidget)
        widget.activate()


class DcrPlotControlRow(QtWidgets.QWidget):
    def __init__(self, params, callback):
        super().__init__()
        self.params = params
        self.callback = callback
        self.editFont = QtGui.QFont("Roboto", 12)

        self.setAutoFillBackground(True)
        self.setPalette(Q.WHITE_PALETTE)
        self.setContentsMargins(5, 5, 5, 5)
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setSpacing(15)
        top, topLayout = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        mainLayout.addWidget(top)

        def makelbl(s, y=15, align=QtCore.Qt.AlignRight):
            lbl = QtWidgets.QLabel(s)
            lbl.setFont(QtGui.QFont('Roboto', y))
            lbl.setAlignment(align)
            return lbl

        symbol = mpl.TexWidget(params.getTex(), 14) if params.tex else makelbl("")
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

        controls, controlLayout = Q.makeWidget(QtWidgets.QWidget, "horizontal", self)
        mainLayout.addWidget(controls)
        
        if params.isAdjustable:
            self.minEdit = self.getLineEdit(params.min)
            controlLayout.addWidget(self.minEdit, 1)
            self.minEdit.returnPressed.connect(self.minEntered)
        else:
            lbl = QtWidgets.QLabel(helpers.formatNumber(params.min))
            controlLayout.addWidget(lbl, 1)

        slider = self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, controls)
        slider.wheelEvent = lambda e: None
        controlLayout.addWidget(slider, 8)

        self.xMsg = Q.makeLabel("current x-axis", 22, Q.ALIGN_CENTER)
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
            lbl = QtWidgets.QLabel(helpers.formatNumber(params.max))
            controlLayout.addWidget(lbl, 1)

        slider.sliderMoved.connect(self.sliderMoved)

    def getLineEdit(self, value):
        edit = QtWidgets.QLineEdit(helpers.formatNumber(value))
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
        value = calc.clamp(value, minVal, maxVal)
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
                params.val = calc.clamp(params.val, params.min, params.max)
        except Exception:
            self.minEdit.setText(params.min)
            print("Failed to translate min value input %s" % proposal)

    def maxEntered(self):
        proposal = self.maxEdit.text()
        params, caster = self.paramsAndCaster()
        try:
            val = caster(proposal)
            if val > params.min:
                params.max = val
                params.val = calc.clamp(params.val, params.min, params.max)
        except Exception:
            self.maxEdit.setText(params.max)
            print("Failed to translate max value input %s" % proposal)

    def setMax(self, val):
        params, caster = self.paramsAndCaster()
        params.max = caster(val)
        self.maxEdit.setText(helpers.formatNumber(params.max))
        if params.val > params.max:
            self.setVal(params.max)

    def setMin(self, val):
        params, caster = self.paramsAndCaster()
        params.min = caster(val)
        self.maxEdit.setText(helpers.formatNumber(params.min))
        if params.val < params.min:
            self.setVal(params.min)

    def setVal(self, val, callItBack=True):
        params, caster = self.paramsAndCaster()
        params.val = calc.clamp(caster(val), params.min, params.max)
        self.valEdit.setText(helpers.formatNumber(params.val))
        self.slider.setValue(self.normalizeValue(params.val))
        if callItBack:
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
        self.mode = PARAM_REG

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

    def get(self):
        """
        Returns a dict of params and values
        """
        return {p.name: p.val for p in self.dcrParams.values()}

    def setMode(self, mode):
        for param in self.dcrParams.values():
            if param.type & mode:
                param.widget.setVisible(True)
            else:
                param.widget.setVisible(False)

    def addParameter(self, paramType, name, minVal, maxVal, val, isIntegral, displayName, callback=None, isAdjustable=True, tex=None, unit=None, description=None, **kwargs):
        if name not in self.paramBox:
            self.paramBox[name] = {}
        params = self.paramBox[name]
        self.keys.append(name)
        p = self.dcrParams[name] = DcrParameter(paramType, name, params, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs)
        if not paramType & self.mode:
            p.widget.setVisible(False)
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
    def __init__(self, paramType, name, params, minVal, maxVal, val, isIntegral, displayName, callback=None, isAdjustable=True, tex=None, unit=None, description=None, **kwargs):
        # params should maybe be called subparams or something here
        self.__dict__["params"] = params
        self.type = paramType # A bitmask used to quickly sort the parameter
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

    def __setitem__(self, key, val):
        self.params[key] = val

    def __getitem__(self, key):
        if key in self.params:
            return self.params[key]
        raise KeyError("%s not found in sub-parameters for DcrParameter %s" % (key, self.name))

    def __getattr__(self, key):
        if key in self.params:
            return self.params[key]
        if hasattr(self.widget, key):
            return getattr(self.widget, key)
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
        return mpl.wrapTex(self.tex)

    def enable(self):
        self.widget.slider.setVisible(True)
        self.widget.xMsg.setVisible(False)

    def xDisable(self):
        self.widget.slider.setVisible(False)
        self.widget.xMsg.setVisible(True)

    def axisLabel(self):
        lbl = self.displayName
        if self.tex:
            lbl += ", %s" % mpl.wrapTex(self.tex)
        if self.unit:
            lbl += " (%s)" % mpl.wrapText(self.unit)
        return lbl


class DcrAttackCapital(QtWidgets.QWidget):
    def __init__(self, explorer, mainWindow):
        super().__init__()
        self.explorer = explorer
        self.mainWindow = mainWindow
        self.settings = explorer.getSettings(self.__class__.__name__)
        self.windowSelector = explorer.mainWindow.windowSelector
        self.x1 = None
        self.reportFetch = explorer.makeThreadSafeVersion(self._reportFetch)
        self.chartMode = "cost"
        self.contourParams = ("ticketFraction", "powSplit")
        self.stackedParams = ("xcRate", "ticketFraction")

        self.windowWidget = QtWidgets.QSplitter()
        self.windowWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.resized = self.resizeSplitter
        self.splitterRatio = 0.7
        self.windowWidget.splitterMoved.connect(self.setSplitterRatio)
        self.windowWidget.addWidget(self)

        self.layout = QtWidgets.QVBoxLayout(self)

        rightWgt, rightColumn = Q.makeWidget(QtWidgets.QWidget, "vertical")
        Q.setBackgroundColor(rightWgt, "white")
        self.windowWidget.addWidget(rightWgt)

        modeWgt, mode = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        rightColumn.addWidget(modeWgt)
        modeWgt.setContentsMargins(5, 5, 5, 5)
        mode.addStretch(1)
        mode.addWidget(Q.makeLabel("Regular mode", 16))
        self.modeToggle = toggle = Q.QToggle(self, callback=self.modeToggled)
        toggle.onBrush = toggle.slotBrush
        mode.addWidget(toggle)
        mode.addWidget(Q.makeLabel("Reverse mode", 16))
        mode.addStretch(1)

        sa = self.controls = QtWidgets.QScrollArea()
        rightColumn.addWidget(sa, 1)
        controlRows, self.controlLayout = Q.makeWidget(QtWidgets.QWidget, "vertical")
        self.controlLayout.setSpacing(20)
        controlRows.setAutoFillBackground(True)
        controlRows.setPalette(Q.WHITE_PALETTE)
        # sa.setLineWidth(0)
        sa.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        sa.setAlignment(QtCore.Qt.AlignTop)
        sa.setWidgetResizable(True)
        sa.setWidget(controlRows)
        sa.setContentsMargins(0, 0, 0, 0)
        # self.widgetsColumn.setSpacing(5)
        # self.widgetsColumnScrollbar = sa.verticalScrollBar()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.updateGeometry()

        def verticalbar():
            wgt, lyt = Q.makeWidget(QtWidgets.QWidget, "horizontal")
            lyt.addStretch(1)
            line = QtWidgets.QFrame()
            Q.setBackgroundColor(line, "#555555")
            line.setFixedWidth(1)
            line.setContentsMargins(0, 20, 0, 20)
            line.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding)
            lyt.addWidget(line)
            lyt.addStretch(1)
            return wgt

        topWgt, topLyt = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        topLyt.setSpacing(5)
        self.layout.addWidget(topWgt, 0)
        Q.setBackgroundColor(topWgt, "white")

        _, self.switchableLyt = switchableWgt, switchable = Q.makeWidget(QtWidgets.QWidget, "vertical")
        topLyt.addWidget(switchableWgt, 1)
        topLyt.addWidget(verticalbar(), 0)

        wgt, topBar = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        switchable.addWidget(wgt)
        topBar.setContentsMargins(12, 6, 0, 6)

        # a box for the window selector
        winSelect, self.windowSelectorBox = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        winSelect.setContentsMargins(3, 3, 3, 3)
        topBar.addWidget(winSelect)

        # A selector for the switchable area
        switchableSelect = self.switchableSelect = QtWidgets.QComboBox()
        topBar.addWidget(switchableSelect)
        switchableSelect.setItemDelegate(QtWidgets.QStyledItemDelegate()) # this is needed for the qlistview items to obey stylesheet settings
        switchableSelect.setMaximumWidth(350)
        switchableSelect.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        switchableSelect.currentTextChanged.connect(self.activateSwitchable)

        # A widget to hold controls inline with selects
        wgt, self.optionsLyt = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        topBar.addWidget(wgt)

        self.switchables = {}
        self.currentSwitchable = None
        self.switchables["Equations"] = self.makeEquations()       
        self.switchables["Network state"] = self.makeNetworkState()
        switchableSelect.addItems(self.switchables.keys())
        self.activateSwitchable("Network state")

        bttnWgt, bttnLyt = Q.makeWidget(QtWidgets.QWidget, "vertical")
        topLyt.addWidget(bttnWgt)

        bttn = explorer.getButton("small", "attack cost")
        bttn.clicked.connect(lambda e: self.switchChart("cost"))
        bttnLyt.addWidget(bttn)

        bttn = explorer.getButton("small", "stacked")
        bttn.clicked.connect(lambda e: self.switchChart("stacked"))
        bttnLyt.addWidget(bttn)

        bttn = explorer.getButton("small", "contour")
        bttn.clicked.connect(lambda e: self.switchChart("contour"))
        bttnLyt.addWidget(bttn)

        topLyt.addWidget(verticalbar(), 0)

        # The selectors grid holds all plottable x-axis parameters as buttons to select.
        w, selectors = Q.makeWidget(QtWidgets.QWidget, "vertical")
        topLyt.addWidget(w, 0)
        w.setContentsMargins(5, 5, 5, 5)
        selectors.addWidget(Q.makeLabel("select x", 22))
        xGridWgt, self.xGrid = Q.makeWidget(QtWidgets.QWidget, "grid")
        selectors.addWidget(xGridWgt)
        self.xGridColumns = 5
        self.dragWgt = None

        # Simple value display
        self.attackCostDisplay = AttackCostDisplay(explorer, self)
        self.layout.addWidget(self.attackCostDisplay, 1)

        # Two plots, one 2d and one 3d
        self.tickFont = mpl.getFont("EBGaramond-Regular", 16)
        self.axisFont = mpl.getFont("EBGaramond-Regular", 20)
        self.titleFont = mpl.getFont("EBGaramond-Regular", 22)
        self.stackedFigure = mpl.Figure()
        self.stackedCanvas = mpl.FigureCanvas(self.stackedFigure)
        ax = self.stackedAxes = self.stackedFigure.add_subplot("111")
        self.stackedCanvas.setVisible(False)
        ax.set_ylabel(r"Attack Cost, $ A $ (billion USD)", fontproperties=self.axisFont)
        ax.set_xlabel(" ", fontproperties=self.axisFont)
        self.layout.addWidget(self.stackedCanvas, 1)

        self.contourFigure = mpl.Figure()
        self.contourCanvas = mpl.FigureCanvas(self.contourFigure)
        self.contourCanvas.setVisible(False)
        self.contourPlot = None
        self.contourAxes = self.contourFigure.add_subplot("111") #, projection="3d")
        self.layout.addWidget(self.contourCanvas, 1)

        self.normalizeSettings()
        self.fetch()

    def activate(self):
        self.windowSelectorBox.addWidget(self.windowSelector)

    def resizeSplitter(self, event):
        width = self.explorer.mainWindow.width()
        rightRatio = 1 - self.splitterRatio
        self.windowWidget.setSizes([width*self.splitterRatio, width*rightRatio])

    def setSplitterRatio(self, pos, idx):
        l, r = self.windowWidget.sizes()
        self.splitterRatio = l / (l + r)
        self.settings["slitter.ratio"] = self.splitterRatio
        self.explorer.saveLowPriority()

    def normalizeSettings(self):
        if "params" not in self.settings:
            self.settings["params"] = {}
        self.paramBox = self.settings["params"]
        callback = self.valChanged
        # addParameter: name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs
        self.params = ParameterManager(self.paramBox)

        # Both Modes
        # ticketFraction = None
        self.registerParam(PARAM_BOTH, "ticketFraction", 1e-9, 1., 1e-9, False,
            "ticket fraction", callback, True, r"y", None,
            "The fraction of the ticket pool under attacker control.")
        # xcRate = None
        self.registerParam(PARAM_BOTH, "xcRate", 10, 30, 20, False,
            "exchange rate", callback, True, r"X", "USD", 
            "Exhange rate.")        
        # blockHeight = None
        self.registerParam(PARAM_BOTH, "blockHeight", 0, 1e6, 3e5, True, 
            "block height", callback, True, r"t_a", "hours", 
            "The total time of the attack.")
        # blockTime = None
        self.registerParam(PARAM_BOTH, "blockTime", 0, 900, mainnet.TargetTimePerBlock, True, 
            "block time", callback, True, r"t_b", "seconds", 
            "The total time of the attack.")
        # # rentability = None 
        # self.registerParam(PARAM_BOTH, "rentability", 0., 2e6, 1000, False, 
        #     "rentability", callback, True, r"a", "terahash/s", 
        #     "Amount of hashing power available on the rental market")
        # rentalRatio = None
        self.registerParam(PARAM_BOTH, "rentalRatio", 0., 1., 0., False, 
            "rentability ratio", callback, True, r"a_r", None, 
            "Same as rentability, but as a portion of existing network hashpower.")
        # rentalRate = None
        self.registerParam(PARAM_BOTH, "rentalRate", NICEHASH_RATE*0.5, NICEHASH_RATE*1.5, NICEHASH_RATE, False, 
            "rental rate", callback, True, r"r_e", "USD/terahash", 
            "Rental rate.")
        # winners = None
        self.registerParam(PARAM_BOTH, "winners", 1, 10, 5, True, 
            "stake winners", callback, True,  r"N", "tickets", 
            "POS validators per block.")
        # participation = 1
        self.registerParam(PARAM_BOTH, "participation", 1e-9, 1., 1., False, 
            "participation (%)", callback, True, r"p", None, 
            "Participation level. Fraction of tickets which belong to an online stakeholder.")
        # poolSize = None
        self.registerParam(PARAM_BOTH, "poolSize", 1000, 100000, mainnet.TicketExpiry, True, 
            "ticket pool size", callback, True, r"Z", "tickets", 
            "Ticket pool size. A network parameter.")

        # Regular Mode
        # ticketPrice = None
        self.registerParam(PARAM_REG, "ticketPrice", 10, 10000, 2000, False, 
            "ticket price (DCR)", callback, True, r"p_t", "DCR", 
            "Ticket price (stake difficulty)")
        # nethash = None
        self.registerParam(PARAM_REG, "nethash", 5e16, 1e18, 2e17, True, 
            "network hashrate", callback, True, r"H_n", "hashes/second", 
            "Netowrk hashrate.")

        # Reverse Mode
        # roi = None
        self.registerParam(PARAM_REV, "roi", -0.01, 0.05, 0, False,
            "profitability", callback, True, r"\alpha_w", None,
            "POW profitability. Daily earnings as a fraction of device cost.")
        # apy = None
        self.registerParam(PARAM_REV, "apy", .05, .3, 0.15, False,
            "annual percentage yield (%)", callback, True, r"\alpha_s", None,
            "Stake profitability. Immediate reinvestment for 1 year.")
        # These last three will need special handling to ensure they sum to 1
        # powSplit = None
        self.registerParam(PARAM_REV, "powSplit", 1e-9, 0.9, mainnet.STAKE_SPLIT, False,
            "miner split", callback, True, r"s_w", None,
            "Portion of block reward paid to the miner")
        # stakeSplit = None
        self.registerParam(PARAM_REV, "stakeSplit", 1e-9, 0.9, mainnet.POW_SPLIT, False,
            "stake split", callback, True, r"s_s", None,
            "Portion of block reward paid to ticket holders")
        # treasurySplit = None
        self.registerParam(PARAM_REV, "treasurySplit", 1e-9, 0.9, mainnet.TREASURY_SPLIT, False,
            "treasury split", callback, True, r"s_s", None,
            "Portion of block reward paid to ticket holders")

    def makeNetworkState(self):
        # Current network state
        explorer = self.explorer
        opts, lyt = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        opts.setContentsMargins(5, 5, 5, 5)
        bttn = explorer.getButton("tiny", "fetch current state")
        bttn.clicked.connect(self.fetch)
        lyt.addWidget(bttn)
        bttn = explorer.getButton("tiny", "use all")
        bttn.clicked.connect(self.useFetch)
        lyt.addWidget(bttn)
        
        stateLabels = self.stateLabels = {}
        grid, defaults = Q.makeWidget(QtWidgets.QWidget, "grid")
        grid.setContentsMargins(5, 5, 5, 5)

        rowCount = 4
        column = 0
        counter = 0

        def addDefault(name, text, defaultVal=None):
            nonlocal counter
            nonlocal column
            if counter >= rowCount:
                counter = 0
                column += 2
            defaults.addWidget(Q.makeLabel(text, 15, Q.ALIGN_LEFT), counter, column)
            lbl = stateLabels[name] = Q.makeLabel(str(defaultVal) if defaultVal else "fetching...", 15, Q.ALIGN_LEFT)
            lbl.currentValue = defaultVal
            lbl.setMinimumWidth(75)
            defaults.addWidget(lbl, counter, column + 1)
            counter += 1
        addDefault("xcRate", "exchange rate (USD): ")
        addDefault("blockHeight", "block height: ")
        addDefault("treasurySplit", "treasury split: ", mainnet.TREASURY_SPLIT)
        addDefault("blockTime", "block time (seconds): ", mainnet.TargetTimePerBlock)

        addDefault("ticketPrice", "ticket price (USD): ")
        addDefault("apy", "Annual percentage yield ")
        addDefault("poolSize", "Tickets pool size ", mainnet.TicketExpiry)
        addDefault("stakeSplit", "Stake split ", mainnet.STAKE_SPLIT)

        addDefault("nethash", "Network hashrate ")
        addDefault("roi", "profitability: ")
        addDefault("winners", "Tickets per block: ", mainnet.TicketsPerBlock)        
        addDefault("powSplit", "Miner split ", mainnet.POW_SPLIT)
        return opts, grid

    def makeEquations(self):
        w, equations = Q.makeWidget(QtWidgets.QWidget, "vertical")
       
        self.equation = mpl.TexWidget(r"$A(y) = ar_et_a +\left( H_a - a \right) \left(\rho + \frac{ c t_a }{ \eta } \right) + yZp_t$")
        self.equation.setFixedHeight(65)
        equations.addWidget(self.equation, 1)

        self.subEquation = mpl.TexWidget(r"$ H_a = \frac{ 86400 s \sigma(y) R_{tot}(h) X }{ t_b (\alpha\rho + 0.24 c / \eta) } $")
        self.subEquation.setFixedHeight(65)
        equations.addWidget(self.subEquation, 1)

        return None, w

    def registerParam(self, paramType, name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs):
        p = self.params.addParameter(paramType, name, minVal, maxVal, val, isIntegral, displayName, callback, isAdjustable, tex, unit, description, **kwargs)
        self.controlLayout.addWidget(p.widget)
        texWgt = mpl.TexWidget(mpl.wrapTex(p.tex), 20)
        texWgt.setToolTip(p.tooltip)
        texWgt.setFixedSize(35, 35)
        texWgt.enterEvent = lambda e, w=texWgt: self.xGridEnter(w)
        texWgt.leaveEvent = lambda e, w=texWgt: self.xGridLeave(w)
        texWgt.mousePressEvent = lambda e, w=texWgt: self.xGridDown(w)
        texWgt.mouseReleaseEvent = lambda e, w=texWgt: self.xGridUp(e, w)
        texWgt.param = p
        xGrid = self.xGrid
        xCount = xGrid.count()
        cols = self.xGridColumns
        xGrid.addWidget(texWgt, int(xCount/cols), xCount % cols)

    def modeToggled(self, state, toggle):
        if state:
            self.params.setMode(PARAM_REV)
        else:
            self.params.setMode(PARAM_REG)

    def xGridEnter(self, widget):
        widget.setFacecolor("#ccffdd")

    def xGridLeave(self, widget):
        widget.setFacecolor()

    def xGridDown(self, widget):
        self.gridWgt = widget

    def xGridUp(self, e, widget):
        if widget == self.gridWgt:
            if e.button() == QtCore.Qt.LeftButton:
                if widget.param != self.x2:
                    self.x1 = widget.param
            if e.button() == QtCore.Qt.RightButton:
                if widget.param != self.x1:
                    self.x2 = widget.param
            self.reButton()

    def setXAxes(self, x1Name, x2Name):
        for w in Q.layoutWidgets(self.xGrid):
            if w.param.name == x1Name:
                self.x1 = w.param
            elif w.param.name == x2Name:
                self.x2 = w.param
        self.reButton()

    def reButton(self):
        for w in Q.layoutWidgets(self.xGrid):
            if w.param == self.x1:
                w.defaultColor = "#ccddff"
                w.setFacecolor()
            elif w.param == self.x2:
                w.defaultColor = "#ccffdd"
                w.setFacecolor()
            else:
                w.defaultColor = "white"
                w.setFacecolor()
        self.calc({})

    def activateSwitchable(self, key):
        if self.currentSwitchable == key:
            return
        self.currentSwitchable = key
        opts, wgt = self.switchables[key]
        lytItem = self.switchableLyt.itemAt(1)
        if lytItem:
            lytItem.widget().setParent(None)
        Q.clearLayout(self.optionsLyt)
        if opts:
            self.optionsLyt.addWidget(opts)
        self.switchableLyt.addWidget(wgt)
        if self.switchableSelect.currentText() != key:
            self.switchableSelect.setCurrentText(key)

    def writeEquation(self):
        # H_a = \frac{ 86400 s \sigma(y) R_{tot}(h) X }{ t_b (\alpha\rho + 0.24 c / \eta) }
        return

    def valChanged(self, key, val):
        print("%s val changed to %r" % (key, val))
        if key == "treasurySplit":
            powSplit = self.params.powSplit.val
            stakeSplit = self.params.stakeSplit.val
            remainder = 1 - val
            adjustment = (remainder - powSplit - stakeSplit) / 2
            self.params.powSplit.setMax(remainder)
            self.params.stakeSplit.setMax(remainder)
            self.params.powSplit.setVal(powSplit + adjustment, False)
            self.params.stakeSplit.setVal(stakeSplit + adjustment, False)
        elif key == "powSplit":
            self.params.stakeSplit.setVal(1 - self.params.treasurySplit.val - self.params.powSplit.val, False)
        elif key == "stakeSplit":
            self.params.powSplit.setVal(1 - self.params.treasurySplit.val - self.params.stakeSplit.val, False)
        self.calc({})

    def switchChart(self, key):
        if self.chartMode == key:
            return
        self.chartMode = key
        if key == "cost":
            self.attackCostDisplay.setVisible(True)
            self.stackedCanvas.setVisible(False)
            self.contourCanvas.setVisible(False)
            self.setXAxes(None, None)
        if key == "stacked":
            self.attackCostDisplay.setVisible(False)
            self.stackedCanvas.setVisible(True)
            self.contourCanvas.setVisible(False)
            self.setXAxes(*self.stackedParams)
        if key == "contour":
            self.attackCostDisplay.setVisible(False)
            self.stackedCanvas.setVisible(False)
            self.contourCanvas.setVisible(True)
            self.setXAxes(*self.contourParams)

    def fetch(self):
        self.explorer.makeThread(self.actuallyFetch)

    def actuallyFetch(self):
        xcRate = fetchCMCPrice()
        self.reportFetch("xcRate", xcRate, helpers.formatNumber(xcRate, isMoney=True))
        bestBlock = dataClient.block.best()
        hBest = bestBlock["height"]
        self.reportFetch("blockHeight", hBest, str(hBest))
        self.reportFetch("ticketPrice", bestBlock["ticket_pool"]["valavg"]) 
        self.reportFetch("nethash", getDcrDataHashrate())
        self.reportFetch("roi", getDcrDataProfitability(xcRate))
        self.reportFetch("apy", getDcrDataAPY())

    def _reportFetch(self, k, v, text=None):
        if k not in self.stateLabels or k not in self.params:
            return
        lbl = self.stateLabels[k]
        lbl.currentValue = v
        lbl.setText(text if text else helpers.formatNumber(v))

    def useFetch(self):
        for k, lbl in self.stateLabels.items():
            if not lbl.currentValue:
                continue
            self.params[k].setVal(lbl.currentValue)

    def calc(self, overrides):
        '''
        overrides will be used in place of native parameters
        '''
        params = helpers.recursiveUpdate(self.params.get(), overrides)
        if self.modeToggle.switch:
            params.pop("nethash")
            params.pop("ticketPrice")
        mode = self.chartMode
        if mode == "cost":
            self.attackCostDisplay.setA(params)
        elif mode == "stacked":
            self.plotStacked(params)
        elif mode == "contour":
            self.plotContour(params)

    def plotStacked(self, params):
        self.explorer.scheduleFunction("plotStacked", self.actuallyPlotStacked, time.time() + 1, params)

    def actuallyPlotStacked(self, params):
        x1 = self.x1
        x1Name = x1.name
        x2 = self.x2
        x2Name = x2.name

        self.params.enableAll()
        x1.xDisable()
        x2.xDisable()
        if x1.isIntegral:
            X1 = np.linspace(int(x1.min), int(x1.max), 100)
        else:
            X1 = np.linspace(x1.min, x1.max, 100)

        if x2.isIntegral:
            xRange = x2.max - x2.min
            jump = xRange/4
            X2 = []
            for i in range(5):
                X2.append(int(round(x2.min+jump*i)))
        else:
            X2 = np.linspace(x2.min, x2.max, 5)

        ax = self.stackedAxes
        while ax.lines:
            ax.lines.pop(0)

        minY = C.INF
        maxY = -C.INF
        for x_2 in X2:
            x = []
            y = []
            params[x2Name] = x_2
            for x_1 in X1:
                x.append(x_1)
                params[x1Name] = x_1
                A = calc.attackCost(**params).attackCost
                y.append(A)
                if A > maxY:
                    maxY = A
                if A < minY:
                    minY = A
            ax.plot(x, y)

        ax.set_xlim(left=min(X1), right=max(X1))
        ax.set_ylim(bottom=minY, top=maxY)
        self.stackedFigure.canvas.draw()

    def plotContour(self, params):
        self.explorer.scheduleFunction("plotContour", self.actuallyPlotContour, time.time() + 1, params)

    def actuallyPlotContour(self, params):
        x1 = self.x1
        x1Name = x1.name
        x2 = self.x2
        x2Name = x2.name

        self.params.enableAll()
        x1.xDisable()
        x2.xDisable()
        if x1.isIntegral:
            X1 = np.linspace(int(x1.min), int(x1.max), 100)
        else:
            X1 = np.linspace(x1.min, x1.max, 100)

        if x2.isIntegral:
            xRange = x2.max - x2.min
            jump = xRange/4
            X2 = []
            for i in range(5):
                X2.append(int(round(x2.min+jump*i)))
        else:
            X2 = np.linspace(x2.min, x2.max, 5)

        ax = self.contourAxes
        if self.contourPlot:
            for coll in self.contourPlot.collections:
                ax.collections.remove(coll)

        minX1 = X1[0]
        maxX1 = X1[-1]
        minX2 = X2[0]
        maxX2 = X2[-1]
        X1, X2 = np.meshgrid(X1, X2)

        ogX1 = params[x1Name]
        ogX2 = params[x2Name]        

        def processor(x1, x2):
            params[x1Name] = x1
            params[x2Name] = x2
            return calc.attackCost(**params).attackCost

        Z = np.array([processor(x1, x2) for x1, x2 in zip(np.ravel(X1), np.ravel(X2))]).reshape(X1.shape)
        ax.set_xlim(left=minX1, right=maxX1)
        ax.set_ylim(bottom=minX2, top=maxX2)
        ax.set_xlabel(self.params[x1Name].axisLabel())
        ax.set_ylabel(self.params[x2Name].axisLabel())
        self.contourPlot = ax.contourf(X1, X2, Z, levels=20, cmap='plasma_r')
        self.contourFigure.canvas.draw()


class AttackCostDisplay(QtWidgets.QWidget):
    """
    Values and charts for the attack cost at the current parameters.
    """
    def __init__(self, explorer, parent):
        super().__init__()
        self.explorer = explorer
        self.parent = parent
        # Simple value display
        lyt = self.layout = QtWidgets.QVBoxLayout(self)        
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        lyt.addStretch(1)

        wgt, row = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        lyt.addWidget(wgt)
        row.addStretch(1)

        def makeTerm(txt, v):
            wgt, lyt = Q.makeWidget(QtWidgets.QWidget, "vertical")
            wgt.setContentsMargins(10, 0, 10, 0)
            lyt.addWidget(Q.makeLabel(txt, 25), 0)
            val = Q.makeLabel(v, 55)
            lyt.addWidget(val, 0)
            return wgt, val

        termWgt, self.attackCostLabel = makeTerm("Cost of Attack", "...")
        row.addWidget(termWgt)

        termWgt, _ =  makeTerm(" ", "=")
        row.addWidget(termWgt)

        termWgt, self.workTermLabel = makeTerm("Work Term", "...")
        row.addWidget(termWgt)

        termWgt, _ =  makeTerm(" ", "+")
        row.addWidget(termWgt)

        termWgt, self.stakeTermLabel = makeTerm("Stake Term", "...")
        row.addWidget(termWgt)

        row.addStretch(1)

        wgt, row = Q.makeWidget(QtWidgets.QWidget, "horizontal")
        lyt.addWidget(wgt)
        row.addStretch(1)
        
        self.tickFont = mpl.getFont("EBGaramond-Regular", 16)
        self.axisFont = mpl.getFont("EBGaramond-Regular", 20)
        self.titleFont = mpl.getFont("EBGaramond-Regular", 22)
        self.fig = mpl.Figure()
        self.canvas = mpl.FigureCanvas(self.fig)
        self.canvas.setFixedSize(750, 500)
        self.scatter = None
        ax = self.ax = self.fig.add_subplot("111")
        ax.set_ylabel(r"attack cost (million USD)", fontproperties=self.axisFont)
        ax.set_xlabel(r"ticket fraction, $ y $", fontproperties=self.axisFont)
        ax.set_xlim(left=0., right=1.)
        row.addWidget(self.canvas, 1)

        row.addStretch(1)

        lyt.addStretch(1)

    def setA(self, params):
        Ay = calc.attackCost(**params)
        ogY = params["ticketFraction"]
        self.attackCostLabel.setText("$%s" % helpers.formatNumber(Ay.attackCost, isMoney=True))
        self.workTermLabel.setText("$%s" % helpers.formatNumber(Ay.workTerm, isMoney=True))
        self.stakeTermLabel.setText("$%s" % helpers.formatNumber(Ay.stakeTerm, isMoney=True))
        X = np.linspace(1e-9, 1., 100)
        stake = []
        work = []
        attackCost = []
        maxVal = 0
        closest = C.INF
        bestSpots = None
        for y in X:
            params["ticketFraction"] = y
            A = calc.attackCost(**params)
            stake.append(A.stakeTerm/1e6)
            work.append(A.workTerm/1e6)
            attackCost.append(A.attackCost/1e6)
            maxVal = max(A.attackCost, maxVal)
            gap = abs(y - ogY)
            if gap < closest:
                closest = gap
                bestSpots = (y, A.stakeTerm, A.workTerm, A.attackCost)

        self.ax.set_ylim(bottom=0., top=maxVal/1e6*1.05)
        lines = self.ax.get_lines()
        bestY, bestS, bestW, bestA = bestSpots
        bestS, bestW, bestA = bestS/1e6, bestW/1e6, bestA/1e6
        if lines:
            lines[0].set_data(X, stake)
            lines[1].set_data(X, work)
            lines[2].set_data(X, attackCost)
            lines[3].set_data((bestY, bestY), (-1, maxVal/1e6*1.1))
            lines[4].set_data((0, bestY), (bestS, bestS))
            lines[5].set_data((0, bestY), (bestW, bestW))
            lines[6].set_data((0, bestY), (bestA, bestA))
        else:
            self.ax.plot(X, stake, linestyle=":", color="#00AA00", linewidth=2, label="stake")
            self.ax.plot(X, work, linestyle="--", color="#0000FF", linewidth=2, label="work")
            self.ax.plot(X, attackCost, linestyle="-", color="#333333", linewidth=2, label="attack")
            self.ax.plot((bestY, bestY), (-1, maxVal/1e5*1.1), linestyle="-", color="#00000033")
            self.ax.plot((0, bestY), (bestS, bestS), linestyle="-", color="#00AA0088", linewidth=1)
            self.ax.plot((0, bestY), (bestW, bestW), linestyle="-", color="#0000FF88", linewidth=1)
            self.ax.plot((0, bestY), (bestA, bestA), linestyle="-", color="#00000088", linewidth=1)
            self.ax.legend()
        if self.scatter:
            self.scatter.remove()
        self.scatter = self.ax.scatter((bestY, bestY, bestY, 0, 0, 0), (bestS, bestW, bestA, bestS, bestW, bestA), 20, "#000000")
        self.fig.canvas.draw()


class DcrLoadingAnimation(QtWidgets.QGraphicsItem):
    """ A loading animation that covers a widget. """
    def __init__(self, *args, **kwargs):
        super(Q.QStrataGraphicsItem, self).__init__(*args, **kwargs)

    def boundingRect(self):
        """
        Any class that inherits QGraphicsItem must override this method.
        It should probably be a little smarter
        """
        return QtCore.QRectF(-10000, -10000, 20000, 20000)


def loadFonts():
        # see https://github.com/google/material-design-icons/blob/master/iconfont/codepoints
        # for conversions to unicode
        # http://zavoloklom.github.io/material-design-iconic-font/cheatsheet.html
        fontDir = os.path.join(C.PACKAGEDIR, "fonts")
        for filename in os.listdir(fontDir):
            if filename.endswith(".ttf"):
                QtGui.QFontDatabase.addApplicationFont(os.path.join(fontDir, filename))


def runDecredExplorer():
    QtWidgets.QApplication.setDesktopSettingsAware(False)
    QtWidgets.QApplication.setFont(QtGui.QFont("Roboto"));
    app = QtWidgets.QApplication(sys.argv)
    loadFonts()

    explorer = DecredExplorer(app)

    icon = QtGui.QIcon(os.path.join(C.PACKAGEDIR, "logo.svg"))
    app.setWindowIcon(icon)
    app.setStyleSheet(Q.QUTILITY_STYLE)
    explorer.mainWindow.setWindowIcon(icon)
    try:
        app.exec_()
    except Exception as e:
        try:
            logger.warning("Error encountered: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
        except Exception:
            pass
        finally:
            print("Error encountered: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
    app.deleteLater()
    return


if __name__ == '__main__':
    runDecredExplorer()
