from pydecred import mainnet, helpers, calc
from pydecred import constants as C
import pydecred.mplstuff as mpl
from pydecred.cmcapi import CMCClient
from pydecred.dcrdata import DcrDataClient, PostgreArchivist
import os
import json
import time

import matplotlib.pyplot as plt
import numpy as np
import csv

APPDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
# NiceHash price for Decred 0.0751/PH/day
NICEHASH_RATE = 0.0751/1e12
helpers.mkdir(APPDIR)
archivist = PostgreArchivist("dcrdata", "localhost", "dcrdatauser", "dcrpass8675309")
DCRDATA_URI = "http://localhost:7777/"
dataClient = DcrDataClient(DCRDATA_URI)

cmcDir = os.path.join(APPDIR, "cmc")
helpers.mkdir(cmcDir)
cmcClient = CMCClient(cmcDir)

# A range of devices for mining Black256R14
DeviceRanges = {
    "asic": {
        "high": {
            "model": "INNOSILICON D9 Miner",
            "price": 1699,
            "release":  "2018-04-18",
            "hashrate": 2.1e12,
            "power": 900,
        },
        "low": {
            "model": "Baikal Giant B",
            "price": 399,
            "release": "2018-01-31",
            "hashrate": 160e9,
            "power": 410,
        }
    },
    "gpu": {
        "low": {
            "model": "RX 480",
            "price": 200,
            "release": "2016-06-01",
            "source": "https://forum.ethereum.org/discussion/11761/31-1mh-eth-575mh-dcr-dual-on-msi-rx-480-8gb",
            "hashrate": 575e6,
            "power": 140,
        },
        "high": {
            "model": "GeForce GTX 1080 Ti",
            "price": 475,
            "release": "2017-03-10",
            "source": "https://www.easypc.io/crypto-mining/decred-hardware/",
            "hashrate": 3.8e9,
            "power": 216,
        }
    }
}

# State-of-the-art devices for a range of algorithms.
DeviceParams = {
    "Blake256r14": helpers.recursiveUpdate({"example": "DCR"}, C.MODEL_DEVICE),
    "Equihash <200,9>": {
        "model": "Bitmain Z9",
        "hashrate": 41e3,
        "power": 1150,
        "price": 3300
    },
    # "Equihash <144, 5>": {
    #   "model": "GeForce 1080 Ti",
    #   "example": "BTG",
    #   "hashrate": 56,
    #   "power": 275,
    #   "price": 475
    # },
    "Ethash": {
        "model": "Antminer E3",
        "example": "ETH",
        "hashrate": 190e6,
        "power": 760,
        "price": 1150
    },
    "ProgPOW": {
        "model": "NVIDIA GeForce 1080 Ti",
        "example": "ZCash",
        "hashrate": 22e6,
        "power": 275,
        "price": 475
    },
    "Cryptonight V8": {
        "model": "NVIDIA GeForce 1080 Ti",
        "example": "XMR",
        "hashrate": 950,
        "power": 180,
        "price": 475
    },
    "Sha256": {
        "model": "Antminer S15",
        "example": "BTC",
        "hashrate": 28e12,
        "power": 1596,
        "price": 1475
    }
}
[helpers.makeDevice(d) for d in DeviceParams.values()]


archivist = None


def getPGArchivist():
    global archivist
    if not archivist:
        archivist = PostgreArchivist("dcrdata", "localhost", "dcrdatauser", "dcrpass8675309")


def getDbHeight():
    """
    Grab the best block height from a DCRData DB.
    """
    return archivist.getQueryResults("SELECT height FROM blocks ORDER BY height DESC LIMIT 1")[0][0]


def getDcrDataHashrate(height=None):
    """
    Get the network hashrate average for the last day-ish.
    """
    height = height if height else int(dataClient.block.best.height())
    block = dataClient.block.verbose(height)
    oldBlock = dataClient.block.verbose(int(height - C.DAY/mainnet.TargetTimePerBlock))
    return (int(block["chainwork"], 16) - int(oldBlock["chainwork"], 16))/(block["time"] - oldBlock["time"])


def getDcrDataProfitability(xcRate, height=None):
    """
    Get current mining profitability from DCRData.
    """
    device = C.MODEL_DEVICE
    height = height if height else int(dataClient.block.best.height())
    nethash = getDcrDataHashrate(height)
    gross = device["hashrate"]/nethash*calc.dailyPowRewards(height)*xcRate
    power = device["power"]*24/1000*C.PRIME_POWER_RATE
    return (device["hashrate"]/nethash*calc.dailyPowRewards(height)*xcRate - device["power"]*24/1000*C.PRIME_POWER_RATE)/device["price"]


def getDcrDataAPY():
    """
    Get current stake profitability from DCRData.
    """
    block = dataClient.block.best.verbose()
    juice = principal = 0
    for txid in block["stx"]:
        vin = dataClient.tx(txid)["vin"]
        if "stakebase" in vin[0]:
            juice += vin[0]["amountin"]
            principal += vin[1]["amountin"]
    power = 365/28
    return (juice/principal + 1)**power - 1


def getDevices():
    """
    A generator for the devices list.
    """
    for dType in DeviceRanges:
        for level in DeviceRanges[dType]:
            dvc = DeviceRanges[dType][level]
            dvc["level"] = level
            dvc["type"] = dType
            yield dvc


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


def avgPrice(pt):
    """
    Averages the four candlestick values.
    """
    return (pt["open"] + pt["close"] + pt["high"] + pt["low"])/4


def getCurrentParameters(asObject=False):
    """
    Returns a map of commonly used network figures.
    """
    params = {}
    params["xcRate"] = fetchCMCPrice()
    params["blockHeight"] = int(dataClient.block.best.height())
    params["roi"] = getDcrDataProfitability(params["xcRate"])
    params["apy"] = getDcrDataAPY()
    if asObject:
        return helpers.Generic_class(params)
    return params


def fetchCoinbase(process=True):
    """
    Fetches the actual coinbase transactions for all blocks except 1 and 2.
    For network averaging. Stores results to intermediate file for use by
    other plotting functions.
    """
    dcrFactor = 1e-8
    query = "SELECT block_height, block_time, spent FROM transactions WHERE tx_type=0 AND block_index=0 AND is_mainchain=TRUE ORDER BY block_height LIMIT 10000 offset %i;"
    blocks = []
    offset = 2  # skip the genesis and next block. Non-standard coinbase txs.
    while True:
        print("Processing blocks %i to %i" % (offset, offset + 9999))
        newRows = list(archivist.getQueryResults(query % offset))
        if len(newRows) == 0:
            break
        for i, newRow in enumerate(newRows):
            newRow = list(newRow)
            newRows[i] = newRow
            newRow[1] = helpers.dt2stamp(newRow[1])
            newRow[2] = newRow[2]*dcrFactor
        blocks.extend(newRows)
        offset += 10000
    filepath = os.path.join(APPDIR, "coinbase.json")
    with open(filepath, "w") as f:
        f.write(json.dumps(blocks))
    if process:
        processDailyOut(blocks)


def processDailyOut(blocks=None):
    """
    Process coinbase file from fetchCoinbase into daily
    totals.
    """
    if not blocks:
        filepath = os.path.join(APPDIR, "coinbase.json")
        with open(filepath, "r") as f:
            blocks = json.loads(f.read())
    # height, time, value
    firstDayStamp = helpers.stamp2dayStamp(blocks[0][1])
    nextDayStamp = firstDayStamp + C.DAY
    dayOut = 0
    days = []
    for height, stamp, out in blocks:
        if stamp >= nextDayStamp:
            days.append((helpers.stamp2dayStamp(stamp-C.DAY), dayOut))
            nextDayStamp = nextDayStamp + C.DAY
            dayOut = 0
        dayOut += out
    filepath = os.path.join(APPDIR, "daily-out.json")
    with open(filepath, "w") as f:
        f.write(json.dumps(days))


def getDailyOut():
    """
    Load the results from processDailyOut.
    """
    filepath = os.path.join(APPDIR, "daily-out.json")
    with open(filepath, "r") as f:
        return json.loads(f.read())


def storeDailyChainwork():
    """
    Calculate the work done every day. Saves to file.
    """
    query = "SELECT height, time, chainwork FROM blocks WHERE is_mainchain=TRUE ORDER BY height"
    chainworks = []
    print("Querying chainwork")
    rows = archivist.getQueryResults(query)
    firstRow = rows[0]
    firstDayStamp = helpers.stamp2dayStamp(helpers.dt2stamp(firstRow[1]))
    nextDayStamp = firstDayStamp + C.DAY
    lastDayBlock = False
    lastBlock = False
    print("Sorting chainwork")
    for height, stamp, chainwork in rows:
        stamp = helpers.dt2stamp(stamp)
        chainwork = int(chainwork, 16)
        if stamp < nextDayStamp:
            lastBlock = (stamp, height, chainwork)
            continue
        lastStamp, lastHeight, lastWork = lastBlock
        if lastDayBlock:
            lastDayStamp, lastDayHeight, lastDayWork = lastDayBlock
            work = (lastWork - lastDayWork)*C.DAY/(lastStamp - lastDayStamp)
            chainworks.append((helpers.stamp2dayStamp(stamp), (lastHeight + lastDayHeight) / 2,  work))
        nextDayStamp = nextDayStamp + C.DAY
        lastDayBlock = (stamp, height, chainwork)
    filepath = os.path.join(APPDIR, "daily-chainwork.json")
    with open(filepath, "w") as f:
        f.write(json.dumps(chainworks))


def getChainwork():
    """
    Loads the file from storeDailyChainwork.
    """
    filepath = os.path.join(APPDIR, "daily-chainwork.json")
    with open(filepath, "r") as f:
        return json.loads(f.read())


def compileDailyStats():
    """
    Daily tuples of (total work, miner rewards, exchange rate).
    This is everything needed to calculate profitability.
    """
    chainworks = getChainwork()
    tChain = chainworks[0][0]
    # available keys "date.string","open","high","low","close","volume","market.cap"
    cmcDaily = cmcClient.loadHistory(C.CMC_TOKEN, keys=["open", "close", "volume", "market.cap"])
    tCmc = cmcDaily[0][0]
    dailyOut = getDailyOut()
    tOut = dailyOut[0][0]
    tMin = max(tChain, tCmc, tOut)
    for rows in (chainworks, cmcDaily, dailyOut):
        while True:
            if rows[0][0] < tMin:
                rows.pop(0)
            else:
                break
    shortest = min(len(chainworks), len(cmcDaily), len(dailyOut))
    days = []
    for idx in range(shortest):
        stamp, openv, closev, volume, cap = cmcDaily.pop(0)
        chainwork = chainworks.pop(0)[2]
        out = dailyOut.pop(0)[1]
        price = (openv + closev) / 2
        days.append((stamp, chainwork, out, price))
    return days


def plotDevices(processor):
    """
    Plots data for the DeviceRanges. The values plotted depend on the processor
    argument. See `profitProcessor` and `RetailCapitalProcessor`.
    """
    for dvc in getDevices():
        helpers.makeDevice(dvc)
        dvc["x"] = []
        dvc["y"] = []
    fig = plt.gcf()
    plt.subplots_adjust(0.25, 0.1, 0.9, 0.9, 0, 0.1)
    stats = compileDailyStats()
    for dvc in getDevices():
        for stat in stats:
            coords = processor(dvc, stat)
            if not coords:
                continue
            x, y = coords
            dvc["x"].append(x)
            dvc["y"].append(y)
    gpu = DeviceRanges["gpu"]
    asic = DeviceRanges["asic"]
    priceAx = fig.add_subplot("311")
    gpuAx = fig.add_subplot("312", sharex=priceAx)
    asicAx = fig.add_subplot("313", sharex=priceAx)
    for ax in (priceAx, gpuAx, asicAx):
        for spine in ax.spines.values():
            spine.set_color(mpl.MPL_COLOR)
    plotParams = {
        "gpu": {
            "yticks": [0, 0.005, 0.01],
            "yticklabels": ["0", "0.5", "1"],
            "ylim": {
                "bottom": -0.002, 
                "top": 0.022
            },
            "fillcolor": "#1d33af30",
            "ax": gpuAx,
            "min.alpha": min(gpu["low"]["min.profitability"], gpu["high"]["min.profitability"]),
            "low": {
                "linecolor": "#1d33af",
            },
            "high": {
                "linecolor": "#1d33af"
            }
        },
        "asic" : {
            "yticks": [0, 0.003, 0.006],
            "yticklabels": ["0", "0.3", "0.6"],
            # "yticks" : [0, 0.05, 0.1],
            # "yticklabels": ["0", "5", "10"],
            "ylim": {
                "bottom": -0.01, 
                "top": 0.12
            },
            "fillcolor": "#84166c30",
            "ax": asicAx,
            "min.alpha": min(asic["low"]["min.profitability"], asic["high"]["min.profitability"]),
            "low": {
                "linecolor": "#84166c"
            },
            "high": {
                "linecolor": "#84166c"
            }
        }
    }
    fullMin = None
    fullMax = None
    axisFontSize = 11
    for dType in ["gpu", "asic"]:
        dvcs = DeviceRanges[dType]
        plotDevice = plotParams[dType]
        lines = []
        ax = plotDevice["ax"]
        for level, dvc in dvcs.items():
            seriesStyle = plotDevice[level]
            lines.append(list(zip(dvc["x"], dvc["y"])))
            ax.plot(dvc["x"], dvc["y"], color=seriesStyle["linecolor"], linewidth=1, zorder=10)
        l1, l2 = lines
        tMins = [min(l1, key=lambda pt: pt[0])[0], min(l2, key=lambda pt: pt[0])[0]]
        shareMin = max(tMins)
        tMin = min(tMins)
        fullMin = min(tMin, fullMin) if fullMin else tMin
        tMaxes = [max(l1, key=lambda pt: pt[0])[0], max(l2, key=lambda pt: pt[0])[0]]
        shareMax = min(tMaxes)
        tMax = min(tMaxes)
        fullMax = max(tMax, fullMax) if fullMax else tMax
        X = [t for t, y in l1 if shareMin <= t <= shareMax]
        Y1 = [y for t, y in l1 if shareMin <= t <= shareMax]
        Y2 = [y for t, y in l2 if shareMin <= t <= shareMax]
        ax.fill_between(X, Y1, Y2, color=plotDevice["fillcolor"], zorder=10)
        ax.set_ylim(**plotDevice["ylim"])
        ax.set_yticks(plotDevice["yticks"])
        ax.set_yticklabels(plotDevice["yticklabels"], fontproperties=mpl.getFont("Roboto-Regular", axisFontSize))
        aMin = plotDevice["min.alpha"]

    priceAx.set_xlim(left=fullMin, right=fullMax)
    for plotDevice in plotParams.values():
        ax = plotDevice["ax"]
        ax.set_xlim(left=fullMin, right=fullMax)
        aMin = plotDevice["min.alpha"]
        ax.plot([fullMin-1e6, fullMax+1e6], [aMin, aMin], color="#999999", linestyle="--", zorder=1)
        ax.plot([fullMin-1e6, fullMax+1e6], [0, 0], color="#333333", zorder=1)

    # Set axis labels on the asic plot
    ax = plotParams["asic"]["ax"]
    ax.set_xlim(left=fullMin, right=fullMax)
    xLabels = []
    xTicks = []
    y, m, d = helpers.yearmonthday(fullMin)
    tick = helpers.mktime(y,m)
    increment = 2
    # increment = 4
    end = fullMax + C.DAY*120
    while True:
        xTicks.append(tick)
        xLabels.append(time.strftime("%b-%y", time.gmtime(tick)))
        m += increment
        if m > 12:
            m -= 12
            y += 1
        tick = helpers.mktime(y, m)
        if tick > end:
            break
    ax.set_xticks(xTicks)
    ax.set_xticklabels(xLabels, fontproperties=mpl.getFont("Roboto-Regular", axisFontSize))

    for ax in (gpuAx, priceAx):
        [label.set_visible(False) for label in ax.get_xticklabels()]
    prices = [(pt["timestamp"], avgPrice(pt)) for pt in cmcClient.loadHistory(C.CMC_TOKEN) if fullMin <= pt["timestamp"] <= fullMax]
    x, y = zip(*prices)
    priceAx.plot(x, y, color="black")
    plt.show()


def profitProcessor(dvc, stat):
    """
    A processor for `plotDevices`. Returns mining profitability stats.
    """
    stamp, chainwork, out, price = stat
    if stamp < dvc["release"]:
        return False
    nethash = chainwork / C.DAY
    xy = stamp, (out*price*dvc["hashrate"]/nethash - dvc["daily.power.cost"])/dvc["price"]
    # if dvc["type"] == "asic" and dvc["level"] == "high":
    #   print(repr(nethash/1e15))
    #   print(repr(helpers.yearmonthday(stamp)))
    return xy


def retailCapitalProcessor(dvc, stat):
    """
    A processor for `plotDevices`. Returns retail capital of devices on network.
    """
    stamp, chainwork, out, price = stat
    if stamp < dvc["release"]:
        return False
    return stamp, chainwork/C.DAY/dvc["hashrate"]*dvc["price"]


def plotSigma(Ns=None):
    """
    Sigma vx. y (work fraction vs. ticket fraction)
    """
    Ns = Ns if Ns else [mainnet.TicketsPerBlock]
    plt.subplots_adjust(0.25, 0.25, 0.90, 0.85, 0, 0.1)
    fig = plt.gcf()
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_color(mpl.MPL_COLOR)
    X = np.arange(0.01, 1.000, 0.01)
    ticks = [0, 0.5, 1]
    labels = ["0", "0.5", "1"]
    ax.set_yticks(ticks)
    ax.set_xticks(ticks)
    ax.set_yticklabels(labels, fontproperties=mpl.getFont("Roboto-Regular", 12))
    ax.set_xticklabels(labels, fontproperties=mpl.getFont("Roboto-Regular", 12))
    linestyles = ["--", ":", "-."]
    lsIdx = 0
    for N in Ns:
        if N == mainnet.TicketsPerBlock:
            linestyle = "-"
            linecolor = "#333333"
        else:
            linestyle = linestyles[lsIdx%len(linestyles)]
            lsIdx += 1
            linecolor = "#999999"
        Y = [calc.hashportion(x, winners=N) for x in X]
        plt.plot(X, Y, color=linecolor, linestyle=linestyle)
    plt.show()


def plotPrices():
    """
    Plot stake diff and exchange rate.
    Update CMC history file with fetchCMCHistory() first.
    """
    xcRates = [(pt["timestamp"], avgPrice(pt)) for pt in cmcClient.loadHistory(C.CMC_TOKEN)]
    tMin = min(xcRates, key=lambda pt: pt[0])[0]
    tMax = max(xcRates, key=lambda pt: pt[0])[0]
    dataClient = DcrDataClient(DCRDATA_URI)
    ts = dataClient.chart("ticket-price")
    ticketStamps = [dataClient.timeStringToUnix(t) for t in ts["time"]]
    pricesDCR = ts["valuef"]
    filtered = [(t, v*calc.interpolate(xcRates, t)) for t, v in zip(ticketStamps, pricesDCR) if tMin < t < tMax]
    filteredStamps, pricesFiat = zip(*filtered)

    fig = plt.gcf()
    ax = plt.gca()
    ax.plot(filteredStamps, pricesFiat)

    priceAx = ax.twinx()
    x, y = zip(*xcRates)
    priceAx.plot(x, y)

    plt.show()


def calculateTicketReturns():
    """
    Historical ticket return rate.
    """
    query = "SELECT height, ticket_price, vote_reward FROM votes ORDER BY height LIMIT 10000 offset %i;"
    height = archivist.getQueryResults("SELECT height FROM blocks ORDER BY height DESC LIMIT 1")[0][0]
    setSize = 10000

    def rowSets():
        offset = 0
        rows = [0]
        while rows:
            rows = archivist.getQueryResults(query % offset)
            offset += setSize
            yield rows

    accumulator = helpers.Generic_class(reward=0, price=0)

    def takeAvg():
        avg = accumulator.reward/accumulator.price
        accumulator.price = 0
        accumulator.reward = 0
        return avg

    def addPt(price, reward):
        accumulator.price += price
        accumulator.reward += reward

    def getTime(height):
        return archivist.getQueryResults("SELECT time FROM blocks WHERE height=%i LIMIT 1" % height)[0][0].timestamp()

    windowSize = 144
    windowIdx = int(4096/windowSize)
    pts = []
    for i, rowSet in enumerate(rowSets()):
        offset = i*setSize
        print("processing rows %i through %i" % (offset, offset+setSize-1))
        for height, price, reward in rowSet:
            idx = int(height/windowSize)
            if idx > windowIdx:
                windowIdx = idx
                pts.append((idx-1, getTime(height), takeAvg()))
            addPt(price, reward)
    filepath = os.path.join(APPDIR, "ticket-return.json")
    with open(filepath, "w") as f:
        f.write(json.dumps(pts))


def plotTicketReturns():
    """
    Run calculateTicketReturns to create the dataset before running
    plotTicketReturns.
    The plot is historical data, with units annual percentage yield.
    """
    filepath = os.path.join(APPDIR, "ticket-return.json")
    with open(filepath, "r") as f:
        pts = json.loads(f.read())
    windows, stamps, returns = list(zip(*pts))
    power = 365/28

    def makeAPY(r):
        return (1+r)**power - 1

    plt.subplots_adjust(0.15, 0.2, 0.9, 0.9, 0, 0.1)
    fig = plt.gcf()
    ax = plt.gca()
    # ax.set_yscale('log')

    tMin = min(stamps)
    tMax = max(stamps)
    tRange = tMax - tMin
    xTicks, xLabels = mpl.getMonthTicks(tMin, tMax, 4, 3)
    ax.set_xlim(left=tMin, right=tMax)
    ax.set_xticks(xTicks)
    ax.set_xticklabels(xLabels, fontproperties=mpl.getFont("Roboto-Regular", 11))
    ax.set_xlim(left=helpers.mktime(2017, 6, 1), right=helpers.mktime(2019, 2, 1))

    yTicks = [0, 10, 20, 30, 40, 50]
    ax.set_yticks(yTicks)
    ax.set_yticklabels([str(y) for y in yTicks], fontproperties=mpl.getFont("Roboto-Regular", 11))
    ax.set_ylim(bottom=-3, top=57)

    pad = 0.5*tRange
    stockReturn = [7, 7]
    bondReturn = [2, 2]
    x = [tMin-pad, tMax+pad]
    ax.plot(x, stockReturn, linestyle="--", color="#aaaaaa", linewidth=1)
    ax.plot(x, bondReturn, linestyle="--", color="#aaaaaa", linewidth=1)
    ax.fill_between(x, stockReturn, bondReturn, color="#00000017")

    ax.plot(stamps, [makeAPY(r)*100 for r in returns], color="#333333", linewidth=1.5)

    def minApy(t):
        circulation = calc.getCirculatingSupply(t)
        posReward = calc.blockReward(calc.timeToHeight(t))*mainnet.STAKE_SPLIT
        return (mainnet.TicketExpiry*posReward/circulation/mainnet.TicketsPerBlock + 1)**(365/28) - 1

    ax.plot(stamps, [minApy(t)*100 for t in stamps], color="#555555", linestyle=":")

    plt.show()


def plotContour(processor, var1, var2, divisor=None, fmt="%i", lvlCount=15, 
                contourType="contourf", xLims=None, yLims=None, **kwargs):
    """
    plotContour can create a contour plot of cost of attack variation along any
    two attackCost parameters. Also surface plots and filled contours.
    """
    xKey, xVals = var1
    yKey, yVals = var2

    fig = plt.figure(figsize=(3.5, 3.5))
    if contourType == "surface":
        ax = fig.add_subplot("111", projection="3d")
    else:
        ax = fig.add_subplot("111")#, projection="3d")

    X, Y = np.meshgrid(xVals, yVals)
    divisor = divisor if divisor else 1
    Z = np.array([processor(**{xKey: x, yKey: y}, **kwargs).attackCost/divisor for x, y in zip(np.ravel(X), np.ravel(Y))]).reshape(X.shape)
    if contourType == "contour":
        plt.clabel(ax.contour(X, Y, Z, levels=lvlCount, cmap='plasma_r'), fmt=fmt)
    elif contourType == "contourf":
        plt.contourf(X, Y, Z, levels=lvlCount, cmap='plasma_r')
        plt.colorbar()
    elif contourType == "surface":
        ax.plot_surface(X, Y, Z, cmap='plasma_r')
    else:
        raise Exception("plotContour: Unknown contourType: %s" % contourType)
    if xLims:
        ax.set_xlim(**xLims)
    if yLims:
        ax.set_ylim(**yLims)
    mpl.setAxesFont("Roboto-Regular", 12, ax)
    plt.show()


def plotLine(variable, divisor=1, **kwargs):
    """
    Plot cost of attack for any parameter of attackCost.
    variable should be a dictionary with one key,
    which matches a kwargs of AttackCost, and whose value is a list or numpy
    array of points on the x axis.
    """
    fig = plt.gcf()
    ax = plt.gca()
    plt.subplots_adjust(0.22, 0.2, 0.9, 0.9, 0, 0.1)
    params = getCurrentParameters()
    helpers.recursiveUpdate(params, kwargs)
    k = next(iter(variable))
    X = variable[k]
    Ytotal = []
    Yrental = []
    Yretail = []
    Ywork = []
    Ys = []
    for x in X:
        params[k] = x
        A = calc.attackCost(**params)
        Ytotal.append(A.attackCost)
        Yrental.append(A.retailTerm)
        Yretail.append(A.rentalTerm)
        Ywork.append(A.workTerm)
        Ys.append(A.stakeTerm)

    linestyle = iter(["--", ":", "-."])
    ax.plot(X, [y/divisor for y in Ytotal], color="#333333", label="sum")
    ax.plot(X, [y/divisor for y in Ywork], color="#777777", linestyle=next(linestyle), label="work")
    # ax.plot(X, [y/divisor for y in Yretail], color="#777777", linestyle=linestyle(), label="retail")
    # ax.plot(X, [y/divisor for y in Yrental], color="#777777", linestyle=linestyle(), label="rental")
    ax.plot(X, [y/divisor for y in Ys], color="#777777", linestyle=next(linestyle), label="stake")
    mpl.setAxesFont("Roboto-Regular", 12, ax)
    plt.legend()
    plt.show()


def plotSupplyReturn():
    """
    APY vs locked DCR, with some lines representing total circulation.
    """
    fig = plt.gcf()
    ax = plt.gca()
    height = getDbHeight()
    X = np.arange(0.02, 0.25, 0.001)
    linestyle = iter([":", "-.", "-", "--"])
    color = iter(["#777777", "#777777", "#333333", "#777777"])
    for stakeShare in [0.10, 0.20, 0.3, 0.4]:
        Y = []
        for apy in X:
            locked = calc.ReverseEquations.calcTicketPrice(apy, height, stakeSplit=stakeShare)*mainnet.TicketExpiry/1e6
            Y.append(locked)
        plt.plot([x*100 for x in X], Y, linestyle=next(linestyle), color=next(color), label="%i%%" % (stakeShare*100,))
    supply = dataClient.supply()["supply_mined"]/1e8/1e6 # 1e8 converts from atoms. 1e9 to millions.
    ax.set_ylim(bottom=0, top=26)
    ax.set_xlim(left=0, right=26)
    mpl.setAxesFont("Roboto-Regular", 12, ax)
    # plt.legend()
    for supplyTime in (helpers.mktime(2019), helpers.mktime(2025), helpers.mktime(2040)):
        supply = calc.getCirculatingSupply(supplyTime)/1e6
        plt.plot([0, 100],[supply, supply], linestyle=":", color="#999999")
    plt.show()


def calcAlgos():
    """
    The cost of attack for different algorithms based on model devices.
    """
    fig = plt.gcf()
    ax = plt.gca()
    # ax.semilogy()
    ax.xaxis.set_ticks_position("both")

    xcRate = 17.
    height = getDbHeight()
    alpha = 0 # getDcrDataProfitability(xcRate, height)
    apy = getDcrDataAPY()
    maxProfitability = .003
    params = getCurrentParameters()
    linestyle = iter(["-", "--", ":", "-", "--", ":"])
    color = iter(["#333333", "#333333", "#333333", "#339999", "#339999", "#339999"])

    for algo, device in DeviceParams.items():
        X = np.linspace(device["min.profitability"]+1e-9, maxProfitability, 100)
        Y = []
        for alpha in X:
            params["roi"] = alpha
            Y.append(calc.attackCost(ticketFraction=1e-9, device=device, **params).attackCost)
        ax.plot([x*100. for x in X], [y/1e6 for y in Y], label=algo, linestyle=next(linestyle), color=next(color), zorder=2)
    ax.plot([0, 0], [-1000, 1000], color="#cccccc", linewidth=1, zorder=1)
    ax.set_ylim(bottom=0, top=129)
    mpl.setAxesFont("Roboto-Regular", 12, ax)
    plt.legend()
    plt.show()


def plotBlockCreationTime():
    """
    The time it would take to create a block on a private chain, with
    varying level of ticket fraction, y.
    """
    fig = plt.gcf()
    ax = plt.gca()
    plt.subplots_adjust(0.2, 0.2, 0.8, 0.8, 0, 0.1)
    ax.semilogy()

    X = np.linspace(1e-9, 1.-1e-9, 1000)
    Y = []
    Y2 = []
    for stakeOwnership in X:
        fullPower = 1/calc.concensusProbability(stakeOwnership)*mainnet.TargetTimePerBlock/C.HOUR
        Y.append(fullPower)
        Y2.append(fullPower/calc.hashportion(stakeOwnership))

    yTicks = [5/60., 1, 24, 24*30, 24*365]
    yLabels = ["$ t_b $", "hour", "day", "month", "year"]
    ax.set_yticks(yTicks)
    ax.set_yticklabels(yLabels)
    for y in yTicks:
        ax.plot([-100, 200], [y, y], linewidth=1, color="#dddddd", zorder=1)

    ax.set_ylim(bottom=1e-2, top=24*365*1.1)
    left, right = 0, 1.
    ax.set_xlim(left=left, right=right)

    # ticketPrice = dataClient.stake.diff()["current"]
    # xcFactor = fetchCMCPrice()*mainnet.TicketExpiry*ticketPrice/1e6
    # ax2 = ax.twiny()
    # ax2.set_xlim(left=left/xcFactor, right=right/xcFactor)
    # setAxesFont("Roboto-Regular", 12, ax2)

    mpl.setAxesFont("Roboto-Regular", 12, ax)
    # ax.plot([x*xcFactor for x in X], Y, color="#333333")
    ax.plot(X, Y, color="#555555", zorder=20)
    ax.plot(X, Y2, color="#555555", zorder=20)
    ax.fill_between(X, Y, Y2, color="#00000022", zorder=10)

    plt.show()


def plotTransactions(startHeight, makePlot=True, makeCsv=False, regularOnly=True):
    """
    Plot all transactions since start height. DCR vs time. Each transaction is
    one pixel.
    """
    bestBlockHeight = getDbHeight()
    height = startHeight
    # 0 = regular, 1 = ticket, 2 = vote, 3 = revocation
    types = ['Regular', 'Ticket', 'Vote', 'Rev']
    color = iter(['#00c903', '#c600c0', '#002ccc', '#d60000'])
    txTypes = {
        0: [],
        1: [],
        2: [],
        3: []
    }
    query = "SELECT tx_type, sent, time FROM transactions WHERE is_mainchain=TRUE AND (tx_type > 0 OR block_index > 0) AND block_height >= %i AND block_height < %i"
    minStamp = C.INF
    maxStamp = 0
    while height <= bestBlockHeight:
        txs = archivist.getQueryResults(query % (height, height+1000))
        for txType, sent, dt in txs:
            stamp = int(dt.timestamp())
            txTypes[txType].append((stamp, sent/1e8))
            minStamp = min(stamp, minStamp)
            maxStamp = max(stamp, maxStamp)
        height += 1000

    if makePlot:
        fig = plt.gcf()
        ax = plt.gca()
        ax.semilogy()
        if regularOnly:
            X, Y = zip(*txTypes[0])
            ax.scatter(X, Y, c="#555555", s=1, marker=".")
        else:
            for idx, pts in txTypes.items():
                X, Y = zip(*pts)
                ax.scatter(X, Y, c=next(color), s=1, marker=".")
        stamp = helpers.stamp2dayStamp(minStamp)
        xTicks = []
        xLabels = []
        tickSpacing = 5 # days
        while stamp < maxStamp:
            xTicks.append(stamp)
            xLabels.append(time.strftime("%b %d", time.gmtime(stamp)))
            stamp += 86400*tickSpacing
        ax.set_xticks(xTicks)
        ax.set_xticklabels(xLabels)
        mpl.setAxesFont("Roboto-Regular", 12, ax)
        plt.show()

    if makeCsv:
        csvPath = os.path.join(APPDIR, "transaction-dump_307000-312893.csv")
        try:
            with open(csvPath, 'w', newline='') as f:
                csvWriter = csv.writer(f)
                csvWriter.writerow(("timestamp", "DCR"))
                csvWriter.writerows(txTypes[0]) # only regular for now
            print("%i transactions dumped to CSV file at %s" % (len(txTypes[0]), csvPath))
        except Exception:
            print("Failed to create CSV file at %s" % csvPath)

# fetchCoinbase()
# storeDailyChainwork()

# plotDevices(profitProcessor)

# plotDevices(retailCapitalProcessor)

# parametrizeProfitability()

# plotSigma()

# plotPrices()

# calculateTicketReturns()
# plotTicketReturns()

# plotSupplyReturn()

# calcAlgos()

# plotLine(
#   {"ticketFraction": np.linspace(0.001, 0.999, 100)},
#   # rentability = 200e12,
#   # attackDuration = CDAY,
#   rentalRate = NICEHASH_RATE,
#   divisor = 1e6
# )

plotContour(
  calc.attackCost,
  ("stakeSplit", np.linspace(1e-9, 0.9, 250)),
  ("ticketFraction", np.linspace(1e-9, 1, 250)),
  fmt=lambda v: "%i M" % int(v),
  lvlCount=20,
  contourType="contourf",
  divisor=1e6,
  # rentalRate=NICEHASH_RATE,
  # rentalRatio = 0.2,
  **getCurrentParameters()
)

# plotBlockCreationTime()

# plotTransactions(307000, makePlot=True, makeCsv=True, regularOnly=True)