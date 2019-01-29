import os
import sys
import time
import calendar
import math
import json
# import traceback
import urllib.request as urlrequest

# For logging
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("pydecred")

# A few globals
INF = float("inf")
VERBOSITY = 1 # 0->low, 1->normal, 2->high
PACKAGEDIR = os.path.dirname(os.path.realpath(__file__))
HEADERS = {'Content-Type': 'application/json'}
A_DAY = 86400
AN_HOUR = 3600
PRIME_POWER_RATE = 0.05
SYMBOL = "DCR"

BLOCKTIME = 300
TICKETPOOL_SIZE = 40960
TICKETS_PER_BLOCK = 5
GENESIS_STAMP = 1454954400
REWARD_WINDOW_SIZE = 6144
STAKE_SPLIT = 0.3
POW_SPLIT = 0.6
TREASURY_SPLIT = 0.1


def mkdir(path):
    """
    Create the directory if it doesn't exist.
    """
    if os.path.isdir(path):
        return True
    if os.path.isfile(path):
        return False
    os.makedirs(path)
    return True


def yearmonthday(t):
    """
    Returns a tuple (year, month, day) with 1 <= month <= 12 
    and 1 <= day <= 31
    """
    return tuple(int(x) for x in time.strftime("%Y %m %d", time.gmtime(t)).split())


def mktime(year, month=None, day=None):
    """
    Take make a timestamp from year, month, day. See `yearmonthday`.
    """
    if month:
        if day:
            return calendar.timegm(time.strptime("%i-%s-%s" % (year, str(month).zfill(2), str(day).zfill(2)), "%Y-%m-%d"))
        return calendar.timegm(time.strptime("%i-%s" % (year, str(month).zfill(2)), "%Y-%m"))
    return calendar.timegm(time.strptime(str(year), "%Y"))


def dt2stamp(dt):
    return int(time.mktime(dt.timetuple()))


def stamp2dayStamp(stamp):
    """
    Reduces Unix timestamp to midnight.
    """
    return int(mktime(*yearmonthday(stamp)))


def ymdString(stamp):
    """ YY-MM-DD """
    return ".".join([str(x).zfill(2) for x in yearmonthday(stamp)])


MODEL_DEVICE = {
    "model": "INNOSILICON D9 Miner",
    "price": 1699,
    "release":  mktime(2018, 4, 18),
    "hashrate": 2.1e12,
    "power": 900
}


def clamp(val, minVal, maxVal):
    return max(minVal, min(val, maxVal))


def recursiveUpdate(target, source):
    """
    Recursively update the target dictionary with the source dictionary, leaving unfound keys in place.
    This is different than dict.update, which removes target keys not in the source

    :param dict target: The dictionary to be updated
    :param dict source: The dictionary to be integrated
    :return: target dict is returned as a convenience. This function updates the target dict in place.
    :rtype: dict
    """
    for k, v in source.items():
        if isinstance(v, dict):
            target[k] = recursiveUpdate(target.get(k, {}), v)
        else:
            target[k] = v
    return target


class Benchmarker:
    on = False

    def __init__(self, startStr=None):
        if not self.on:
            return
        if startStr:
            print(startStr)
        self.start()

    def start(self):
        if self.on:
            tNow = time.time()*1000
            self.startTime = tNow
            self.lapTime = tNow

    def resetLap(self):
        if self.on:
            tNow = time.time()*1000
            self.lapTime = tNow

    def lap(self, identifier):
        if self.on:
            tNow = time.time()*1000
            print("  %i ms to %s" % (int(tNow-self.lapTime), identifier))
            self.resetLap()

    def end(self, identifier):
        if self.on:
            tNow = time.time()*1000
            print("%i ms to %s" % (int(tNow-self.startTime), identifier))
            self.start()


class Generic_class:
    """
    If you want to use .dot notation but don't want to write a class.
    """
    def __init__(self, atsDict={}, **kwargs):
        for k, v in atsDict.items():
            setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)


def formatNumber(number, billions="B", spacer=" ", isMoney = False):
        """
        Format the number to a string with max 3 sig figs, and appropriate unit multipliers

        :param number:  The number to format
        :type number: float or int
        :param str billions: Default "G". The unit multiplier to use for billions. "B" is also common.
        :param str spacer: Default " ". A spacer to insert between the number and the unit multiplier. Empty string also common.
        :param bool isMoney: If True, a number less than 0.005 will always be 0.00, and a number will never be formatted with just one decimal place.
        """
        if number == 0:
            return "0%s" % spacer

        absVal = float(abs(number))
        flt = float(number)
        if absVal >= 1e12: # >= 1 trillion
            return "%.2e"
        if absVal >= 10e9: # > 10 billion
            return "%.1f%s%s" % (flt/1e9, spacer, billions)
        if absVal >= 1e9: # > 1 billion
            return "%.2f%s%s" % (flt/1e9, spacer, billions)
        if absVal >= 100e6: # > 100 million
            return "%i%sM" % (int(round(flt/1e6)), spacer)
        if absVal >= 10e6: # > 10 million
            return "%.1f%sM" % (flt/1e6, spacer)
        if absVal >= 1e6: # > 1 million
            return "%.2f%sM" % (flt/1e6, spacer)
        if absVal >= 100e3: # > 100 thousand
            return "%i%sk" % (int(round(flt/1e3)), spacer)
        if absVal >= 10e3: # > 10 thousand
            return "%.1f%sk" %  (flt/1e3, spacer)
        if absVal >= 1e3: # > 1 thousand
            return "%.2f%sk" % (flt/1e3, spacer)
        if isinstance(number, int):
            return "%i" % number
        if absVal >= 100:
            return "%i%s" % (flt, spacer)
        if absVal >= 10:
            if isMoney:
                return "%.2f%s" % (flt, spacer) # Extra degree of precision here because otherwise money looks funny.
            return "%.1f%s" % (flt, spacer) # Extra degree of precision here because otherwise money looks funny.
        # if absVal > 1:
        #   return "%.2f%s" % (absVal, spacer)
        if absVal > 0.01:
            return "%.2f%s" % (flt, spacer)
        if isMoney:
            return "0.00%s" % spacer
        return ("%.2e%s" % (flt, spacer)).replace("e-0", "e-")


def prepareLogger(filepath, printLvl=logging.INFO, logLevel=logging.DEBUG):
    """
    Set logger setttings appropriately
    """
    log_formatter = logging.Formatter('%(asctime)s %(module)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    fileHandler = RotatingFileHandler(filepath, mode='a', maxBytes=5*1024*1024, backupCount=2, encoding=None, delay=0)
    fileHandler.setFormatter(log_formatter)
    fileHandler.setLevel(logLevel)
    logger.setLevel(logLevel)
    logger.addHandler(fileHandler)
    if sys.executable and os.path.split(sys.executable)[1] == "pythonw.exe":
        # disabling stdout printing for pythonw
        pass
    else:
        # skip adding the stdout handler for pythonw in windows
        printHandler = logging.StreamHandler()
        printHandler.setFormatter(log_formatter)
        printHandler.setLevel(printLvl)
        logger.addHandler(printHandler)


def makeDevice(device):
    """
    Set some commonly used parameters.
    Modifies in-place. Device returned as convenience.
    """
    device["daily.power.cost"] = PRIME_POWER_RATE*device["power"]/1000*24
    device["min.profitability"] = -1*device["daily.power.cost"]/device["price"]
    device["power.efficiency"] = device["hashrate"]/device["power"]
    device["relative.price"] = device["price"]/device["hashrate"]
    return device
makeDevice(MODEL_DEVICE)


def fetchSettingsFile(filepath):
    """
    Fetches the JSON settings file, creating an empty json object if necessary
    """
    if not os.path.isfile(filepath):
        try:
            with open(filepath, 'w+') as file:
                file.write("{}")
        except IOError:
            print("Unable to create a settings file. Settings will not be saved across sessions.")
            return False
    if os.path.isfile(filepath):
        with open(filepath) as file:
            return json.loads(file.read())
    return False


def interpolate(pts, x):
    """
    Linearly interpret between points to get an estimate.
    pts should be of the form ((x1,y1), (x2,y2), ..) of increasing x.
    """
    lastPt = pts[0]
    for pt in pts[1:]:
        t, v = pt
        lt, lv = lastPt
        if t >= x:
            return lv + (x - lt)/(t - lt)*(v - lv)
        lastPt = pt


def derivative(pts, x):
    """
    Linearly interpret between points to get an estimate of the derivative (δy/δx).
    pts should be of the form ((x1,y1), (x2,y2), ..) of increasing x.
    """

    lastPt = pts[0]
    for pt in pts[1:]:
        t, v = pt
        if t >= x:
            lt, lv = lastPt
            return (v - lv)/(t - lt)
        lastPt = pt


# def hueGenerator():
#     denominator = 2
#     numerator = 1
# # todo: translate from js
# #    this.generateHue = function(){
#  #        // Generates colors on the sequence 0, 1/2, 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, 1/16, ...
#  #        while(self.colorDenominator < 512){ //Should generate a little more than 100 unique values
#  #            if(self.colorNumerator == 0){
#  #                self.colorNumerator += 1
#  #                return 0;
#  #            }
#  #            if(self.colorNumerator >= self.colorDenominator){
#  #                self.colorNumerator = 1; // reset the numerator
#  #                self.colorDenominator *= 2; // double the denominator
#  #                continue;
#  #            }
#  #            hue = self.colorNumerator/self.colorDenominator*360
#  #            self.colorNumerator += 2;
#  #            return hue
#  #        }
#  #        self.colorNumerator = 0
#  #        self.colorDenominator = 2
#  #        return self.generateHue()
#  #    }

def getUriAsJson(uri):
    req = urlrequest.Request(uri, headers=HEADERS, method="GET")
    return json.loads(urlrequest.urlopen(req).read().decode())


def getCirculatingSupply(tBlock):
    """ An approximation based on standard block time of 5 min and timestamp of genesis block """
    if tBlock < GENESIS_STAMP:
        return 0
    premine = 1.68e6
    if tBlock == GENESIS_STAMP:
        return premine
    block2reward = 21.84
    block4096stamp = mktime(2016, 2, 22)
    if tBlock < block4096stamp:
        return premine + (tBlock - GENESIS_STAMP)/BLOCKTIME*block2reward
    block4096reward = 31.20
    regularStamp = GENESIS_STAMP+REWARD_WINDOW_SIZE*BLOCKTIME
    if tBlock < regularStamp:
        return premine + (tBlock - GENESIS_STAMP)/BLOCKTIME*block4096reward
    tRemain = tBlock - regularStamp
    blockCount = tRemain/BLOCKTIME
    periods = blockCount/float(REWARD_WINDOW_SIZE)
    vSum = 1833321 # supply at start of regular reward period
    fullPeriods = int(periods)
    partialPeriod = periods - fullPeriods
    p = 0
    for p in range(fullPeriods):
        reward = blockReward((p+1)*REWARD_WINDOW_SIZE)
        vSum += reward*REWARD_WINDOW_SIZE
    p += 1
    reward = blockReward((p+1)*REWARD_WINDOW_SIZE)
    vSum += reward*REWARD_WINDOW_SIZE*partialPeriod
    return vSum


def timeToHeight(t):
        return int((t-GENESIS_STAMP)/BLOCKTIME)


def binomial(n, k):
    f = math.factorial
    return f(n)/f(k)/f(n-k)


def concensusProbability(stakeportion, winners=TICKETS_PER_BLOCK, participation=1):
    halfN = winners/2.
    k = 0
    probability = 0
    while k < halfN:
        probability += binomial(winners, k)*stakeportion**(winners-k)*((1-stakeportion)*participation)**k
        k += 1
    if probability == 0:
        print("Quitting with parameters %s" % repr((stakeportion, winners, participation)))
    return probability


def hashportion(stakeportion, winners=TICKETS_PER_BLOCK, participation=1):
    return 1 - concensusProbability(stakeportion, winners)


def grossEarnings(device, roi, energyRate=PRIME_POWER_RATE):
    return roi*device["price"] + 24*device["power"]*energyRate/1000


def blockReward(height):
    # https://docs.decred.org/advanced/inflation/
    return 31.19582664*(100/101)**int(height/6144)


def dailyPowRewards(height, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
    return A_DAY/blockTime*blockReward(height)*powSplit


def dailyPosRewards(height, blockTime=BLOCKTIME, stakeSplit=STAKE_SPLIT):
    return A_DAY/blockTime*blockReward(height)*stakeSplit


def networkDeviceCount(device, xcRate, roi, height=3e5, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
    return dailyPowRewards(height, blockTime, powSplit)*xcRate/grossEarnings(device, roi)


def networkHashrate(device, xcRate, roi, height=3e5, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
    return networkDeviceCount(device, xcRate, roi, height, blockTime, powSplit)*device["hashrate"]


def calcTicketPrice(apy, height, winners=TICKETS_PER_BLOCK, stakeSplit=STAKE_SPLIT):
    Rpos = stakeSplit*blockReward(height)
    return Rpos/(winners*((apy + 1)**(25/365.) - 1))


class Ay:
    def __init__(self, retailTerm, rentalTerm, stakeTerm, ticketFraction):
        self.retailTerm = retailTerm
        self.rentalTerm = rentalTerm
        self.stakeTerm = stakeTerm
        self.workTerm = rentalTerm + retailTerm
        self.attackCost = retailTerm + rentalTerm + stakeTerm
        self.ticketFraction = ticketFraction

    def __str__(self):
        return "<AttackCost: ticketFraction %.3f, workTerm %i, stakeTerm %i, attackCost %i>" % (self.ticketFraction, self.workTerm, self.stakeTerm, self.attackCost)


def AttackCost(ticketFraction=None, xcRate=None, blockHeight=None, roi=None, ticketPrice=None, blockTime=BLOCKTIME, powSplit=None, 
        stakeSplit=None, treasurySplit=TREASURY_SPLIT, rentability=None, nethash=None, winners=TICKETS_PER_BLOCK, participation=1., 
        poolSize=TICKETPOOL_SIZE, apy=None, attackDuration=AN_HOUR, device=None, rentalRatio=None, rentalRate=None):
    if any([x is None for x in (ticketFraction, xcRate, blockHeight)]):
        raise Exception("ticketFraction, xcRate, and blockHeight are required args/kwargs for AttackCost")
    if treasurySplit is None:
        raise Exception("AttackCost: treasurySplit cannot be None")

    if stakeSplit:
        if not powSplit:
            powSplit = 1 - treasurySplit - stakeSplit
    else:
        if powSplit:
            stakeSplit = 1 - treasurySplit - powSplit
        else:
            powSplit = POW_SPLIT
            stakeSplit = STAKE_SPLIT

    device = device if device else MODEL_DEVICE
    if nethash is None:
        if roi is None: # mining ROI could be zero 
            raise Exception("minimizeY: Either a nethash or an roi must be provided")
        nethash = networkHashrate(device, xcRate, roi, blockHeight, blockTime, powSplit)
    if rentability or rentalRatio:
        if not rentalRate:
            raise Exception("minimizeY: If rentability is non-zero, rentalRate must be provided")
    else:
        rentalRate = 0
    if ticketPrice is None:
        if not apy:
            raise Exception("minimizeY: Either a ticketPrice or an apy must be provided")
    ticketPrice = calcTicketPrice(apy, blockHeight, winners, stakeSplit)
    stakeTerm = ticketFraction*poolSize*ticketPrice*xcRate
    hashPortion = hashportion(ticketFraction, winners, participation)
    attackHashrate = nethash*hashPortion
    rent = rentability if rentability is not None else attackHashrate*rentalRatio if rentalRatio is not None else 0
    rentalPart = min(rent, attackHashrate)
    retailPart = attackHashrate - rentalPart
    rentalTerm = rentalPart*rentalRate/86400*attackDuration
    retailTerm = retailPart*( device["relative.price"] + device["power"]/device["hashrate"]*PRIME_POWER_RATE/1000/3600*attackDuration)
    return Ay(retailTerm, rentalTerm, stakeTerm, ticketFraction)


def purePowAttackCost(xcRate=None, blockHeight=None, roi=None, blockTime=BLOCKTIME, treasurySplit=TREASURY_SPLIT, 
    rentability=None, nethash=None,attackDuration=AN_HOUR, device=None, rentalRatio=None, rentalRate=None, **kwargs):
    if any([x is None for x in (xcRate, blockHeight)]):
        raise Exception("xcRate and blockHeight are required args/kwargs for PurePowAttackCost")
    device = device if device else MODEL_DEVICE
    if nethash is None:
        if roi is None: # mining ROI could be zero 
            raise Exception("minimizeY: Either a nethash or an roi must be provided")
        nethash = networkHashrate(device, xcRate, roi, blockHeight, blockTime, 1-treasurySplit)
    if rentability or rentalRatio:
        if not rentalRate:
            raise Exception("minimizeY: If rentability is non-zero, rentalRate must be provided")
    else:
        rentalRate = 0
    attackHashrate = 0.5*nethash
    rent = rentability if rentability is not None else attackHashrate*rentalRatio if rentalRatio is not None else 0
    rentalPart = min(rent, attackHashrate)
    retailPart = attackHashrate - rentalPart
    rentalTerm = rentalPart*rentalRate/86400*attackDuration
    retailTerm = retailPart*( device["relative.price"] + device["power"]/device["hashrate"]*PRIME_POWER_RATE/1000/3600*attackDuration)
    return Ay(retailTerm, rentalTerm, 0, 0)


def minimizeAy(*args, grains=100, **kwargs):
    lowest = INF
    result = None
    grainSize = 0.999/grains
    for i in range(1, grains):
        poolPortion = grainSize*i
        A = AttackCost(grainSize*i, *args, **kwargs)
        if A.attackCost < lowest:
            lowest = A.attackCost
            result = A
    return result