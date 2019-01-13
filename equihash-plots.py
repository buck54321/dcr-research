from pystrata.compatibility import *
from pystrata.commonfunctions import *
from mplstuff import *
import os
import json
import time, calendar
import math, statistics
import urllib.request as urlrequest
import traceback
from blockninja import BlockNinja
import pickle
import statistics
import imageio
from PIL import Image, ImageFilter

archivist = Archivist("/home/buck/.pystrata/stratarchive.sql", logger)
SYMBOLS = ["ZEC", "BTG", "ZCL", "ZEN"]
WALLET_COUNT_DIR = "wallet-counts"

	# Currencies table
	# currencies = DatabaseTable("currencies")
	# "symbol_id", "int"
	# "symbol", "varchar(10)"
	# "name", "varchar(255)"


	# # Market history table
	# candlesticks = DatabaseTable("candlesticks")
	# "symbol_id", "int"
	# "date_stamp", "int"
	# "open", "float"
	# "high", "float"
	# "low", "float"
	# "close", "float"
	# "volume", "float"
	# "market_cap", "float"

symbolInfo = {}
seed = {
	"name": "wmuser",
	"password": "wmpwd123321"
}
symbolInfo["BTG"] = recursiveUpdate(dict(seed), {
	"algorithm":"Equihash",
	"node.path": "/home/buck/crypto/btg/bin/bgoldd",
	"rpc.protocol":"btc",
	"port":10456,
	"addnode.list": "https://status.bitcoingold.org/dl.php?format=config", 
	"custom.args": ["-txindex=1"],
	"block.reward" : lambda h: 12.5,
	"block.time": 600,
	"long.name": "Bitcoin Gold",
	"leader.style" : {
		"linestyle":"-",
		"color":"#5555bb"
	},
	"genesis.height":491407
})
symbolInfo["ZEC"] = recursiveUpdate(dict(seed), {
	"algorithm":"Equihash",
	"node.path": "/home/buck/crypto/zec/zcashd",
	"rpc.protocol":"btc",
	"port":10457,
	"addnode.list": "https://www.coinexchange.io/network/peers/ZEC", # need to pull json out of html, not sure how to do that yet
	"custom.args": ["-txindex=1"],
	"block.reward" : lambda h: 10,
	"block.time":150,
	"long.name": "ZCash",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["AEON"] = recursiveUpdate(dict(seed), {
	"node.path": "/home/buck/crypto/aeon/aeond",
	"rpc.protocol":"xmr",
	"port":10458,
	"addnode.list": None,
	"custom.args": [], 
	"long.name": "AEON",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["ZEN"] = recursiveUpdate(dict(seed), {
	"algorithm":"Equihash",
	"node.path": "zend",
	"rpc.protocol":"btc",
	"port":10459,
	"addnode.list": None,
	"custom.args": [],
	"block.reward" : lambda h: 8.75, 
	"long.name": "Horizen",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["ZCL"] = recursiveUpdate(dict(seed), {
	"node.path": "/home/buck/crypto/zcl/zcld",
	"rpc.protocol":"btc",
	"port":10460,
	"addnode.list": None,
	"custom.args": ["-disabledeprecation=1.0.14"],
	"block.reward" : lambda h: 12.5, 
	"long.name": "ZClassic",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["KMD"] = recursiveUpdate(dict(seed), {
	"node.path": "/home/buck/crypto/kmd/komodod",
	"rpc.protocol":"btc",
	"port":10461,
	"addnode.list": None,
	"custom.args": [],
	"block.reward" : lambda h: 3, 
	"long.name": "Komodo",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["GRS"] = recursiveUpdate(dict(seed), {
	"node.path": "/home/buck/crypto/grs/groestlcoind",
	"rpc.protocol":"btc",
	"port":10462,
	"addnode.list": None,
	"custom.args": [], 
	"long.name": "Greostlcoin",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["ETH"] = recursiveUpdate(dict(seed), {
	"algorithm":"Ethash",
	"node.path": "/home/buck/crypto/eth/geth",
	"rpc.protocol":"eth",
	"port":10463,
	"addnode.list": None,
	"custom.args": ["--syncmode full", "--cache 8192"], 
	"long.name": "Ethereum",
	"leader.style" : {
		"linestyle":"-",
		"color":"#33bb33"
	},
	"block.reward":lambda h: 5 if h < 4.37e6 else 3,
	"block.time":15
})
symbolInfo["BCI"] = recursiveUpdate(dict(seed), {
	"node.path": "/home/buck/crypto/bci/bcid",
	"rpc.protocol":"btc",
	"port":10464,
	"addnode.list": None, # need to pull json out of html, not sure how to do that yet
	"custom.args": ["-txindex=1"],
	"block.reward" : lambda h: 10.76, 
	"long.name": "Bitcoin Interest",
	"leader.style" : {
		"linestyle":"-",
		"color":"#555555"
	}
})
symbolInfo["ETC"] = recursiveUpdate(dict(seed), {
	"algorithm":"Ethash",
	"node.path": "/home/buck/crypto/etc/geth",
	"rpc.protocol":"eth",
	"port":10465,
	"addnode.list": None,
	"custom.args": ["--port 11465", "--cache 8192"], 
	"long.name": "Ethereum Classic",
	"leader.style" : {
		"linestyle":"-",
		"color":"#bb5555"
	},
	"block.reward":lambda h: 5 if h < 5e6 else 4,
	"block.time":15,
	"genesis.height":1920001
})
symbolInfo["DCR"] = recursiveUpdate(dict(seed), {
	# /home/buck/crypto/dcr/dcrd --rpcuser=wmuser --rpcpass=wmpwd123321 --rpclisten=127.0.0.1:10466 --txindex --addrindex
	"algorithm":"Equihash",
	"node.path": "/home/buck/crypto/dcr/dcrd",
	"rpc.protocol":"btc",
	"port":10466,
	"addnode.list": None, 
	"custom.args": ["-txindex=1"],
	"block.reward" : lambda h: 12.5,
	"block.time": 300,
	"long.name": "Decred",
	"leader.style" : {
		"linestyle":"-",
		"color":"#5555bb"
	}
})

algoInfo = {
	"Equihash": {
		"ranges":{
			"gpu":{
				"start":0,
				"linecolor":"#1d33af",
				"segments":[
					{
						"label":"GPU before ASICS",
						"end":1529668551,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor":"#1d33af18"
					},
					{
						"label":"GPU after ASICS",
						"end":1e12,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor":"#1d33af00"
					}
				],
				"low":{
					"model":"GeForece GTX 1050 Ti",
					"hashrate": 180,
					"power": 75,
					"price": 200,
				},
				"high":{
					"model":"GeForece GTX 1080 Ti",
					"hashrate": 735,
					"power": 200,
					"price": 475,
				}
			},
			"asic":{
				"start":1522583751,
				"linecolor": "#84166c",
				"segments":[
					{
						"label":"ASIC rumors only",
						"end": 1525348551,
						"linestyle": ":",
						"linewidth": 0.75,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor": "#84166c18"
					},{
						"label":"ASIC confirmed",
						"end": 1529668551,
						"linestyle": ":",
						"linewidth": 0.75,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor": "#84166c18"
					},{
						"label":"ASICs shipped",
						"end": 1e12,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor": "#84166c18"
					}
				],
				"low":{
					"model":"Bitmain Z9 Mini",
					"hashrate": 10000,
					"power": 266,
					"price": 800,
				},
				"high":{
					"model":"Asicminer Zeon",
					"hashrate": 180000,
					"power": 2200,
					"price": 19900,
				}
			}
		}
	},
	"Ethash": {
		"ranges":{
			"gpu":{
				"start":0,
				"linecolor":"#1d33af",
				"segments":[
					{
						"label":"GPU before ASIC",
						"end":1531756475,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor":"#1d33af18"
					},
					{
						"label":"GPU after ASIC",
						"end":1e12,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor":"#1d33af00"
					}
				],
				"low":{
					"model":"GeForece GTX 1050 Ti",
					"hashrate": 12e6,
					"power": 75,
					"price": 200,
				},
				"high":{
					"model":"GeForece GTX 1080 Ti + EthLargement Pill",
					"hashrate": 50e6,
					"power": 250,
					"price": 475,
				}
			},
			"asic":{
				"start":1522770875,
				"linecolor": "#84166c",
				"segments":[
					{
						"label":"ASIC confirmed",
						"end":1531756475,
						"linestyle": ":",
						"linewidth": 0.75,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor": "#84166c18"
					},{
						"label":"ASIC shipped",
						"end": 1e12,
						"linestyle": "-",
						"linewidth": 1.5,
						"timestamps":[],
						"high":[],
						"low":[],
						"fillcolor": "#84166c18"
					}
				],
				"high":{
					"model": "Bitmain Antminer E3",
					"hashrate": 190e6,
					"power": 760,
					"price": 1150,
				},
				"low":{
					"model": "Innosilicon A10 ETHMaster",
					"hashrate": 485e6,
					"power": 850,
					"price": 5000,
				}
			}
		}
	}
}

revertedTips = [
	{
		"height": 529043,
		"hash": "000000001783db4c9bcc58c4c28c517bf839b785ac02a836d42ce6438def5684",
		"branchlen": 22,
		"status": "valid-fork"
	}, 
	{
		"height": 528953,
		"hash": "0000000024cc17971de3cf0b03f527562093cd5e10ee26562376b1b40df65776",
		"branchlen": 2,
		"status": "valid-fork"
	}, 
	{
		"height": 528942,
		"hash": "000000002b887b73e05333c93cd83096b03405ab2dbc7b2164a59a5ec4614a7f",
		"branchlen": 11,
		"status": "valid-fork"
	}, 
	{
		"height": 528929,
		"hash": "0000000032c7e239820d283ce531867683b6da22f2a5df24a7a8ab7a4c5ae40b",
		"branchlen": 9,
		"status": "valid-fork"
	}, 
	{
		"height": 528916,
		"hash": "00000000291b073f1b504783a81c0dd01f3ceb94279eff002c658be547056cbd",
		"branchlen": 7,
		"status": "valid-fork"
	}, 
	{
		"height": 528908,
		"hash": "000000001e5d6d7f66604ffba4dd5a7f09ba94686c65560c8da1e8695d03f062",
		"branchlen": 9,
		"status": "valid-fork"
	}, 
	{
		"height": 528896,
		"hash": "000000002ab685f176f820a10df2a21e8891457534dcbfd13c74cdfd861765af",
		"branchlen": 11,
		"status": "valid-fork"
	}, 
	{
		"height": 528880,
		"hash": "0000000024980856ef6ed778b6a6aafb3d160e151e92784574f2b867b25fa35a",
		"branchlen": 6,
		"status": "valid-fork"
	}, 
	{
		"height": 528865,
		"hash": "000000002edeb249dbb2e28d7e17ca275fb3b3b6f738d6999099f4b5bbb6a001",
		"branchlen": 3,
		"status": "valid-fork"
	}, 
	{
		"height": 528836,
		"hash": "0000000021557ac1e65c1246d869f519c12901101b1f8377d720b2796da3de49",
		"branchlen": 5,
		"status": "valid-fork"
	}, 
	{
		"height": 528778,
		"hash": "000000000a58038744f54d8be26cb9959986211b7a509ad7359c7131348e97d6",
		"branchlen": 10,
		"status": "valid-fork"
	}, 
	{
		"height": 528765,
		"hash": "000000001acf8667a73029b5cef8614cdcf593f9eb139471d1da17e09b430571",
		"branchlen": 5,
		"status": "valid-fork"
	}, 
	{
		"height": 528752,
		"hash": "000000002fee9bb475fe5ccc40f1b5907493bd8983574e70648cc7e6afacae50",
		"branchlen": 2,
		"status": "valid-fork"
	}, 
	{
		"height": 528745,
		"hash": "000000002baff4217c1098548948cb08fd9183381672f919843a0f9f29664c49",
		"branchlen": 3,
		"status": "valid-fork"
	}, 
	{
		"height": 528736,
		"hash": "0000000009302871e691105605e266e66b66a42b26d22c0ee5c7d2e4c93934ef",
		"branchlen": 2,
		"status": "valid-fork"
	}, 
	{
		"height": 528732,
		"hash": "00000000190c90b77cebd11ecedc4cb38d00f8c941c6287a569b06905824fd9f",
		"branchlen": 1,
		"status": "valid-fork"
	}, 
	{
		"height": 528651,
		"hash": "000000002af60b217f587617c1c00e9175d3d6b7f9e684bcd298450791a943ce",
		"branchlen": 1,
		"status": "valid-fork"
	}
]

def mkdir(path):
	if os.path.isdir(path):
		return True
	if os.path.isfile(path):
		return False
	os.mkdir(path)
	return True

def getFirstLastPairs(symbol, tStart=None):
	blockNinja = getBlockNinja()
	algo = symbolInfo[symbol]["algorithm"]
	chainworkKey = "totalDifficulty" if algo == "Ethash" else "chainwork"
	zeroBlock = blockNinja.getGenesisBlock(symbol)
	if not zeroBlock:
		print("zeroBlock not found: %s" % repr(zeroBlock.errorMessage))
		return False


	# block = zeroBlock
	# lastTime = None
	# msgs = []
	# for _ in range(34):
	# 	if lastTime:
	# 		msgs.append(str(block["time"] - lastTime))
	# 	lastTime = block["time"]
	# 	block = blockNinja.iterateBlock(symbol, block)
	# exit("\n".join(msgs))



	tZeroStamp = zeroBlock["time"]+86400
	if symbol == "BTG":
		tZeroStamp += 86400
	blockPeriod = blockNinja.getAverageBlockTime(symbol)
	tip = blockNinja.getTip(symbol)
	if not tip:
		print("no tip")
		return False
	tLastStamp = tip["time"]
	# tOneStamp = tLastStamp - 670*86400

	# if tZeroStamp > tOneStamp:
	# 	tOneStamp = tZeroStamp
	tIterator = tStart if tStart and tStart >= tZeroStamp else tZeroStamp
	firstBlocks = []
	yfb = None # yesterday's first block
	initialGuess = None
	while tIterator < tLastStamp:
		year, month, day = yearmonthday(tIterator)
		print("getting %i-%i-%i" % (year, month, day))
		firstBlock = blockNinja.getFirstBlockOfDay(symbol, year, month, day, initialGuess=initialGuess)
		if not firstBlock:
			print("No firstBlock: %r" % firstBlock)
			return False
		if yfb:
			ylb = blockNinja.getBlockByHeight(symbol, firstBlock["height"]-1) # yesterday's last block
			if not ylb:
				print("no ylb")
				return False
			deposit = (yfb["height"], yfb["time"], yfb[chainworkKey]),(ylb["height"], ylb["time"], ylb[chainworkKey])

			print("depositing %s" % repr(deposit))
			firstBlocks.append(deposit)
			initialGuess = int(firstBlock["height"] + 86400/((ylb["time"] - yfb["time"])/(ylb["height"] - yfb["height"])))
		yfb = firstBlock
		tIterator = tIterator + 86400
	with open("data/%s-day-spans.json" % symbol, "w") as f:
		f.write(json.dumps(firstBlocks))

def processRawData(symbols=None):
	symbols = symbols if symbols else SYMBOLS
	symbolLists = {}
	for symbol in symbols:
		symbolList = symbolLists[symbol] = []
		filename = "/home/buck/programs/blockchain/data/%s-day-spans.json" % symbol
		results = archivist.getQueryResults("SELECT symbol_id FROM currencies WHERE symbol=? ", (symbol, ))
		symbolId = results[0][0]
		with open(filename, "r") as f:
			symbolData = json.loads(f.read())
		for firstBlock, lastBlock in symbolData:
			hFirst, tFirst, wFirst = firstBlock
			hLast, tLast, wLast = lastBlock
			wLast, wFirst = int(wLast, 16), int(wFirst, 16)
			query = "SELECT high, low, close, date_stamp FROM candlesticks WHERE symbol_id=? AND date_stamp < ? ORDER BY date_stamp DESC LIMIT 1"
			results = archivist.getQueryResults(query, (symbolId, tLast))
			if not results:
				print("got no results: %r" % results)
				continue
			high, low, close, tStamp = results[0]
			blocks = hLast - hFirst
			tDelta = tLast-tFirst
			blockReward = symbolInfo[symbol]["block.reward"](hLast)
			dailyOut = 86400/tDelta*blocks*blockReward*close
			hashrate = (wLast-wFirst)/(tLast-tFirst)
			# print(hashrate)
			# print("--(high, low, close), hashrate, dailyOut: %s, %i, %i" % (repr((high, low, close)), hashrate, dailyOut))
			if symbol == "BTG":
				if hashrate > 1e15 or hashrate < 1:
					# BTG has a weird first point
					continue
				# if hLast > 536200: # timestamp ~= 1530679085
				# 	continue
			symbolList.append((tStamp, hashrate, dailyOut))
			# print("%s: tDelta=%i, blocks=%i, close=%i, blockReward=%.2f, dailyOut=%i, hashrate=%i" % (
			# 	symbol, tDelta, blocks, close, blockReward, dailyOut, hashrate
			# ))
		if symbol == "BTG":
			symbolList.pop(0)
		with open(os.path.join("data","%s.json" % symbol), "w") as f:
			f.write(json.dumps(symbolList))

def yearmonthday(t):
	return tuple(int(x) for x in time.strftime("%Y %m %d", time.gmtime(t)).split())

def mktime(year, month=None, day=None):
	if month:
		if day:
			return calendar.timegm(time.strptime("%i-%s-%s" % (year, str(month).zfill(2), str(day).zfill(2)), "%Y-%m-%d"))
		return calendar.timegm(time.strptime("%i-%s" % (year, str(month).zfill(2)), "%Y-%m"))
	return calendar.timegm(time.strptime(str(year), "%Y"))

def getPts(symbols=None, start=None, end=None):
	symbols = symbols if symbols else SYMBOLS
	timePts = {}
	for symbol in symbols:
		with open(os.path.join("data","%s.json" % symbol), "r") as f:
			pts = json.loads(f.read())
		for timestamp, hashrate, dailyOut in pts:
			if start and timestamp < start:
				continue
			if end and timestamp > end:
				break
			if timestamp not in timePts:
				timePts[timestamp] = {
					"timestamp":timestamp,
					"hashrate":hashrate,
					"daily.out":dailyOut, 
					"pph":dailyOut/(hashrate*86400/1e9)
				}
			else:
				timePt = timePts[timestamp]
				timePt["hashrate"] += hashrate
				timePt["daily.out"] += dailyOut
				# apply an average weighted on dailyOut
				timePt["pph"] = timePt["daily.out"]/(timePt["hashrate"]*86400/1e9)
	return [timePts[t] for t in sorted(timePts)]

def getMonthTicks(first, last, addYear=True):
	xTicks = []
	xLabels = []
	year, month, _ = yearmonthday(first)
	minStamp = time.mktime(time.strptime("%s-%s" % (year, month), "%Y-%m"))
	xTicks.append(minStamp)
	if addYear:
		xLabels.append(time.strftime("%b '%y", time.gmtime(minStamp)))	
	else:
		xLabels.append(time.strftime("%b", time.gmtime(minStamp)))
	lastYear, lastMonth, _ = yearmonthday(last)
	monthStamp = 0
	while True:
		month += 1
		newYear = False
		if month == 13:
			year += 1
			month = 1
			newYear = True
		finalStamp = False
		if year > lastYear:
			finalStamp = True
		if year == lastYear and month > lastMonth:
			finalStamp = True
		monthStamp = time.mktime(time.strptime("%s-%s" % (year, month), "%Y-%m"))
		xTicks.append(monthStamp)
		if newYear or finalStamp:
			xLabels.append(time.strftime("%b '%y", time.gmtime(monthStamp)))
		else:
			xLabels.append(time.strftime("%b", time.gmtime(monthStamp)))
		if finalStamp:
			break
	return xTicks, xLabels

def unpackProfitLine(d):
		# tRange, style, linewidth, stamps, vals
		return d["time.range"], d["style"], d["linewidth"], d["timestamps"], d["values"]

def deviceTemplates():
	def findPrice(timestamp, pts):
		for i, pt in enumerate(pts):
			if timestamp < pt[0]:
				lastPt = pts[i-1]
				pDelta = pt[1] - lastPt[1]
				tRange = pt[0] - lastPt[0]
				tDelta = timestamp - lastPt[0]
				return lastPt[1] + (tDelta/tRange)*pDelta
	pts1050 = [(0,180),(1538413150,180), (1517590750, 295), (1533142750, 210), (1538413150, 200), (1e12,200)]
	pts1080 = [(0, 800), (1514825950, 800), (1516294750, 890), (1517849950, 1100), (1525539550, 1000), (1534352350, 775), (1e12, 775)]
	ptsZ9 = [(0, 1000), (1525348551, 1000), (1528199751, 850), (1538394951, 745), (1e12, 745)]
	powerFactor = 1/1000*24
	return {
		"GPU":{
			"lowend":{
				"hashrate":180,
				"power":75,
				"power.rate": 0.15*powerFactor,
				"price.function": lambda t, p=pts1050: findPrice(t,p),
				"price":200,
				"range.lines":[
					{
					"time.range": (0,1529668551),
					"style": "-",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1529668551,1e12),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				}],
				"roi.time":[],
				"release.date":0, 
				"timestamps":[],
				"color":"#1d33af"
			},
			"highend":{
				"hashrate":735,
				"power":200,
				"power.rate": 0.05*powerFactor,
				"price.function": lambda t, p=pts1080: findPrice(t,p),
				"price":475,
				"range.lines":[
					{
					"time.range": (0,1529668551),
					"style": "-",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1529668551,1e12),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				}],
				"roi.time":[],
				"release.date":0, 
				"timestamps":[],
				"color":"#1d33af"
			}
		},
		"ASIC":{
			"lowend":{
				"hashrate":10000,
				"power":266,
				"power.rate": 0.15*powerFactor,
				"price.function": lambda t, p=ptsZ9: findPrice(t,p),
				"price":800,
				"range.lines":[{
					"time.range": (1522583751,1525348551),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1525348551,1529668551),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1529668551,1e12),
					"style": "-",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				}],
				"roi.time":[], 
				"release.date":1525348551, 
				"timestamps":[],
				"color":"#84166c"
			},
			"highend":{
				"hashrate":180000,
				"power":2200,
				"power.rate": 0.05*powerFactor,
				"price.function": lambda t: 19900,
				"price":19900,
				"range.lines":[{
					"time.range": (1522583751,1525348551),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1525348551,1529668551),
					"style": ":",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				},{
					"time.range": (1529668551,1e12),
					"style": "-",
					"linewidth": 1,
					"timestamps":[],
					"values":[]
				}],
				"roi.time":[], 
				"release.date":1525348551, 
				"timestamps":[],
				"color":"#84166c"
			}			
		}
	}

def calculateDeviceProfitability(ptsList):
	deviceStats = deviceTemplates()
	timestamps = []
	pphs = []
	for i, pt in enumerate(ptsList):
		timestamp = pt["timestamp"]
		timestamps.append(timestamp)
		hashrate = pt["hashrate"]
		dailyOut = pt["daily.out"]
		pph = pt["pph"]
		pphs.append(pph)
		for name, tiers in deviceStats.items():
			for tier, data in tiers.items():
				rangeLines = data["range.lines"]
				firstStamp = min([p["time.range"][0] for p in rangeLines])
				lastStamp  = max([p["time.range"][1] for p in rangeLines])
				if timestamp < firstStamp or timestamp > lastStamp:
					continue
				data["timestamps"].append(timestamp)
				dHashrate = data["hashrate"]
				daysMH = 86400*dHashrate/1e6
				dPower = data["power"]
				dPrice = data["price.function"](timestamp)
				dConstantPrice = data["price"]
				# print("%s: %i" % (name, dPrice))
				dPowerCost = dPower*data["power.rate"]
				dProfitability = (dHashrate/hashrate*dailyOut - dPowerCost)/dConstantPrice
				# (1522583751,1525348551),"rumor",".",[]
				for tRange, style, linewidth, stamps, vals in [unpackProfitLine(l) for l in rangeLines]:
					if tRange[0] <= timestamp < tRange[1]:
						stamps.append(timestamp)
						vals.append(dProfitability)
						break
				# Now integrate for ROI, extending last know profitability indefinitely if roi hasn't been achieved yet
				profit = 0
				lastStamp = timestamp
				lastProfitability = 0
				maxPayback = 5*365
				for timePt in ptsList[i:]:
					lastStamp = timePt["timestamp"]
					lastProfitability = dHashrate/timePt["hashrate"]*timePt["daily.out"] - dPowerCost
					# if name == "GPU" and tier == "highend":
					# 	print("highend GPU profitability: $%.2f/day, %s" % (lastProfitability, repr([dPowerCost, dHashrate/timePt["hashrate"]*timePt["daily.out"]])))
					profit += lastProfitability
					# print(repr((profit, dPrice)))
					if profit >= dPrice:
						break
					elif lastProfitability < 0:
						# print("%s became unprofitable at %i, barring ROI for a device purchased on %i" % (name, lastStamp, timestamp))
						break
				# print("--%s" % repr([name, tier, profit]))
				if profit >= dPrice:
					paybackDays = (lastStamp-timestamp)/86400
				else:
					if lastProfitability > 0:
						paybackDays = (lastStamp-timestamp)/86400 + (dPrice-profit)/lastProfitability
					else:
						paybackDays = maxPayback
				paybackDays = min(paybackDays, maxPayback)
				# if name == "GPU" and tier == "lowend":
				# 	print("--%s" % repr([name, tier, paybackDays, profit, dPrice]))
				data["roi.time"].append({
					"payback.days":paybackDays,
					"is.paid":profit >= dPrice
				})
	return timestamps, deviceStats, pphs

def plotEquihash(symbols=None, withEvents=True, addYear=True, plotPaybackTime=False, plotPph=False, plotProfit=True):
	symbols = symbols if symbols else SYMBOLS
	
	fig = plt.gcf()
	fig.set_dpi(100)
	fig.set_size_inches(6, 6)
	plt.subplots_adjust(0.30, 0.15, 0.95, 0.85, 0, 0.1)

	events = [
		{
			"title":"ASIC\nrumors",
			"timestamp": 1522583751 # April 1st, 2018
		},
		{
			"title":"Z9 Mini\nconfirmed",
			"timestamp": 1525348551 # May 3rd, 2018
		},
		{
			"title":"Z9 Mini\nshipped",
			"timestamp": 1529668551 # June 22nd, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
		},
		{
			"title":"peak GPU\ndemand",
			"timestamp": 1518263751 # June 22nd, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
		}
	]
	allAxes = []
	if plotPph:
		pphAxes = fig.add_subplot("311")
		pphAxes.set_xticks([])
		pphAxes.set_ylabel("pay per hash\n($/GH)", fontproperties=getFont("Roboto-Medium", 11))
		allAxes.append(pphAxes)
	if plotProfit:
		profitAxes = fig.add_subplot("312")
		profitAxes.set_xticks([])
		profitAxes.set_ylabel("daily ROI\n(%)", fontproperties=getFont("Roboto-Medium", 11))
		allAxes.append(profitAxes)
	mons3 = 365/4.
	if plotPaybackTime:
		roiAxes = fig.add_subplot("313")	
		roiAxes.set_ylim(bottom=0, top=800)
		roiAxes.set_yticks([0, mons3, mons3*2, mons3*3, 365])
		roiAxes.set_yticklabels(["0", "3", "6", "9", "12"], fontproperties=getFont("Roboto-Regular", 9))
		roiAxes.set_ylabel("payback time\n(months)", fontproperties=getFont("Roboto-Medium", 11))
		roiAxes.set_xlabel("date", fontproperties=getFont("Roboto-Medium", 11))
		allAxes.append(roiAxes)

	bottomAxes = allAxes[0]
	topAxes = allAxes[-1]

	ptsList = getPts(symbols=symbols)
	
	timestamps, deviceStats, pphs = calculateDeviceProfitability(ptsList)

	if plotPph:
		maxPph = max(pphs)*1.05
		pphtick = 0
		pphTicks = []
		pphLabels = []
		print("maxPph: %i" % maxPph)
		while pphtick < maxPph:
			pphTicks.append(pphtick)
			pphLabels.append(str(pphtick))
			pphtick += 50
		print("maxTick: %i" % pphtick)
		pphTicks.append(pphtick)
		pphLabels.append(str(pphtick))
		pphLims = {
			"bottom":-5,
			"top":pphtick+5
		}
		pphAxes.set_yticks(pphTicks)
		pphAxes.set_yticklabels(pphLabels, fontproperties=getFont("Roboto-Regular", 9))
		pphAxes.set_ylim(**pphLims)

		pphAxes.plot(timestamps, pphs, color="#555555", linewidth=2)
		
	first, last = timestamps[0], timestamps[-1]

	xTicks, xLabels = getMonthTicks(first, last, addYear=addYear)
	
	minStamp = xTicks[0]
	maxStamp = xTicks[-1]
	stampRange = maxStamp-minStamp
	xLims = {
		"left":minStamp-0.05*stampRange,
		"right":maxStamp+0.05*stampRange
	}
	for ax in allAxes:
		ax.set_xlim(**xLims)
		ax.grid(b=None, which='major', axis='y', linewidth=1, color="#dddddd")
	while len(xTicks) > 8:
		xTicks = xTicks[::2]
		xLabels = xLabels[::2]
	bottomAxes.set_xticks(xTicks)
	bottomAxes.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 9))
	maxProfit = 0
	profitAxes.plot([minStamp-0.5*stampRange, maxStamp+0.5*stampRange],[0,0], linewidth=1, color="#cc7777")
	fillColors = {
		"GPU":"#1d33af18",
		"ASIC":"#84166c18"
	}
	for name, tiers in deviceStats.items():
		roiYs = {
			"lowend":[],
			"highend":[]
		}
		Ys = {
			"lowend":[],
			"highend":[]
		}
		xStamps = []
		for tier in ("lowend", "highend"):
			data = tiers[tier]
			for tRange, style, linewidth, stamps, vals in [unpackProfitLine(l) for l in data["range.lines"]]:
				vals = [x*100 for x in vals]
				maxProfit = max(maxProfit, max(vals))
				lastStamps = stamps
				Ys[tier].extend(vals)
				profitAxes.plot(stamps, vals, linestyle=style, color=data["color"], linewidth=linewidth)
			if plotPaybackTime:
				rois = [d["payback.days"] for d in data["roi.time"]]
				roiYs[tier].extend(rois)
				roiAxes.plot(data["timestamps"], rois, color=data["color"], linewidth=1)
		profitAxes.fill_between(data["timestamps"], Ys["lowend"], Ys["highend"], color=fillColors[name])
		if plotPaybackTime:
			roiAxes.fill_between(data["timestamps"], roiYs["lowend"], roiYs["highend"], color=fillColors[name])
	fig.canvas.draw()
	ylims = topAxes.get_ylim()
	pphTop = fig.transFigure.inverted().transform(topAxes.transData.transform([ylims[0],ylims[1]]))[1]
	if withEvents:
		for event in events:
			timestamp = event["timestamp"]
			title = event["title"]
			bttm = 0 if plotPaybackTime else -0.3
			bottomPt = fig.transFigure.inverted().transform(bottomAxes.transData.transform([timestamp,bttm]))
			topPt = [bottomPt[0], pphTop]
			line = matplotlib.lines.Line2D([bottomPt[0],topPt[0]], [bottomPt[1],topPt[1]], transform=fig.transFigure, linewidth=1, color="#00000055")# markerfacecolor="#1f77b4", marker="o",  markersize=4
			fig.lines.append(line)
			fig.text(bottomPt[0], pphTop, title, fontproperties=getFont("Roboto-Regular", 9), 
				horizontalalignment="center", verticalalignment="bottom")
	maxProfit = int(math.ceil(maxProfit))
	profitTicks = []
	profitLabels = []
	piterator = 0
	def appendpit(i, tcks=profitTicks, lbls=profitLabels):
		tcks.append(i)
		lbls.append(str(i))
	while piterator < maxProfit:
		appendpit(piterator)
		piterator +=2
	appendpit(piterator)
	profitAxes.set_yticks(profitTicks)
	profitAxes.set_yticklabels(profitLabels, fontproperties=getFont("Roboto-Regular", 9))
	profitAxes.set_ylim(bottom = -0.3, top=piterator+0.3)

	#circle = Ellipse(coords, width=0.02, height=0.03, facecolor="white", edgecolor="#555555", linewidth=2, transform=fig.transFigure, zorder=2)
	#fig.patches.append(circle)
	plt.show()

def plotThing(thing, start=None, end=None):
	fig = plt.gcf()
	ax = plt.gca()
	plt.subplots_adjust(0.25, 0.25, 0.90, 0.85, 0, 0.1)
	ptsList = getPts(start=start, end=end)

	if thing == "power":
		xTicks, xLabels = getMonthTicks(start, end, addYear=False)
		events = [
			{
				"title":"Z9 Mini release",
				"timestamp": 1529668551 # April 1st, 2018
			}
		]
	else:
		xTicks, xLabels = getMonthTicks(start, end)
		events = []
	minStamp = xTicks[0]
	maxStamp = xTicks[-1]
	stampRange = maxStamp-minStamp
	xLims = {
		"left":minStamp-0.05*stampRange,
		"right":maxStamp+0.05*stampRange
	}
	ax.set_xlim(**xLims)
	ax.set_xticks(xTicks)
	ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 9))
	ax.grid(b=None, which='major', axis='y', linewidth=1, color="#dddddd")
	timestamps, deviceStats, pphs = calculateDeviceProfitability(ptsList)
	maxProfit = 0
	ax.plot([minStamp-0.5*stampRange, maxStamp+0.5*stampRange],[0,0], linewidth=1, color="#cc7777")
	fillColors = {
		"GPU":"#1d33af18",
		"ASIC":"#84166c18"
	}
	hashrates = []
	if thing == "power":
		ax.set_xlabel("date", fontproperties=getFont("Roboto-Medium", 11))
		ax.set_ylabel("energy (GWh)", fontproperties=getFont("Roboto-Medium", 11))
	def calculateNetworkPower(deviceData, dayPt):
		print("%r" % repr([dayPt["hashrate"],deviceData["hashrate"],deviceData["power"],time.strftime("%Y-%m-%d", time.gmtime(dayPt["timestamp"]))]))
		return dayPt["hashrate"]/deviceData["hashrate"]*deviceData["power"]/1e9*24
	minY = 1e12
	maxY = 0
	if thing in ("profitability", "power"):
		for name, tiers in deviceStats.items():
			Ys = {
				"lowend":[],
				"highend":[]
			}
			for tier, data in tiers.items():
				for tRange, style, linewidth, stamps, vals in [unpackProfitLine(l) for l in data["range.lines"]]:
					if not vals:
						continue
					if thing == "profitability":
						vals = [x*100 for x in vals]
					elif thing == "power":
						pts = [pt for pt in ptsList if tRange[0] <= pt["timestamp"] < tRange[1]]
						vals = [calculateNetworkPower(data, pt) for pt in pts]
					minY = min(minY, min(vals))
					maxY = max(maxY, max(vals))
					Ys[tier].extend(vals)
					maxProfit = max(maxProfit, max(vals))
					ax.plot(stamps, vals, linestyle=style, color=data["color"], linewidth=1, zorder=10)
			ax.fill_between(data["timestamps"], Ys["lowend"], Ys["highend"], color=fillColors[name])
		if thing == "profitability":
			ax.set_yticks([0, 0.5, 1, 1.5, 2, 2.5])
			ax.set_yticklabels(["0", "0.5", "1", "1.5", "2", "2.5"], fontproperties=getFont("Roboto-Regular", 9))
	else:
		if thing == "hashrate":
			Ys = [pt["hashrate"] for pt in ptsList]
			minY = min(minY, min(Ys))
			maxY = max(maxY, max(Ys))
			print(repr(Ys[:-10]))
			Xs = [pt["timestamp"] for pt in ptsList]
			ax.plot(Xs, Ys, color="#555555", linewidth=1.5, zorder=1)
	yRange = maxY-minY
	ax.set_ylim(bottom=minY-0.1*yRange, top=maxY+0.1*yRange)
	for event in events:
		timestamp = event["timestamp"]
		ax.plot([timestamp, timestamp], [-1e12, 1e12], linewidth=1, color="#dddddd", zorder=1)
	# elif thing == "power":


	# maxProfit = int(math.ceil(maxProfit))
	# profitTicks = []
	# profitLabels = []
	# piterator = 0
	# def appendpit(i, tcks=profitTicks, lbls=profitLabels):
	# 	tcks.append(i)
	# 	lbls.append(str(i))
	# while piterator < maxProfit:
	# 	appendpit(piterator)
	# 	piterator +=2
	# appendpit(piterator)
	# ax.set_yticks(profitTicks)
	# ax.set_yticklabels(profitLabels, fontproperties=getFont("Roboto-Regular", 9))
	# ax.set_ylim(bottom = -0.5, top=piterator+0.3)

	plt.show()

def plotRetailCapital(symbols=None):
	symbols = symbols if symbols else ("ZEC", "BTG")
	

	events = [
		{
			"title":"ASIC\nrumors",
			"timestamp": 1522583751, # April 1st, 2018,
			"symbols":("BTG", "ZEC")
		},
		{
			"title":"Z9 Mini\nshipped",
			"timestamp": 1529668551, # June 22nd, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
			"symbols":("BTG", "ZEC")
		},
		{
			"title":"51%\nattack",
			"timestamp":1526662750,
			"symbols":("BTG",)
		},
		{
			"title":"fork to\n<144,5>",
			"timestamp":1530576000,
			"symbols":("BTG",)
		}
	]

	fig = plt.gcf()
	# ax = plt.gca()
	zecAx = fig.add_subplot("211")
	btgAx = fig.add_subplot("212")
	plt.subplots_adjust(0.25, 0.25, 0.90, 0.85, 0, 0.1)
	timePts = {}
	symbolLines = {}
	devices = deviceTemplates()

	colors = {
		"ZEC" : "#20208c",
		"BTG" : "#2b9613",
	}

	for symbol in symbols:
		nameLines = symbolLines[symbol] = {}
		with open(os.path.join("data","%s.json" % symbol), "r") as f:
			pts = json.loads(f.read())
		for timestamp, hashrate, dailyOut in pts:			
			for name, tiers in devices.items():
				if name not in nameLines:
					nameLines[name] = {}
				lines = nameLines[name]
				stats = tiers["highend"]
				rangeLines = stats["range.lines"]
				for i, profitLine in enumerate(rangeLines):
					tRange = profitLine["time.range"]
					if tRange[0] < timestamp < tRange[1]:
						if i not in lines:
							lines[i] = {
								"color":stats["color"],
								"linewidth":profitLine["linewidth"],
								"marker.style":profitLine["style"],
								"timestamps":[],
								"Ys":[]
							}
						line = lines[i]
						line["timestamps"].append(timestamp)
						dHashrate = stats["hashrate"]
						if symbol == "BTG" and name == "GPU" and timestamp > 1530679085:
							dHashrate = 56
						print(dHashrate)
						line["Ys"].append(hashrate/dHashrate*stats["price"]/1e6)
	xlims = {
		"left": mktime(2018, 4) - 5*86400,
		"right": mktime(2018, 10) + 5*86400
	}
		
	xTicks = []
	xLabels = []
	for year, month in ((2017, 10),(2018, 4),(2018, 6),(2018, 8),(2018, 10)):
		stamp = mktime(year, month)
		xTicks.append(stamp)
		xLabels.append(time.strftime("%b '%y", time.gmtime(stamp)))
	
	btgAx.set_xticks(xTicks)
	btgAx.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 9))
	btgAx.set_xlabel("date", fontproperties=getFont("Roboto-Medium", 11))
	zecAx.set_xticks([])
	for ax in (zecAx, btgAx):
		ax.set_xlim(**xlims)
	# zecAx.set_xticks([])
	yTicks = {
		"ZEC":list(range(0, 1001, 200)),
		"BTG":list(range(0, 31, 10))
	}
	yLims = {
		"ZEC":{
			"bottom":-50,
			"top":1050
		},
		"BTG":{
			"bottom":-3,
			"top":33
		}
	}
	fig.canvas.draw()
	for symbol, ax in (("ZEC", zecAx), ("BTG", btgAx)):
		nameLines = symbolLines[symbol]
		maxY = 0
		for name, lines in nameLines.items():
			if name == "GPU" and symbol == "BTG":
				# and timestamp > 1529668551:
				# if timestamp < 1526662750:
				ogLine = lines[0]
				pts = list(zip(ogLine["timestamps"], ogLine["Ys"]))
				#Before ASICS
				ts, ys = zip(*[(t,y) for t,y in pts if t < 1529668551])
				maxY = max(maxY, max(ys))
				ax.plot(ts, ys, linewidth=1.5, linestyle="-", color=ogLine["color"], zorder=10)
				#After ASICS
				ts, ys = zip(*[(t,y) for t,y in pts if 1529668551 <= t < 1530576000])
				print("BTG network device value at fork, %.2f" % ys[-1])
				maxY = max(maxY, max(ys))
				ax.plot(ts, ys, linewidth=1.5, linestyle=":", color=ogLine["color"], zorder=10)
				#After Fork
				ts, ys = zip(*[(t,y) for t,y in pts if t >= 1530576000])
				maxY = max(maxY, max(ys))
				ax.plot(ts, ys, linewidth=1.5, linestyle="-", color=ogLine["color"], zorder=10)
			elif name == "GPU":
				ogLine = lines[0]
				pts = list(zip(ogLine["timestamps"], ogLine["Ys"]))
				#Before ASICS
				ts, ys = zip(*[(t,y) for t,y in pts if t < 1529668551])
				maxY = max(maxY, max(ys))
				ax.plot(ts, ys, linewidth=1.5, linestyle="-", color=ogLine["color"], zorder=10)
				#After ASICS
				ts, ys = zip(*[(t,y) for t,y in pts if t >= 1529668551])
				maxY = max(maxY, max(ys))
				ax.plot(ts, ys, linewidth=1.5, linestyle=":", color=ogLine["color"], zorder=10)
			else: # ASIC
				if symbol == "BTG":
					# remove ASIC pts older than the fork
					ogLine = lines[2]
					pts = list(zip(ogLine["timestamps"], ogLine["Ys"]))
					ogLine["timestamps"], ogLine["Ys"] = zip(*[(t,y) for t,y in pts if t < 1530576000])
					print("Last BTG ASIC device value before fork: %.2f" % ogLine["Ys"][-1])
				if symbol == "ZEC":
					ogLine = lines[2]
					prerelease = lines[1]
					print("ZEC ASIC network captial at release %.2f" % prerelease["Ys"][-1])
					print("Last ZEC ASIC device value: %.2f" % ogLine["Ys"][-1])
				for i, line in lines.items():
					ys = line["Ys"]
					maxY = max(maxY, max(ys))
					# minY = min(minY, min(ys))
					ax.plot(line["timestamps"], ys, linewidth=2, linestyle=line["marker.style"], color=line["color"], zorder=10)
		maxY = int(math.ceil(maxY/100)*100)
		ax.set_yticks(yTicks[symbol])
		ax.set_yticklabels([str(y) for y in yTicks[symbol]])
		ax.set_ylabel("network device\nvalue ($M)", fontproperties=getFont("Roboto-Medium", 11))
		ylims = yLims[symbol]
		for event in events:
			if symbol not in event["symbols"]:
				continue
			timestamp = event["timestamp"]
			ax.plot([timestamp, timestamp], [ylims["bottom"], ylims["top"]], linewidth=1, color="#dddddd", zorder=1)
			# topPt = fig.transFigure.inverted().transform(ax.transData.transform([timestamp,ylims["top"]]))
			# fig.text(topPt[0], topPt[1], event["title"], fontproperties=getFont("Roboto-Regular", 9), 
			# 	horizontalalignment="center", verticalalignment="bottom")
		ax.set_ylim(**ylims)

	plt.show()

def plotEnergyCurves():
	deviceStats = deviceTemplates()
	fig = plt.gcf()
	ax = plt.gca()
	plt.subplots_adjust(0.25, 0.25, 0.90, 0.85, 0, 0.1)
	colors = {
		"ASIC":{
			"highend":"red",
			"lowend":"orange"
		},
		"GPU":{
			"highend":"blue",
			"lowend":"green"
		}
	}
	for name, tiers in deviceStats.items():
		for tier, data in tiers.items():
			relCost = data["price"]/data["hashrate"]
			beta = 86400/150*10
			efficiency = data["hashrate"]/data["power"]
			print("efficiency: %.")
			desiredRoi = 0.005 # 0.5%
			energyRate = 0.10 # 10 cents/kWH
			exchangeRate = 140
			# nethash = beta*exchangeRate/(desiredRoi*relCost+0.024*energyRate/efficiency)
			# print("nethash: %i" % nethash)
			# totalPower = beta*exchangeRate/(efficiency*relCost*desiredRoi + 0.024*energyRate)
			# totalEnergy = totalPower*24
			print("%s %s device factor: %f" % (tier, name, relCost*efficiency))
	# 		def totNrg(exchangeRate):
	# 			return 24*beta*exchangeRate/(efficiency*relCost*desiredRoi + 0.024*energyRate)
	# 		Xs = list(range(100,501))
	# 		Ys = [totNrg(exr) for exr in range(100, 501)]
	# 		ax.plot(Xs, Ys, color=colors[name][tier])
			
			# def pwrNrg(rate):
			# 	return 24*beta*exchangeRate/(efficiency*relCost*desiredRoi + 0.024*rate)
			# Xs = list(range(5,25))
			# Ys = [pwrNrg(centRate/100) for centRate in Xs]
			# ax.plot(Xs, Ys, color=colors[name][tier])

	plt.show()

BLOCK_NINJA = None
def getBlockNinja():
	global BLOCK_NINJA
	if BLOCK_NINJA:
		return BLOCK_NINJA
	BLOCK_NINJA = BlockNinja()
	BLOCK_NINJA.msgCallback = lambda s: print(s)
	for symbol, info in symbolInfo.items():
		BLOCK_NINJA.registerNode(
			symbol, 
			info["rpc.protocol"], 
			nodepath=info["node.path"], 
			port=info["port"], 
			name=info["name"], 
			password=info["password"], 
			customArgs=info["custom.args"],
			genesisHeight=info["genesis.height"] if "genesis.height" in info else 0
			)
		BLOCK_NINJA.setNodeRemote(symbol)
	return BLOCK_NINJA

# MINER_STATS_PATH = "%s-miner-stats"

def makeDumpPath(dataDir, t, extension="json"):
	y,m,d = yearmonthday(t)
	dirpath = os.path.join(dataDir, str(y).zfill(2))
	mkdir(dirpath)
	dirpath = os.path.join(dirpath, str(m).zfill(2))
	mkdir(dirpath)
	return os.path.join(dirpath, "%s.%s" % (str(d).zfill(2), extension))

def dumpExists(dataDir, t, extension="json"):
	return os.path.isfile(makeDumpPath(dataDir, t, extension))

# def fetchDump(dataDir, t):
# 	with open(makeDumpPath(dataDir, t)) as f:
# 		return json.loads(f.read())

def iterateYearMonth(year, month, steps=1):
	if steps > 0:
		for _ in range(steps):			
			month += 1
			if month == 13:
				year += 1
				month = 1
	elif steps < 0:
		for _ in range(-steps):
			month -= 1
			if month == 0:
				year -= 1
				month = 12
	return year, month	

def getMinerStats(symbol):
	protocol = symbolInfo[symbol]["rpc.protocol"]
	prevBlkMethod = "parentHash" if protocol == "eth" else "previousblockhash"
	blockNinja = getBlockNinja()
	node = blockNinja.nodes[symbol]

	tip = blockNinja.getTip(symbol)
	mkdir(WALLET_COUNT_DIR)
	symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
	mkdir(symbolDir)
	year, month, day = yearmonthday(tip["time"])
	nextDump = mktime(year, month, day) - 86400
	while dumpExists(symbolDir, nextDump):
		print("skipping %i-%i-%i" % yearmonthday(nextDump))
		nextDump -= 86400

	block = blockNinja.getLastBlockOfDay(symbol, *yearmonthday(nextDump))
	counts = {}	
	while block["height"] > node.genesisHeight:
		print("checking block at height %i on %s" % (block["height"], time.strftime("%b %d %y", time.gmtime(block["time"]))))
		if block["time"] < nextDump:
			dirpath = os.path.join(WALLET_COUNT_DIR, symbol)
			mkdir(dirpath)
			year, month, day = yearmonthday(nextDump)
			for sub in (year, month):
				dirpath = os.path.join(dirpath, str(sub).zfill(2))
				mkdir(dirpath)
			filepath = os.path.join(dirpath, "%s.json" % str(day).zfill(2))
			with open(filepath, "w") as f:
				print("writing to %s" % filepath)
				f.write(json.dumps(counts))
			counts.clear()
			nextDump -= 86400 # may use iterateDump here in the future, Will need to 
			if dumpExists(symbolDir, nextDump):
				nextDump -= 86400
				while dumpExists(symbolDir, nextDump):
					nextDump -= 86400
				block = blockNinja.getLastBlockOfDay(symbol, nextDump, *yearmonthday(nextDump))
				if not block:
					exit("error1853: %s" % str(block))
		address = blockNinja.getMinerAddress(symbol, block)
		if not address:
			print(json.dumps(address, indent=4))
			exit("no address")
		if address in counts:
			counts[address] += 1
		else:
			counts[address] = 1
		block = blockNinja.iterateBlock(symbol, block, -1)
	# with open(MINER_STATS_PATH % symbol, "wb") as f:
	# 	pickle.dump(sorted(counts.items(), key=lambda tup:tup[1], reverse=True), f, pickle.HIGHEST_PROTOCOL)

def getFirstDay(dataDir):
	for year in range(2015, 2020):
		yearDir = os.path.join(dataDir, str(year))
		if os.path.isdir(yearDir):
			for month in range(1, 13): 
				monthDir = os.path.join(yearDir, str(month).zfill(2))
				if os.path.isdir(monthDir):
					for day in range(1, 35):
						dayPath = os.path.join(monthDir, "%s.json" % str(day).zfill(2))
						if os.path.isfile(dayPath):
							return mktime(year, month, day)
	return False

def getLastDay(dataDir):
	for year in range(2019, 2014, -1):
		yearDir = os.path.join(dataDir, str(year))
		if os.path.isdir(yearDir):
			for month in range(12, 0, -1): 
				monthDir = os.path.join(yearDir, str(month).zfill(2))
				if os.path.isdir(monthDir):
					for day in range(31, 0, -1):
						dayPath = os.path.join(monthDir, "%s.json" % str(day).zfill(2))
						if os.path.isfile(dayPath):
							return mktime(year, month, day)
	return False

def timelinesTemplate():
	return {
		"BTG" : {
			"start":1510663427,
			"end":0,
			"transitions":[],
			"events":[
				{
					"title":"ASIC rumors",
					"timestamp": 1522583751, # April 1st, 2018
					"active": False
				},
				{
					"title":"ASIC confirmed",
					"timestamp": 1525348551, # May 3rd, 2018
					"active": False,
					"y.offset":-1.8,
					"x.offset":-3
				},
				{
					"title":"ASIC ships",
					"timestamp": 1529668551, # June 22nd, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
					"active": True,
					"x.offset":-2.2
				},
				{
					"title":"51% attack",
					"timestamp":1526662750,
					"active": False,
					"y.offset":-3.6,
				},
				{
					"title":"fork to <144,5>",
					"timestamp":1530576000,
					"symbols":("BTG",),
					"active": True,
					"y.offset":-1.8,
				}
			]
		},
		"ZEC" : {
			"start":1477745027,
			"end":0,
			"transitions":[],
			"events":[
				{
					"title":"ASIC rumors",
					"timestamp": 1522583751, # April 1st, 2018
					"active": False,
					"x.offset":-2
				},
				{
					"title":"ASIC confirmed",
					"timestamp": 1525348551, # May 3rd, 2018
					"active": False,
					"y.offset":-2,
				},
				{
					"title":"ASIC shipped",
					"timestamp": 1529668551, # June 22nd, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
					"active": True,
					"x.offset":2
				}
			]
		},
		"ETH" : {
			"start":1524833027,
			"end":0,
			"transitions":[],
			"events":[
				{
					"title":"DAO fork",
					"timestamp": mktime(2016, 7, 20),
					"active": False
				},
				# {
				# 	"title":"ASIC rumors",
				# 	"timestamp": 1522166075, # March 27th, 2018
				# 	"x.offset":-2
				# },
				{
					"title":"Metropolis",
					"timestamp": 1508131331,
					"active": False
				},
				{
					"title":"ASIC confirmed",
					"timestamp": 1522770875, # April 3rd, 2018
					"active": False,
					"y.offset":-1.8
				},
				{
					"title":"ASIC shipped",
					"timestamp": 1531756475, # July 16th, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
					"active": True
				}
			]
		},
		"ETC" : {
			"start":0,
			"end":0,
			"transitions":[],
			"events":[
				# {
				# 	"title":"ASIC\nrumors",
				# 	"timestamp": 1522166075 # March 27th, 2018
				# },
				{
					"title":"Block 5M",
					"timestamp": 1513013050,
					"active": False
				},
				{
					"title":"ASIC\nconfirmed",
					"timestamp": 1522770875, # April 3rd, 2018
					"active": False
				},
				{
					"title":"ASIC\nshipped",
					"timestamp": 1531756475, # July 16th, 2018 from https://thebitcoin.pub/t/the-z9s-have-landed/42659
					"active": True
				}
			]
		}
	}

def calculateNakamoto(counts):
	# https://news.earn.com/quantifying-decentralization-e39db233c28e
	propCounter = 0.
	numMiners = 0
	for prop in counts:
		propCounter += prop
		numMiners += 1
		if propCounter > 0.5:
			break
	return numMiners

class NetworkPlotter:
	def __init__(self, figure, figSize, aspectRatio=None):
		with open("transitions.json", "r") as f:
			self.timelines = json.loads(f.read())
		self.fig = figure
		self.figSize = figSize
		self.colorMap = matplotlib.cm.get_cmap('jet')
		self.aspectRatio = aspectRatio if aspectRatio else 9/16.
		self.minFontSize = 6
		self.fontScaleFactor = 1
		self.pctScaler = 10
		self.offsetFactor = 0.5
		self.showName = True
		self.showNakamoto = True
		self.setPadding(0.20)
	def setPadding(self, hPad):
		self.hPad = hPad
		figSize = self.figSize
		w, h = figSize
		horiPadding = hPad*w
		W = w+2*horiPadding
		H = self.aspectRatio*W
		vertPadding = (H - h)/2
		self.ylims = {
			"bottom":-vertPadding*1.,
			"top":figSize[1]+vertPadding*1.
		}
		self.xlims = {
			"left":-horiPadding,
			"right" : figSize[0]+horiPadding

		}
	def inverseColor(self, color):
		# return [1.-c for c in color[:3]] + list(color[3:])
		return "white" if sum(color[:3]) < 1.5 else "#555555"
	def colorFunc(self, val):
		color = self.colorMap(val+0.5)
		return color, self.inverseColor(color)
	def walletFormatter(self, wallet, w):
		headLen, tailLen = self.headtail(w)
		if len(wallet) >  headLen + tailLen:
			return wallet[:headLen] + ".." + wallet[-tailLen:]
		return wallet
	def headtail(self, width):
		chars = int(width-30)/55*24+10
		head = int(chars/2)
		tail = chars = head
		return head, tail
	def createAxes(self, symbol, position):
		timeline = self.timelines[symbol]
		if not timeline["transitions"]:
			return False
		ax = self.fig.add_subplot(position)
		for direction in ax.spines:
			ax.spines[direction].set_visible(False)
		ax.symbol = symbol
		ax.img = Image.open("/home/buck/websites/strataminer/images/%s-100.png" % symbol)
		ax.longName = symbolInfo[symbol]["long.name"]
		ax.timeline = timeline
		ax.numTransitions = len(timeline["transitions"])
		ax.set_xticks([])
		ax.set_yticks([])
		timeline["ax"] = ax
		return ax
		# resetAxes(ax, 0, 1)
	def resetAxes(self, ax, progress, nakamoto):
		figSize = self.figSize
		ax.clear()
		ax.set_xticks([])
		ax.set_yticks([])
		ax.set_ylim(**self.ylims)
		ax.set_xlim(**self.xlims)
		if self.showName:
			ax.imshow(ax.img, extent=(1, 9, 104, 112), zorder=3, interpolation="lanczos")
			ax.text(11.5, 103, ax.longName, fontproperties=getFont("EBGaramond-Medium", 20), horizontalalignment="left", verticalalignment="bottom")
		if self.showNakamoto:
			ax.text(200, 104, "Nakamoto coefficient: %s" % str(int(nakamoto)), fontproperties=getFont("RobotoMono-Regular", 15), horizontalalignment="right", verticalalignment="bottom")

		if progress is False:
			return 
		offset = -17
		left, right = 0, figSize[0]
		start = ax.timeline["start"]
		end = ax.timeline["end"]
		tDelta = end - start
		progressEnd = progress*right
		ax.plot([left,progressEnd], [offset, offset], linewidth=4, color="#4c8dff99", zorder=3)
		ax.plot([progressEnd,right], [offset, offset], linewidth=4, color="#00000066", zorder=3)
		ax.plot(progressEnd, offset, marker="o", markersize=11, markerfacecolor="#4c8dff", markeredgewidth=0, zorder=4)
		# ax.plot(left, offset, marker="o", markersize=10, markerfacecolor="#555555", markeredgewidth=0)
		# ax.plot(right, offset, marker="o", markersize=10, markerfacecolor="#555555", markeredgewidth=0)
		for event in ax.timeline["events"]:
			tEvent = event["timestamp"]
			if tEvent < start:
				continue
			x = (tEvent-start)/tDelta*right
			title = event["title"]
			yOffset = event["y.offset"]*3 if "y.offset" in event else 0
			xOffset = event["x.offset"]*3 if "x.offset" in event else 0
			ax.plot([x,x], [offset+1, offset-2+yOffset], linewidth=3, color="#555555")
			ax.text(x+xOffset, offset-4+yOffset, title, fontproperties=getFont("Roboto-Regular", 11), horizontalalignment="center", verticalalignment="top")
		
		m,d,y = time.strftime("%b %d %y", time.gmtime(start)).split()
		timeString = "%s/%s '%s" % (m.lstrip("0"), d.lstrip("0"), y)
		ax.text(2.5, offset+3, timeString, fontproperties=getFont("Roboto-Medium", 12), horizontalalignment="right", verticalalignment="bottom")
		year, month, _ = yearmonthday(start)
		stamp = 0
		stepSize = int(math.ceil((end-start)/(365*86400)))
		while (month-1)%stepSize:
			year, month = iterateYearMonth(year, month)
		while stamp < end:
			oldYear = year
			year, month = iterateYearMonth(year, month, stepSize)
			newYear = year != oldYear
			if newYear:
				yearStamp = mktime(year)
				yearX = (yearStamp-start)/tDelta*right
				ax.plot([yearX, yearX], [offset-1, offset+1.5], linewidth=2, color="#555555")
			stamp = mktime(year, month)
			if stamp > end-28*86400*stepSize/2:
				break
			x = (stamp-start)/tDelta*right
			tFormat = "%Y" if newYear else "%b"
			fontfamily = "Roboto-Medium" if newYear else "Roboto-Regular"
			fontsize = 12 if newYear else 11
			timeStr = time.strftime(tFormat, time.gmtime(stamp))
			ax.text(x, offset+2, timeStr, fontproperties=getFont(fontfamily, fontsize), horizontalalignment="center", verticalalignment="bottom")
			ax.plot([x,x], [offset-1.5, offset+1.5], linewidth=1.5, color="#555555")
		m,d,y = time.strftime("%b %d %y", time.gmtime(end)).split()
		timeString = "%s/%s '%s" % (m.lstrip("0"), d.lstrip("0"), y)
		ax.text(right-2.5, offset+3, timeString, fontproperties=getFont("Roboto-Medium", 12), horizontalalignment="left", verticalalignment="bottom")
	def plotValues(self, ax, tStamp, values, progress):
		self.resetAxes(ax, progress, calculateNakamoto([v for v,w in values]))
		topLeft = (0,0)
		figSize = self.figSize
		area = (figSize[0] - topLeft[0])*(figSize[1] - topLeft[1])
		maxSquares = 1e9 # used for testing. will probably remove
		i = 0
		pad = 0.5
		pad2 = 2*pad
		valSum = 0
		texts = []
		valueBoxes = []
		for value, wallet in values:
			i += 1
			valSum += value
			if i > maxSquares:
				break
			if value <= 0.01:
				break
			width = figSize[0] - topLeft[0]
			height = figSize[1] - topLeft[1]
			if width == 0 or height == 0:
				break
			winc = hinc = 0
			if width >= height:
				#fill height first, then width
				tl = tuple(x+pad for x in topLeft)
				w = value*area/height
				h = height
				winc  = w
			else:
				tl = tuple(x+pad for x in topLeft)
				h = value*area/width
				w = width
				hinc = h
				separator = "\n"
			if w > pad2 + 2 and h > pad2 + 2:
				topLeft = (topLeft[0]+winc, topLeft[1]+hinc)
				color, fontcolor = self.colorFunc(value)

				# if two rows, set rH to height of 

				rH = (min(h-2, w, 50)-5)/20

				appender = False
				if w > 25 and h > 25:
					appender = "\n%s" % self.walletFormatter(wallet, w)
					fontsize = self.minFontSize + min(w,h)/2/100*self.pctScaler
				elif w > 40 and h > 10:
					appender = " - %s" % self.walletFormatter(wallet, w)
					fontsize = self.minFontSize + min(w,h)/100*self.pctScaler
				elif h > 40 and w > 20:
					appender = "\n%s" % self.walletFormatter(wallet, w)
					fontsize = self.minFontSize + min(w,h)/2/100*self.pctScaler
				elif h > 7 and w > 7:
					appender = ""
					fontsize = self.minFontSize + min(w,h)/100*self.pctScaler
				if appender is not False:
					# pctFontSize = self.minFontSize+self.pctScaler*rH
					pct = value*100
					if w > 25:
						if pct >= 9.5:
							pctFormat = "%i%%"
						else:
							pctFormat = "%.1f%%"
					else:
						if pct >= 9.5:
							pctFormat = "%i"
						else:
							pctFormat = "%.1f"
					texts.append({
						"text" : "%s%s" % (pctFormat % pct, appender),
						"pt": (tl[0]+w/2, tl[1]+h/2), 
						"fontsize" : fontsize,
						"fontcolor": fontcolor,
						"fontfamily":"Roboto-Medium"
					})

				



				# if h > 7 and w > 5:
					
				# 	offset = 0
				# 	if w > 20 and h > 10:
				# 		r = (min(h,50)-15)/35
				# 		offset = 1
				# 		texts.append({
				# 			"text" : self.walletFormatter(wallet, w),
				# 			"pt": [center[0], center[1]-3-3*r], 
				# 			"fontsize" : self.minFontSize + (w-5)/40*self.fontScaleFactor + rH*0.5,
				# 			"fontcolor": "#555555" if sum(color[:3]) >= 1.5 else "white",
				# 			"fontfamily":"RobotoMono-Medium"
				# 		})
				# 	offset += rH*self.offsetFactor
				# 	pctFontSize = self.minFontSize+self.pctScaler*rH
				# 	pct = value*100
				# 	if w > 15:
				# 		if pct >= 10:
				# 			pctFormat = "%i%%"
				# 		else:
				# 			pctFormat = "%.1f%%"
				# 	else:
				# 		if pct >= 10:
				# 			pctFormat = "%i"
				# 		else:
				# 			pctFormat = "%.1f"
					
				rectangle = Rectangle(tl, w-pad2, h-pad2, facecolor=color, edgecolor="#555555", linewidth=1)
			else:
				break
			ax.add_patch(rectangle)
		for box in texts:
			txt = box["text"]
			pt = box["pt"]
			fontsize = box["fontsize"]
			fontcolor = box["fontcolor"]
			fontfamily = box["fontfamily"]
			ax.text(int(pt[0]), int(pt[1]), txt, fontproperties=getFont(fontfamily, fontsize), color=fontcolor,
				horizontalalignment="center", verticalalignment="center")
		tl = tuple(x+pad for x in topLeft)
		width = figSize[0] - topLeft[0]
		height = figSize[1] - topLeft[1]
		# print("valSum: %f" % valSum)
		if width-pad2 > 0 and height-pad2 > 0:
			rectangle = Rectangle(tl, width-pad2, height-pad2, facecolor=self.colorFunc(0)[0], edgecolor="#555555", linewidth=1, hatch="x")
		ax.add_patch(rectangle)


def plotMinerStats(symbols, rebuild=False, startFrame=None, endFrame=None, snapshot=False, framesPerDay=4, averagingLength=7):
	# with open(MINER_STATS_PATH % symbol, "wb") as f:
	# 	counts = pickle.load(f)

	def getAccompliceCount(counts):
		rawCounts = [c for w, c in sorted(counts.items(), key=lambda tup: tup[1], reverse=True)]
		halfBlocks = sum(rawCounts)/2. # must be float
		blockCounter = 0
		numMiners = 0
		while blockCounter < halfBlocks:
			blockCounter += rawCounts.pop(0)
			numMiners += 1
		return numMiners
	def combineCounts(*countsList):
		cs = countsList[0]
		for counts in countsList[1:]:
			for k, v in counts.items():
				if k in cs:
					cs[k] += v
				else:
					cs[k] = v
		return cs

	if rebuild:
		timelines = timelinesTemplate()
		
		for symbol, timeline in timelines.items():
			timeline["start"] = getFirstDay(os.path.join(WALLET_COUNT_DIR, symbol))
			
		blockNinja = getBlockNinja()

		daoStamp = mktime(2016, 7, 20)

		lastDay = mktime(*yearmonthday(time.time()))
		for symbol in symbols:
			lastDay = min(lastDay, getLastDay(os.path.join(WALLET_COUNT_DIR, symbol)))
		for symbol in symbols:
			timeline = timelines[symbol]
			symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
			# firstBlock = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(timeline["start"]))	
			startSet = False
			dayIterator = mktime(*yearmonthday(timeline["start"]+86400))
			frames = []
			dayBuffer = []
			while dayIterator < lastDay:
				if symbol == "ETC" and dayIterator < daoStamp:
					dayIterator += 86400
					continue
				# weekCounts = {}
				# for days in range(1, 8):
				# 	dayStamp = dayIterator + days*86400
				# 	if dayStamp >= lastDay:
				# 		break

				# 	if not dumpExists(symbolDir, dayStamp):
				# 		print("No file at %i-%i-%i. Assuming complete." % yearmonthday(dayIterator))
				# 		time.sleep(2)
				# 		dayIterator = 1e12
				# 		break
				# 	timeline["end"] = dayStamp
				# 	with open(makeDumpPath(symbolDir, dayStamp), "r") as f:
				# 		combineCounts(weekCounts, json.loads(f.read()))
				dayCounts = {}

				if not dumpExists(symbolDir, dayIterator):
					print("No file at %i-%i-%i. Assuming complete." % yearmonthday(dayIterator))
					time.sleep(2)
					dayIterator = 1e12
					break
				timeline["end"] = dayIterator
				with open(makeDumpPath(symbolDir, dayIterator), "r") as f:
					dayBuffer.append(json.loads(f.read()))
					if len(dayBuffer) == averagingLength:
						dayCounts = combineCounts(*dayBuffer)
						dayBuffer.pop(0)
				if dayIterator >= lastDay:
					break
				dayIterator += 86400
				if dayCounts:
					if not startSet:
						timeline["start"] = dayIterator
						startSet = True
					frame = {
						"timestamp":dayIterator,
						"counts":dayCounts
					}
					frames.append(frame)

			frameCount = len(frames)
			transitions = timeline["transitions"]
			for frameIndex, frame in enumerate(frames):
				dayCounts = frame["counts"]
				if frameIndex == frameCount - 1:
					break
				print("Creating transition %s:%i->%i" % (symbol, frameIndex, frameIndex+1))
				nextFrame = frames[frameIndex+1]
				nextDayCounts = nextFrame["counts"]
				pts = sorted(dayCounts.items(), key=lambda tup: tup[1], reverse=True)
				count = sum([pt[1] for pt in pts])
				nextPts = sorted(nextDayCounts.items(), key=lambda tup: tup[1], reverse=True)
				nextCount = sum([pt[1] for pt in nextPts])
				nextLen = len(nextPts)
				transition = []
				for minerIndex, pt in enumerate(pts):
					if nextLen <= minerIndex:
						transition.append((pt[1]/count, pt[0], 0, None))
						continue
					nextPt = nextPts[minerIndex]
					transition.append((pt[1]/count, pt[0], nextPt[1]/nextCount, nextPt[0]))
				minerIndex += 1
				while minerIndex < nextLen:
					nextPt = nextPts[minerIndex]
					transition.append((0, None, nextPt[1]/nextCount, nextPt[0]))
					minerIndex += 1
				transitions.append((frame["timestamp"], nextFrame["timestamp"], transition))
		with open("transitions.json", "w") as f:
			f.write(json.dumps(timelines))

	
	# plt.ion()
	plt.ticklabel_format(useOffset=False, axis="both")
	plt.cla()
	plt.clf()
	fig = plt.gcf()
	subplotAdjustments = {
		"left":0,
		"right":1,
		"bottom":0,
		"top":1,
		"wspace":0,
		"hspace":0
	}
	fig.subplots_adjust(**subplotAdjustments)
	dpi = 100
	fig.set_dpi(dpi)
	figSize = (19.2, 10.8)
	fig.set_size_inches(*figSize)
	pxCounts = tuple(x*dpi for x in figSize)
	# Primary plot and line

	plotter = NetworkPlotter(fig, (200,100))
	plotter.setPadding(0.40)
	plotter.minFontSize = 2
	plotter.showName = True
	plotter.showNakamoto = True
	plotter.pctScaler = 60
	plotter.offsetFactor = 3
	plotter.walletFormatter = lambda a, w: a[-4:]

	axes = []
	maxTransitions = 0
	for plotIndex, symbol in enumerate(["ETH", "ETC", "ZEC", "BTG"]):
		ax = plotter.createAxes(symbol, "22%i" % (plotIndex+1))
		if not ax:
			continue
		maxTransitions = max(maxTransitions, ax.numTransitions)
		axes.append(ax)		
	fig.canvas.draw()

	# transFigure = fig.transFigure.inverted()
	# firstTransition = transitions[0]
	# initialValues = [prop1 for name1, prop1, name2, prop2 in firstTransition]
	# rectangles = []
	# xy = transFigure.transform(ax.transData.transform([0, bottomRight[1]]))
	# imgXy = [x*y for x,y in zip(xy, pxCounts)]
	# img = Image.open(imgTemplate % symbol)
	# fig.figimage(np.array(img), imgXy[0], imgXy[1], origin="upper")
	# fig.text(xy[0]+105/pxCounts[0], xy[1]+12/pxCounts[1], "ZCash", fontproperties=getFont("EBGaramond-Medium", 50), horizontalalignment="left", verticalalignment="bottom")
	outpath = "decentralization_%iday_%iper.mp4" % (averagingLength, framesPerDay)
	writer = imageio.get_writer(outpath, mode='I', fps=30., macro_block_size=None)
	startFrame = startFrame if startFrame and startFrame > 0 else 0
	endFrame = endFrame if endFrame and endFrame < maxTransitions else maxTransitions
	if snapshot or snapshot is 0:
		startFrame = snapshot
		endFrame = snapshot+1
		print("TAKING SHAPSHOT AT FRAME %i" % snapshot)
	print(startFrame)
	print(endFrame)
	for transitionIndex in range(startFrame, endFrame):
		print("plotting transition %i->%i" % (transitionIndex, transitionIndex+1))
		for frameIndex in range(framesPerDay):
			for ax in axes:
				# if transitionIndex > 100:
				# 	break
				symbol = ax.symbol
				timeline = ax.timeline
				ax = timeline["ax"]
				firstTransition = maxTransitions - ax.numTransitions
				if transitionIndex < firstTransition:
					continue
				symbolIndex = transitionIndex - firstTransition
				symbolStart = timeline["start"]
				symbolEnd = timeline["end"]
				symbolDelta = symbolEnd-symbolStart
				tStart, tStop, transition = timeline["transitions"][symbolIndex]
				initialValues = [prop1 for prop1, name1, prop2, name2 in transition]
				endValues = [prop2 for prop1, name1, prop2, name2 in transition]
				complete = frameIndex/framesPerDay
				tStamp = tStart + (tStop-tStart)*complete
				progress = (tStamp-symbolStart)/symbolDelta
				vals = [(prop1+complete*(prop2-prop1), name1 if complete < 0.5 else name2) for prop1, name1, prop2, name2 in transition]
				plotter.plotValues(ax, tStamp, [(prop1+complete*(prop2-prop1), name1 if complete < 0.5 else name2) for prop1, name1, prop2, name2 in transition], progress)
			fig.canvas.draw()
			if snapshot or snapshot is 0:
				path = "snapshot_%i.png" % snapshot
				plt.savefig(path, dpi=dpi)
				exit("Snapshot saved to %s. Exiting" % path)
			ncols, nrows = fig.canvas.get_width_height()
			writer.append_data(np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='').reshape(nrows, ncols, 3))
	writer.close()
	print("File saved to %s" % outpath)
	exit()

def followTheMoney(symbol, startStamp, endStamp=None, integrationLength=7):
	endStamp = endStamp if endStamp else time.time()
	dataDir = "pay-tracking"
	mkdir(dataDir)
	symbolDir = os.path.join(dataDir, symbol)
	mkdir(symbolDir)
	blockNinja = getBlockNinja()
	dayStamp = mktime(*yearmonthday(startStamp))
	while dumpExists(symbolDir, dayStamp):
		print("skipping %i-%i-%i" % yearmonthday(dayStamp))
		dayStamp += 86400
	nextDay = dayStamp+86400
	endStamp = mktime(*yearmonthday(endStamp))+86400
	# collectionEnd = dayStamp + 86400
	block = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(dayStamp))
	days = [{
		"stamp":dayStamp,
		"miners":{}
	}]
	info = symbolInfo[symbol]
	while True:
		if block["time"] >= nextDay:
			if len(days) == integrationLength:
				day = days.pop(0)
				stamp = day["stamp"]
				miners = day["miners"]
				for name, miner in miners.items():
					miner["payees"] = len(miner["payees"])
					miner["total.out"] = miner["total.out"]/1e18
				year, month, day = yearmonthday(stamp)
				dirpath = symbolDir
				for sub in (year, month):
					dirpath = os.path.join(dirpath, str(sub).zfill(2))
					mkdir(dirpath)
				with open(os.path.join(dirpath, "%s.json" % str(day).zfill(2)), "w") as f:
					f.write(json.dumps(miners, indent=4, sort_keys=True))
			dayStamp += 86400
			if dayStamp >= endStamp:
				break
			nextDay += 86400
			days.append({
				"stamp":dayStamp,
				"miners":{}
			})
		minerAddress = blockNinja.getMinerAddress(symbol, block)
		for miners in [day["miners"] for day in days]:			
			if minerAddress not in miners:
				miners[minerAddress] = {
					"blocks": 0,
					"total.in": 0,
					"total.out": 0,
					"transactions":0,
					"payees":set() # To be saved as just a length before saving
				}
			miners[minerAddress]["total.in"] += info["block.reward"](block["height"])
			miners[minerAddress]["blocks"] += 1
				# outputs = minerOutputs[miner]
			for transaction in block["transactions"]:
				if transaction["from"] in miners:
					miner = miners[transaction["from"]]
					miner["payees"].add(transaction["to"])
					value = int(transaction["value"], 0)
					miner["total.out"] += value
					miner["transactions"] += 1
		block = blockNinja.iterateBlock(symbol, block, 1)
		if not block:
			print("block error: %r" % block)
			break
		# Below is ZCash code that doesn't work, possibly
		# because tAddress payouts are immediately exchanged to zAddresses or something. Not sure.
	# def findCoinbase(txid):
	# 	for miner, txs in minerOutputs.items():
	# 		if txid in txs:
	# 			return txs[txid]
	# 	return None

	# protocol = symbolInfo[symbol]["rpc.protocol"]
		# coinbaseId = block["tx"][0]
		# if coinbaseId not in outputs:
		# 	outputs[coinbaseId] = []
		# for txid in block["tx"][1:]:

			# idIterator = txid
			# while True:
			# 	transaction = blockNinja.getRawTransaction(symbol, idIterator, 1)
			# 	vinIndex = int(input(json.dumps(transaction, indent=4, sort_keys=True)))
			# 	vins = transaction["vin"]
			# 	if len(vins) == 0:
			# 		if transaction["vjoinsplit"]:
			# 			idIterator = transaction["vjoinsplit"][0]["anchor"]
			# 			continue
			# 		else:
			# 			exit(json.dumps(transaction, indent=4, sort_keys=True))
			# 	if "txid" in vins[vinIndex]:
			# 		idIterator = vins[vinIndex]["txid"]
			# exit(json.dumps(transaction, indent=4, sort_keys=True))

			# transaction = blockNinja.getRawTransaction(symbol, txid, 1)
			# if not transaction:
			# 	exit(transaction)
			# # exit(json.dumps(transaction, indent=4, sort_keys=True))
			# for vin in transaction["vin"]:
			# 	if "txid" not in vin:
			# 		print("no txid found")
			# 		time.sleep(1)
			# 		continue
			# 	inputTxid = vin["txid"]
			# 	txOutputs = findCoinbase(inputTxid)
			# 	if not txOutputs:
			# 		continue
			# 	txOutputs.append((block["time"], txid))
			# 	print("coinbase output found %s" % repr(yearmonthday(block["time"])))


def plotTheMoney(symbol):

	fig = plt.gcf()
	ax = plt.gca()
	ax.set_ylim(bottom=0)

	stamp = mktime(2018, 1, 1)
	endStamp = mktime(2018, 10, 20)

	X = []
	Y = []
	nextWeek = stamp + 7*86400
	addresses = set()
	while stamp < endStamp:
		if stamp  >= nextWeek:
			X.append(nextWeek)
			Y.append(len(addresses))
			addresses.clear()
			nextWeek += 7*86400
		blocks = getPickledBlocks(symbol, *yearmonthday(stamp))
		for tStamp, height, minerAddress, transactions in blocks:
			for txid, voutIndex, sender, recipients, value in transactions:
				for address in recipients:
					addresses.add(address)
		stamp += 86400
	ax.set_ylim(top=max(Y)*1.05)
	ax.plot(X,Y)
	plt.show()



def plotTheLeader(symbols, averagingLength=14):
	# blockNinja = getBlockNinja()
	earliestEnd = 1e12
	leaderBoard = {symbol:[] for symbol in symbols}
	plt.subplots_adjust(0.30, 0.30, 0.95, 0.85)
	fig = plt.gcf()
	ax = plt.gca()
	ax.set_ylim(bottom=0, top=0.8)
	ax.set_yticks([0, 0.25, 0.5, 0.75])
	ax.set_yticklabels(["0", "25", "50", "75"], fontproperties=getFont("Roboto-Regular", 11))
	minStamp = 1e12
	maxStamp = 0
	for symbol in symbols:
		symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
		firstStamp = getFirstDay(os.path.join(WALLET_COUNT_DIR, symbol))
		lastStamp = getLastDay(os.path.join(WALLET_COUNT_DIR, symbol))
		earliestEnd = min(earliestEnd, lastStamp)
		stamp = firstStamp
		board = leaderBoard[symbol]
		rollBuffer = []
		year, month, day = yearmonthday(stamp)
		symbolDict = symbolInfo[symbol]
		leaderStyle = symbolDict["leader.style"]
		if symbol == "ETC":
			stamp = mktime(2016, 7, 20) # Dao Fork
		while dumpExists(symbolDir, stamp):
			minStamp = min(minStamp, stamp)
			maxStamp = max(maxStamp, stamp)
			# oldMonth = month
			# year, month, day = yearmonthday(stamp)
			# if month != oldMonth:
			# 	board.append((stamp, sum([x[0] for x in rollBuffer])/sum(x[1] for x in rollBuffer)))
			# 	rollBuffer.clear()
			print("Grabbing %s data for %s-%s-%s" % (symbol, *yearmonthday(stamp)))
			with open(makeDumpPath(symbolDir, stamp), "r") as f:
				walletCounts = json.loads(f.read())
				orderedTups = sorted(walletCounts.items(), key=lambda tup: tup[1], reverse=True)
				leader = orderedTups[0]
				blockSum = sum([w[1] for w in orderedTups])
				rollBuffer.append((leader[1], blockSum))
				if len(rollBuffer) == averagingLength:
					board.append((stamp, sum([x[0] for x in rollBuffer])/sum(x[1] for x in rollBuffer)))
					rollBuffer.pop(0)
					rollBuffer.clear()
			stamp += 86400
		year, month, _ = yearmonthday(minStamp)
		year += 1
		stamp = mktime(year, 1)
		xTicks = []
		xLabels = []
		endStamp = mktime(2019)
		while stamp <= endStamp:
			xTicks.append(stamp)
			xLabels.append(time.strftime("%Y", time.gmtime(stamp)))
			year += 1
			stamp = mktime(year, 1)
		duration = endStamp - minStamp
		padding = duration * 0.05
		xlims = {
			"left":minStamp-padding,
			"right":endStamp+padding
		}
		ax.set_xlim(**xlims)
		ax.set_xticks(xTicks)
		ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 11))
		w = duration + 2*padding
		h = 0.5
		rectangle = Rectangle([xlims["left"], 0.5], w, h, facecolor="#ffefef")
		ax.add_patch(rectangle)
		ax.plot([xlims["left"], xlims["right"]], [0.5, 0.5], linewidth=0.5, color="#ff9999", zorder=2)
		ax.plot([w[0] for w in board], [w[1] for w in board], linewidth=2, linestyle=leaderStyle["linestyle"], color=leaderStyle["color"], zorder=3)
	plt.show()

def plotGrid(symbols, plot="range", columns=1, func="dayblock", sharex=None):
	# "Equihash": {
	# 	"ranges":{
	# 		"gpu":{
	# 			"start":0,
	# 			"linecolor":"#1d33af",
	# 			"fillcolor":"#1d33af18",
	# 			"segments":[
				# "low":{
				# 	"model":"Bitmain Z9 Mini",
				# 	"hashrate": 10000,
				# 	"power": 266,
				# 	"cost": 800,
				# },
				# "high":{
				# 	"model":"Asicminer Zeon",
				# 	"hashrate": 180000,
				# 	"power": 2200,
				# 	"cost": 19900,
				# }
	if plot == "range":
		plotHigh = True
		plotLow = True
		plotRange = True
	elif plot == "low":
		plotLow = True
		plotHigh = False
		plotRange = False
	elif plot == "high":
		plotLow = False
		plotHigh = True
		plotRange = False
	else:
		exit("`plot` must be one of ('high','low','range')")
	if func == "dayblock":
		xLabel = "date"
		yLabel = "million USD"
		def plotFunc(tStamp, hashrate, dailyOut, blockTime, device):
			return blockTime/86400*hashrate/device["hashrate"]*device["price"]
		yTicks = {
			"ETH":{
				"ticks":[200e3,400e3],
				"labels":["200k","400k"]
			},
			"ETC":{
				"ticks":[15e3,30e3],
				"labels":["15k","30k"]
			},
			"ZEC":{
				"ticks":[300e3,600e3],
				"labels":["300k","600k"]
			},
			"BTG":{
				"ticks":[200e3, 400e3],
				"labels":["200k","400k"]
			}
		}
	elif func == "retailCapital":
		xLabel = "date"
		yLabel == "million USD"
		def plotFunc(tStamp, hashrate, dailyOut, blockTime, device):
			return hashrate/2/device["hashrate"]*price
		yTicks = {
			"ETH":{
				"ticks":[200e3,400e3],
				"labels":["200k","400k"]
			},
			"ETC":{
				"ticks":[15e3,30e3],
				"labels":["15k","30k"]
			},
			"ZEC":{
				"ticks":[300e3,600e3],
				"labels":["300k","600k"]
			},
			"BTG":{
				"ticks":[200e3, 400e3],
				"labels":["200k","400k"]
			}
		}
	else:
		exit("`func` must be one of ('dayblock')")
	timelines = timelinesTemplate()
	numSymbols = len(symbols)
	rows = int(math.ceil(numSymbols/float(columns)))
	plt.subplots_adjust(left=0.25, bottom=0.25)
	if sharex:
		plt.subplots_adjust(hspace=0)
	fig = plt.gcf()
	topAxes = False
	totalXMax = -1e12
	totalXMin = 1e12
	bottomAxes = []
	for plotIndex, symbol in enumerate(symbols):
		kwargs = {}
		isColumnHeader = plotIndex%rows  == 0
		if isColumnHeader or not sharex:
			topAxes = ax = fig.add_subplot("%i%i%i" % (rows, columns, plotIndex+1))
		else:
			ax = fig.add_subplot("%i%i%i" % (rows, columns, plotIndex+1), sharex=topAxes)
		ax.grid(True, which="major", axis="both", color="#eeeeee")
		algo = symbolInfo[symbol]["algorithm"]
		ranges = recursiveUpdate({}, algoInfo[algo]["ranges"])
		blockTime = symbolInfo[symbol]["block.time"]
		threshold = 1/blockTime
		with open(os.path.join("data","%s.json" % symbol), "r") as f:
			# tStamp, hashrate, dailyOut
			dayPts = json.loads(f.read())
		startStamp = dayPts[0][0]
		endStamp = dayPts[-1][0]
		year, month, day = yearmonthday(startStamp)
		isBottomRow = plotIndex+1 > (rows-1)*columns
		if isBottomRow:
			bottomAxes.append(ax)

		for deviceType, deviceRange in ranges.items():
			for segment in deviceRange["segments"]:
				segment["timestamps"] = []
				segment["high"] = []
				segment["low"] = []

		if sharex:
			if not isBottomRow:
				[label.set_visible(False) for label in ax.get_xticklabels()]
		else:
			xTicks = []
			xLabels = []
			while year < 2019:
				year += 1
				yearStamp = mktime(year, 1, 1)
				xTicks.append(yearStamp)
				xLabels.append(str(year))
				ax.set_ylabel(yLabel, fontproperties=getFont("Roboto-Medium", 13))
				# oldYear = year
				# year, month = iterateYearMonth(year, month)
				# stamp = mktime(year, month)
				# if stamp >= endStamp:
				# 	break
				# xTicks.append(stamp)
				# if oldYear == year:
				# 	xLabels.append("")
				# else:
				# 	xLabels.append(str(year))
			ax.xaxis.set_minor_locator(AutoMinorLocator(12))
			ax.set_xticks(xTicks)
			ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))
		ticks = yTicks[symbol]
		ax.set_yticks(ticks["ticks"])
		ax.set_yticklabels(ticks["labels"], fontproperties=getFont("Roboto-Regular", 10))
		tickmax = max(ticks["ticks"])
		padding = 0.15
		pad = padding*tickmax
		ax.set_ylim(bottom=0, top=tickmax+pad)
		if isBottomRow:
			ax.set_xlabel(xLabel, fontproperties=getFont("Roboto-Medium", 13))
		xMin = yMin = 1e12
		xMax = yMax = -1e12
		lastStamp = 0
		for tStamp, hashrate, dailyOut in dayPts:
			for deviceType, deviceRange in ranges.items():
				if tStamp < deviceRange["start"]:
					continue
				high = deviceRange["high"]
				low = deviceRange["low"]
				if symbol == "BTG" and tStamp > 1530679085:
					if deviceType == "asic":
						continue
					high["hashrate"] = 56
				for segment in deviceRange["segments"]:
					# "end":1e12,
					# "style": "-",
					# "linewidth": 1,
					# "timestamps":[],
					# "high":[],
					# "low":[]
					if tStamp < segment["end"]:
						xMin = min(xMin, tStamp)
						xMax = max(xMax, tStamp)
						segment["timestamps"].append(tStamp)

						# if symbol == "ETH" and deviceType == "asic" and tStamp > mktime(2018, 9, 25):
							# print("hashrate: %r" % (hashrate, ))
							# print("dailyOut: %r" % (dailyOut, ))
							# print("blockTime: %r" % (blockTime, ))
							# print("high['hashrate']: %r" % (high['hashrate'], ))
							# print("plotFunc: %r" % plotFunc(tStamp, hashrate, dailyOut, blockTime, high))
							# exit()
						lowVal = plotFunc(tStamp, hashrate, dailyOut, blockTime, low)
						segment["low"].append(lowVal)
						highVal = plotFunc(tStamp, hashrate, dailyOut, blockTime, high)
						segment["high"].append(highVal)
						for val in (lowVal, highVal):
							yMin = min(val, yMin)
							yMax = max(val, yMax)
						break
		totalXMax = max(totalXMax, xMax)
		totalXMin = min(totalXMin, xMin)
		yRange = yMax - yMin
		xRange = xMax - xMin
		padding = 0.05
		yPad = yRange*padding
		# xPad = xRange*padding
		ylims = {
			"bottom": yMin - yPad,
			"top": yMax + yPad
		}

		# xlims = {
		# 	"left": xMin - xPad,
		# 	"right": xMax + xPad
		# }

		# for event in timelines[symbol]["events"]:
		# 	if not event["active"]:
		# 		continue
		# 	eventStamp = event["timestamp"]
		# 	ax.plot([eventStamp, eventStamp], [ylims["bottom"], ylims["top"]], color="#cccccc", linewidth=1, zorder=1)
		for deviceType, deviceRange in ranges.items():
			high = deviceRange["high"]
			low = deviceRange["low"]
			linecolor = deviceRange["linecolor"]
			allStamps = []
			topLine = []
			bottomLine = []
			(allStamps.extend(segment["timestamps"]) for segment in deviceRange["segments"])
			(topLine.extend(segment["high"]) for segment in deviceRange["segments"])
			(bottomLine.extend(segment["low"]) for segment in deviceRange["segments"])
			for segment in deviceRange["segments"]:
				timestamps = segment["timestamps"]
				if plotLow:
					ax.plot(timestamps, segment["low"], color=linecolor, linewidth=segment["linewidth"], linestyle=segment["linestyle"], zorder=3)
				if plotHigh:
					ax.plot(timestamps, segment["high"], color=linecolor, linewidth=segment["linewidth"], linestyle=segment["linestyle"], zorder=3)
				if plotRange:
					ax.fill_between(timestamps, segment["low"], segment["high"], color=segment["fillcolor"], zorder=2)
	if sharex:
		year, month, day = yearmonthday(totalXMin)
		xTicks = []
		xLabels = []
		while year < 2020:
			xTicks.append(mktime(year, 1, 1))
			xLabels.append(str(year))
			year += 1
		for ax in bottomAxes:
			ax.set_xticks(xTicks)
			ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 11))
			ax.set_xlim(left=mktime(2017, 1, 1), right=mktime(2019, 1, 1))
			ax.xaxis.set_minor_locator(AutoMinorLocator(12))
	plt.show()

def plotBTGAttack():
	symbol = "BTG"
	symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)

	fig = plt.gcf()
	subplotAdjustments = {
		"left":0,
		"right":1,
		"bottom":0,
		"top":1,
		"wspace":0,
		"hspace":0
	}
	fig.subplots_adjust(**subplotAdjustments)
	plotter = NetworkPlotter(fig, (200,100))
	plotter.setPadding(0.05)
	plotter.minFontSize = 2
	plotter.showName = False
	plotter.showNakamoto = False
	plotter.pctScaler = 30
	plotter.offsetFactor = 3
	plotter.walletFormatter = lambda a, w: a[-4:]

	attackStamp = mktime(*yearmonthday(1526662750))
	startStamp = attackStamp-86400*3
	endStamp = attackStamp + 1
	axes = {}
	for i in range(5):
		ax = plotter.createAxes(symbol, "51%i" % (i+1))
		stamp = startStamp + i*86400
		with open(makeDumpPath(symbolDir, stamp), "r") as f:
			miners = json.loads(f.read())
		numBlocks = float(sum([v for k,v in miners.items()]))
		values = sorted([(v/numBlocks, k) for k,v in miners.items()], key=lambda m: m[0], reverse=True)
		plotter.plotValues(ax, stamp, values, progress=False)
	plt.show()


def plotAddresses(symbol, addresses, startStamp, endStamp, threshold, plotRemainder=True, styles=None, rebuild=False):
	styles = styles if styles else {}
	attackStamp = mktime(2018, 5, 18)
	symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
	blockNinja = getBlockNinja()

	fig = plt.gcf()
	subplotAdjustments = {
		"left":0.25,
		"right":0.75,
		"bottom":0.25,
		"top":0.75,
		"wspace":0,
		"hspace":0
	}
	fig.subplots_adjust(**subplotAdjustments)
	ax = plt.gca()
	ax.set_yticks([0, 1, 2, 3, 4])
	ax.set_yticklabels(["0", "1", "2", "3", "4"], fontproperties=getFont("Roboto-Regular", 10))
	ax.set_ylim(bottom=0, top=4.8)
	marketAxis = ax.twinx()
	marketAxis.set_yticks([0, 20, 40, 60, 80])
	marketAxis.set_yticklabels(["0", "20", "40", '60', "80"], fontproperties=getFont("Roboto-Regular", 10))
	marketAxis.set_ylim(bottom=0, top=80)
	
	if rebuild:
		stamp = mktime(*yearmonthday(startStamp))
		days = {}
		block = None
		while stamp <= endStamp:
			miners = days[stamp] = {"the rest": 0}
			if not block:
				block = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(stamp))
				lastBlock = blockNinja.getBlockByHeight(symbol, block["height"])
			nextStamp = stamp + 86400
			while block["time"] < nextStamp:
				miner = blockNinja.getMinerAddress(symbol, block)
				work = int(block["chainwork"], 16) - int(lastBlock["chainwork"], 16)
				if miner in addresses:
					if miner not in miners:
						miners[miner] = 0
					miners[miner] += work
				else:
					miners["the rest"] += work
				lastBlock = block
				block = blockNinja.iterateBlock(symbol, block)
			stamp += 86400
		with open("addresses-data.json", "w") as f:
			f.write(json.dumps(days))
	
	with open("addresses-data.json", "r") as f:
		days = json.loads(f.read())
		for k,v in dict(days).items():
			days.pop(k)
			dayStamp = int(float(k))
			if dayStamp > endStamp:
				continue
			days[dayStamp] = v
	dayItems = sorted(days.items(), key=lambda d: d[0])
	allX = [t for t, d in dayItems]
	allY = []
	marketX = []
	marketY = []
	xTicks = []
	xLabels = []
	attackStamp = mktime(2018, 5, 18)
	ax.plot([attackStamp, attackStamp], [-1, 6], color="#cccccc", linewidth=1, zorder=1)

	results = archivist.getQueryResults("SELECT symbol_id FROM currencies WHERE symbol=? ", (symbol, ))
	symbolId = results[0][0]
	query = "SELECT open, high, low, close, date_stamp FROM candlesticks WHERE symbol_id=? AND date_stamp < ? ORDER BY date_stamp DESC LIMIT 1"



	for stamp in allX:
		marketX.append(stamp)
		results = archivist.getQueryResults(query, (symbolId, stamp+86000))
		openv, high, low, closev, tStamp = results[0]
		marketY.append((openv+closev)/2)
		dayWork = 0
		day = days[stamp]
		for address, work in day.items():
			dayWork += work
		allY.append(dayWork/1e12)

		xTicks.append(stamp)
		y,m,d = yearmonthday(stamp)
		print(stamp-attackStamp)
		if stamp == allX[0] or stamp == allX[-1] or stamp == attackStamp:
			xLabels.append("%i/%i" % (m,d))
		else:
			xLabels.append("")
	linewidth, linestyle, color = styles["market"]
	marketAxis.plot(marketX, marketY, linewidth=linewidth, linestyle=linestyle, color=color, zorder=3)
	ax.set_xticks(xTicks)
	ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))

	for address in addresses + ["the rest"]:
		X = []
		Y = []
		for dayStamp, day in dayItems:
			X.append(dayStamp)
			if address in day:
				Y.append(day[address]/1e12)
			else:
				Y.append(0)
		displayLabel = "rest" if address == "the rest" else address[-4:]
		zorder = 5 if address == "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx" else 3
		linewidth, linestyle, color = styles[address]
		ax.plot(X, Y, linewidth=linewidth, linestyle=linestyle, color=color, zorder=zorder)
	linewidth, linestyle, color = styles["net"]
	ax.plot(allX, allY, linewidth=linewidth, linestyle=linestyle, color=color, zorder=3)
	plt.show()

def plotBlockHistogram(rebuild=False):
	blockNinja = getBlockNinja()
	symbol = "BTG"
	startStamp = mktime(2018, 5, 13)
	normStamp = mktime(2018, 5, 16) 
	endStamp = mktime(2018, 5, 19)

	fig = plt.gcf()
	subplotAdjustments = {
		"left":0.25,
		"right":0.75,
		"bottom":0.25,
		"top":0.75,
		"wspace":0,
		"hspace":0.50
	}
	fig.subplots_adjust(**subplotAdjustments)
	normAxis = fig.add_subplot("211")
	attackAxis = fig.add_subplot("212")
	for ax in (normAxis, attackAxis):
		ax.set_ylim(bottom=0, top=1.2)
		ax.set_yticks([0, 0.5, 1])
		ax.set_yticklabels(["0", "50", "100"],  fontproperties=getFont("Roboto-Regular", 10))
		ax.set_xlim(left=-0.5, right=72.5)
		ax.grid(b=None, which='major', axis='y', linewidth=1, color="#dddddd")
		ax.xaxis.set_minor_locator(AutoMinorLocator(24))


	xTicks = []
	xLabels = []
	for i in range(0, 73, 24):
		xTicks.append(i)
		y, m, d = yearmonthday(startStamp+i*3600)
		xLabels.append("%i/%i" % (m, d))
	normAxis.set_xticks(xTicks)
	normAxis.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))

	xTicks = []
	xLabels = []
	for i in range(0, 73, 24):
		xTicks.append(i)
		y, m, d = yearmonthday(normStamp+i*3600)
		xLabels.append("%i/%i" % (m, d))
	attackAxis.set_xticks(xTicks)
	attackAxis.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))

	if rebuild:
		block = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(startStamp))
		normX = []
		normY = []
		attackX = []
		attackY = []
		nextHour = startStamp + 3600
		hourCounter = attackCounter = 0
		while True:
			if block["time"] >= nextHour:
				if nextHour - 1 < normStamp:
					normX.append((nextHour - startStamp)/3600)
					normY.append(attackCounter/hourCounter)
				else:
					attackX.append((nextHour - normStamp)/3600)
					attackY.append(attackCounter/hourCounter)
				hourCounter = attackCounter = 0
				nextHour += 3600
			if block["time"] > endStamp:
				break
			hourCounter += 1
			minerAddress = blockNinja.getMinerAddress(symbol, block)
			if block["time"] >= normStamp:
				if minerAddress == "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx":
					attackCounter += 1
			elif minerAddress == "GK18bp4UzC6wqYKKNLkaJ3hzQazTc3TWBw": # GK18bp4UzC6wqYKKNLkaJ3hzQazTc3TWBw # GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx
				attackCounter += 1
			block = blockNinja.iterateBlock(symbol, block)
		with open("data/blockhisto.json", "w") as f:
			f.write(json.dumps([normX, normY, attackX, attackY]))

	with open("data/blockhisto.json", "r") as f:
		normX, normY, attackX, attackY = json.loads(f.read())

	normAxis.bar(normX, normY, width=0.75, color="#555555", zorder=3)
	attackAxis.bar(attackX, attackY, width=0.75, color="#a01500", zorder=3)
	plt.show()


		


# blockNinja = getBlockNinja()
# dateStamp = mktime(*yearmonthday(1526662750))
# stamp = dateStamp - 7*86400
# endStamp = dateStamp + 7*86400
# msgs = []
# symbol = "BTG"
# symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
# while stamp <= endStamp:

# 	# with open(makeDumpPath(symbolDir, stamp), "r") as f:
# 	# 	counts = json.loads(f.read())
# 	# if "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx" in counts:
# 	# 	msgs.append("%.2f" % (counts["GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx"]/sum(v for k, v in counts.items())))
# 	# else:
# 	# 	msgs.append("0")

# 	ymd = yearmonthday(stamp)
# 	firstBlock = blockNinja.getFirstBlockOfDay(symbol, *ymd)
# 	lastBlock = blockNinja.getLastBlockOfDay(symbol, *ymd)
# 	hashrate = (int(lastBlock["chainwork"], 16)-int(firstBlock["chainwork"], 16))/(lastBlock["time"] - firstBlock["time"])
# 	if stamp == dateStamp:
# 		msgs.append("*%s: %e" % (symbol, hashrate))
# 	else:
# 		msgs.append("%s: %e" % (symbol, hashrate))

# 	stamp += 86400
# exit("\n".join(msgs))


# blockNinja = getBlockNinja()
# symbol = "ETH"
# block = blockNinja.getBlockByHeight(symbol, int(4e6))
# exit(json.dumps(block, indent=4, sort_keys=True))


# blockNinja = getBlockNinja()
# symbol = "ETH"
# tip = blockNinja.getTip(symbol)
# blocks = 256
# hashpts = blockNinja.getNethashPts(symbol, tip["height"], avgLengths=[blocks])
# deviceRate = 31300000
# deviceRate = 735
# deviceRate = 50e6
# hashrate = hashpts[blocks]
# seconds = hashrate/deviceRate
# exit(repr(seconds/86400))


# exit(imageio.help("FFMPEG"))


# This Monero "miner_tx" block attribute doesn't appear to have a public wallet address
# jsonString = "{\n  \"major_version\": 1, \n  \"minor_version\": 2, \n  \"timestamp\": 1452793716, \n  \"prev_id\": \"b61c58b2e0be53fad5ef9d9731a55e8a81d972b8d90ed07c04fd37ca6403ff78\", \n  \"nonce\": 1646, \n  \"miner_tx\": {\n    \"version\": 1, \n    \"unlock_time\": 912405, \n    \"vin\": [ {\n        \"gen\": {\n          \"height\": 912345\n        }\n      }\n    ], \n    \"vout\": [ {\n        \"amount\": 8968946286, \n        \"target\": {\n          \"key\": \"378b043c1724c92c69d923d266fe86477d3a5ddd21145062e148c64c57677008\"\n        }\n      }, {\n        \"amount\": 80000000000, \n        \"target\": {\n          \"key\": \"73733cbd6e6218bda671596462a4b062f95cfe5e1dbb5b990dacb30e827d02f2\"\n        }\n      }, {\n        \"amount\": 300000000000, \n        \"target\": {\n          \"key\": \"47a5dab669770da69a860acde21616a119818e1a489bb3c4b1b6b3c50547bc0c\"\n        }\n      }, {\n        \"amount\": 7000000000000, \n        \"target\": {\n          \"key\": \"1f7e4762b8b755e3e3c72b8610cc87b9bc25d1f0a87c0c816ebb952e4f8aff3d\"\n        }\n      }\n    ], \n    \"extra\": [ 1, 253, 10, 119, 137, 87, 244, 243, 16, 58, 131, 138, 253, 164, 136, 195, 205, 173, 242, 105, 123, 61, 52, 173, 113, 35, 66, 130, 178, 250, 217, 16, 14, 2, 8, 0, 0, 0, 11, 223, 194, 193, 108\n    ], \n    \"signatures\": [ ]\n  }, \n  \"tx_hashes\": [ ]\n}"
# exit(json.dumps(json.loads(jsonString), indent=4, sort_keys=True))

def pickleBlocks(symbol, year, month, day, blocks):
	rootDir = os.path.join("data", "pickled-blocks", symbol)
	stamp = mktime(year, month, day)
	with open(makeDumpPath(rootDir, stamp, "pkl"), "wb") as f:
		pickle.dump(blocks, f, pickle.HIGHEST_PROTOCOL)

def getPickledBlocks(symbol, year, month, day):
	rootDir = os.path.join("data", "pickled-blocks", symbol)
	mkdir(rootDir)
	stamp = mktime(year, month, day)
	if dumpExists(rootDir, stamp, "pkl"):
		with open(makeDumpPath(rootDir, stamp, "pkl"), "rb") as f:
			return pickle.load(f)
	blockNinja = getBlockNinja()
	block = blockNinja.getFirstBlockOfDay(symbol, year, month, day)
	end = stamp + 86400
	blocks = []
	protocol = blockNinja.nodes[symbol].protocol
	while block["time"] < end:
		minerAddress = blockNinja.getMinerAddress(symbol, block)
		transactions = []
		if protocol == "btc":
			for txid in block["tx"][1:]:
				transaction = blockNinja.getRawTransaction(symbol, txid, 1)
				vins = transaction["vin"]
				sender = ""
				for vin in vins:
					if "txid" in vin:
						source = blockNinja.getRawTransaction(symbol, vin["txid"], 1)
						vout = source["vout"][vin["vout"]]
						if "scriptPubKey" in vout and "addresses" in vout["scriptPubKey"] and len(vout["scriptPubKey"]["addresses"]) == 1:
							sender = vout["scriptPubKey"]["addresses"][0]
							break
				vouts = transaction["vout"]
				for i, vout in enumerate(vouts):
					# print(json.dumps(vout, indent=4))
					scriptPubKey = vout["scriptPubKey"]
					if "addresses" in scriptPubKey:
						value = vout["value"]
						transactions.append((txid, i, sender, scriptPubKey["addresses"], value))
		elif protocol == "eth":
			for tx in block["transactions"]:
				transactions.append((tx["hash"], tx["transactionIndex"], tx["from"], [tx["to"]], tx["value"]))
		blocks.append((block["time"], block["height"], minerAddress, transactions))
		block = blockNinja.iterateBlock(symbol, block)
	pickleBlocks(symbol, year, month, day, blocks)
	return blocks


def blockLog(rebuild=False):
	startStamp = mktime(2018, 5, 16) 
	endStamp = mktime(2018, 5, 20)
	if rebuild:
		blockNinja = getBlockNinja()
		symbol = "BTG"
		block = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(startStamp))
		blocks = []
		while block["time"] < endStamp:
			minerAddress = blockNinja.getMinerAddress(symbol, block)
			transactions = []
			for txid in block["tx"][1:]:
				transaction = blockNinja.getRawTransaction(symbol, txid, 1)
				vouts = transaction["vout"]
				for i, vout in enumerate(vouts):
					# print(json.dumps(vout, indent=4))
					scriptPubKey = vout["scriptPubKey"]
					if "addresses" in scriptPubKey:
						value = vout["value"]
						transactions.append((txid, i, scriptPubKey["addresses"], value))
			print("minerAddress: %s" % minerAddress)

			blocks.append((block["time"], block["height"], minerAddress, transactions))					
			block = blockNinja.iterateBlock(symbol, block)
		with open("data/attack-days-blocks.pkl", "wb") as f:
			pickle.dump(blocks, f, pickle.HIGHEST_PROTOCOL)

	with open("data/attack-days-blocks.pkl", "rb") as f:
		blocks = pickle.load(f)

	attackWallet = "GTNjvCGssb2rbLnDV1xxsHmunQdvXnY2Ft"
	attackMiner = "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx"
	start = mktime(2018, 5, 16) 
	hours = []
	hour = []
	nextHour = start + 3600
	for tStamp, height, minerAddress, transactions in blocks:
		# if tStamp in (1526689020, 1526707540): # The gap
		# 	print("height: %i, time: %s" % (height, time.strftime("%m/%d %H:%M", time.gmtime(tStamp))))

		while tStamp >= nextHour:
			hours.append(hour)
			hour = []
			nextHour += 3600
		isAttacker = minerAddress == attackMiner
		hour.append((tStamp, minerAddress, isAttacker))
		for txid, voutIndex, addresses, value in transactions:
			if attackWallet in addresses:
				pass
			if attackMiner in addresses: 
				pass
	if hour:
		hours.append(hour)

	plt.subplots_adjust(0.25, 0.05, 0.75, 0.95, 0, 0)
	ax = plt.gca()
	numHours = len(hours)
	ax.set_ylim(bottom=0, top=numHours)
	ax.set_xlim(left=0, right=100)
	iterator = 0
	yTicks = []
	yLabels = []
	while iterator <= numHours:
		stamp = startStamp+iterator*3600
		yTicks.append(numHours-iterator)
		y,m,d = yearmonthday(stamp)
		yLabels.append("May %ith" % (d, ))
		am6 = numHours-iterator-6.5
		if am6 >= 0:
			yTicks.append(am6)
			yLabels.append("6:00")
		nooner = numHours-iterator-12.5
		if nooner >= 0:
			yTicks.append(nooner)
			yLabels.append("12:00")
		pm6 = numHours-iterator-18.5
		if pm6 >= 0:
			yTicks.append(pm6)
			yLabels.append("18:00")
		iterator += 24
	ax.yaxis.set_minor_locator(AutoMinorLocator(12))
	ax.set_yticks(yTicks)
	ax.set_yticklabels(yLabels, fontproperties=getFont("Roboto-Regular", 10))
	ax.set_xticks([])

	width = 100
	colors = {
		"GK18bp4UzC6wqYKKNLkaJ3hzQazTc3TWBw": "#5154ff77", 
		"GQ6Btf3KmRz4VoMsEZi7WBdCYuY1XeXTrY": "#ff4fff77", 
		"GVQiajM9TTSNVATL3JEGLG9s48TWHTJg8S": "#30b53777", 
		"GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx": "#ff2626"
	}
	noBlocks = []
	emptyHour = False
	for i, hour in enumerate(hours):
		top = numHours - i
		numBlocks = len(hour)

		if numBlocks:
			if emptyHour:
				noBlocks.append((emptyHour, i))
				emptyHour = False
		else:
			if not emptyHour:
				emptyHour = i
			continue
		blockWidth = width/numBlocks
		print("---- hour %i ----" % i)
		for j, block in enumerate(hour):
			# print(repr(block))
			tStamp, minerAddress, isAttacker = block
			left = blockWidth*j
			color = colors[minerAddress] if minerAddress in colors else "#22d2d877"
			print("%s %s" % (time.strftime("%m/%d %H:%M", time.gmtime(tStamp)), repr((top, left, blockWidth, color, isAttacker))))
			rectangle = Rectangle((left, top), blockWidth, -1, facecolor=color, edgecolor="#555555", linewidth=1)
			ax.add_patch(rectangle)
	for start, end in noBlocks:
		rectangle = Rectangle((0, numHours-start), width, start-end, facecolor="black", edgecolor="black", linewidth=1)
		ax.add_patch(rectangle)
	plt.show()





# exit(repr(blockNinja.getAverageBlockTime("ETH")))


# symbol = "ZEC"
# blocksPerDay = 86400/150
# threshold = 1/blocksPerDay
# blockNinja = getBlockNinja()
# tip = blockNinja.getTip(symbol)
# hashrate = blockNinja.getNethashPts(symbol, tip["height"], avgLengths=[500])[500]
# print()
# print(threshold*hashrate/10000) # devices necessary for a block per day or days for a single device
# 10000
# 180000
# exit()


# print("##### REMOVING COINS #####")
# SYMBOLS = ["ZEC"]
# plotEquihash(addYear=False, withEvents=False)
# print("##### REMOVING COINS #####")
# SYMBOLS.remove("BTG")
# start = time.mktime(time.strptime("2018-04", "%Y-%m"))
# end = time.mktime(time.strptime("2018-10-02", "%Y-%m-%d"))

# symbol = "BTG"
# symbolDir = os.path.join(WALLET_COUNT_DIR, symbol)
# day = getFirstDay(symbolDir)
# lastDay = getLastDay(symbolDir)
# while day <= lastDay:
# 	miners = fetchDump(symbolDir, day)
# 	if "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx" in miners:
# 		print("found it")
# 	day += 86400
# exit()

# exit(repr(yearmonthday(1526662750)))
# plotBTGAttack()


def plotHashrateLengths(rebuild=False):
	symbol = "BTG"
	results = archivist.getQueryResults("SELECT symbol_id FROM currencies WHERE symbol=? ", (symbol, ))
	symbolId = results[0][0]
	query = "SELECT high, low, open, close, date_stamp FROM candlesticks WHERE symbol_id=? AND date_stamp < ? ORDER BY date_stamp DESC LIMIT 1"
	def getOrphanedBranch(height):
		for tip in revertedTips:
			branchlen = tip["branchlen"]
			if height == tip["height"]-branchlen:
				blocks = []
				blockhash = tipHash = tip["hash"]
				for _ in range(branchlen):
					orphanPath = os.path.join("orphans", symbol, "%s.json" % blockhash)
					with open(orphanPath, "r") as f:
						block = json.loads(f.read())
					blocks.insert(0, block)
					blockhash = block["previousblockhash"]
				return tipHash, blocks
		return False, False
	if rebuild:
		lengths = {
			# 4: {
			# 	"best":[],
			# 	"orphans":{}
			# },
			# 8: {
			# 	"best":[],
			# 	"orphans":{}
			# },
			# 16: {
			# 	"best":[],
			# 	"orphans":{}
			# },
			# 32: {
			# 	"best":[],
			# 	"orphans":{}
			# },
			64: {
				"best":[],
				"orphans":{},
				"color": "#555555"
			},
			128: {
				"best":[],
				"orphans":{},
				"color":"#5555aa"
			},
			256: {
				"best":[],
				"orphans":{},
				"color":"#55aa55"
			},
		}
		blockNinja = getBlockNinja()	
		longest = max((l for l, x in lengths.items()))
		block = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(mktime(2018, 5, 12)))
		endStamp = mktime(2018, 5, 25)
		block = blockNinja.getBlockByHeight(symbol, block["height"]-longest)
		work = []
		while block["time"] < endStamp:
			work.append((block["time"], int(block["chainwork"], 16)))
			tipHash, orphans = getOrphanedBranch(block["height"])
			if tipHash and len(work) == longest+1:
				for length, data in lengths.items():
					print("making %i-length chain for %s" % (length, tipHash))
					lst = data["orphans"][tipHash] = []
					numOrphans = len(orphans)
					for i, orphan in enumerate(orphans):
						if length > i:
							t, cw = work[-length+i]
						else:
							idx = i-length
							blk = orphans[idx]
							t, cw = blk["time"], int(blk["chainwork"], 16)
						hashrate = (int(orphan["chainwork"], 16)-cw)/(orphan["time"]-t)
						now = orphan["time"]
						# ages = [now - w[0] for w in work[-length-1:-1]]
						meanAge = (orphan["time"]-t)/length
						lst.append((orphan["time"], meanAge, hashrate, False))
			isAttacker = blockNinja.getMinerAddress(symbol, block) == "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx"
			if not results:
				print("got no results: %r" % results)
				continue
			if len(work) == longest+1:
				for length, data in lengths.items():
					t, cw = work[-length-1]
					hashrate = (int(block["chainwork"], 16)-cw)/(block["time"]-t)
					now = block["time"]
					ages = [now - w[0] for w in work[-length-1:-1]]
					meanAge = sum(ages)/len(ages)
					print("%i: %f" % (length, meanAge/60))
					data["best"].append((block["time"], meanAge, hashrate, isAttacker))
				work.pop(0)
			block = blockNinja.iterateBlock(symbol, block)
		with open("data/hashrate-lengths.json", "w") as f:
			f.write(json.dumps(list(lengths.items())))

	with open("data/hashrate-lengths.json", "r") as f:
		lengthItems = json.loads(f.read())

	ax = plt.gca()
	xTicks = []
	xLabels = []
	for d in range(10, 30):
		xTicks.append(mktime(2018, 5, d))
		xLabels.append("5/%i" % d)
	ax.set_xticks(xTicks)
	ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))
	for label in ax.get_yticklabels():
		label.set_font_properties(getFont("Roboto-Regular", 10))
	rates = {}
	maxY = 0
	replacedLines = {}
	def getAdjustedRate(tStamp):
		ymd = yearmonthday(tStamp)
		startStamp = mktime(*ymd)
		dayRatio = (tStamp-startStamp)/86400
		key = repr(ymd)
		if key not in rates:
			results = archivist.getQueryResults(query, (symbolId, startStamp+86398))
			high, low, mOpen, mClose, dStamp = results[0]
			rates[key] = (mOpen, mClose)
		mOpen, mClose = rates[key]
		pDelta = mClose-mOpen
		return mOpen+dayRatio*pDelta

	for length, data in lengthItems:
		pts = data["best"]
		color = data["color"]
		if length < 33:
			continue
		X = []
		Y = []
		for pt in pts:
			tStamp, meanAge, hashrate, isAttacker = pt
			# adjustedStamp = tStamp - meanAge
			# dateString = time.strftime("%m/%d %H:%M", time.gmtime(tStamp))			
			# price = getAdjustedRate(adjustedStamp)
			# print("%s: %s" % (dateString, (hashrate/1e9, price, mOpen, mClose, dayRatio, meanAge/60)))
			# print(price)
			X.append(tStamp)
			adjustedRate = hashrate/1e6#/price
			Y.append(adjustedRate)
			maxY = max(maxY, adjustedRate)
		ax.plot(X, Y, linewidth=1.5, color=color, zorder=length)
		for tipHash, pts in data["orphans"].items():
			X = []
			Y = []
			for tStamp, meanAge, hashrate, isAttacker in pts:
				X.append(tStamp)
				adjustedRate = hashrate/1e6
				Y.append(adjustedRate)
				maxY = max(maxY, adjustedRate)
			ax.plot(X, Y, linewidth=1.5, color=color, linestyle="--")
	isAttackers = []
	lastAttack = False
	attackRanges = []
	rangeList = lengthItems[-1][1]["best"]
	for i in range(len(rangeList)):
		pt = rangeList[i]
		tStamp, meanAge, hashrate, isAttacker = pt
		if isAttacker:
			if not lastAttack:
				lastAttack = rangeList[i-1][0] # Get the timestamp of the last block
		else:
			if lastAttack:
				attackRanges.append((lastAttack, rangeList[i-1][0]))
			lastAttack = False
	# isAttacking = False
	# for tStamp, isAttacker in isAttackers:
	# 	if isAttacker and not isAttacking:
	# 		isAttacking = tStamp
	# 	elif isAttacking and not isAttacker:
	# 		attackRanges.append((isAttacking, tStamp))
	# 		isAttacking = False
	for start, end in attackRanges:
		# ax.plot([start, start], [-maxY,maxY*2], color="#ff262644", linewidth=0.75)
		# ax.plot([end, end], [-maxY,maxY*2], color="#ff262644", linewidth=0.75)
		ax.add_patch(Rectangle((start, -maxY), end-start, 3*maxY, facecolor="#ff262633", linewidth=0))
	plt.show()

def plotTransactions(symbol):
	symbol = "BTG"
	ax = plt.gca()
	ax.set_yscale("log", basey=10)
	xTicks = []
	xLabels = []
	for d in range(10, 30):
		xTicks.append(mktime(2018, 5, d))
		xLabels.append("5/%i" % d)
	ax.set_xticks(xTicks)
	ax.set_xticklabels(xLabels, fontproperties=getFont("Roboto-Regular", 10))
	for label in ax.get_yticklabels():
		label.set_font_properties(getFont("Roboto-Regular", 10))


	dayStamp = mktime(2018, 5, 13)
	end = mktime(2018, 5, 20)
	X = []
	Y = []
	attackerX = []
	attackerY = []
	attackWallet = "GTNjvCGssb2rbLnDV1xxsHmunQdvXnY2Ft"
	attackMiner = "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx"
	isAttackers = []
	maxY = 0
	lastStamp = lastValue = -1
	while dayStamp < end:
		year, month, day = yearmonthday(dayStamp)
		blocks = getPickledBlocks(symbol, year, month, day)
		for tStamp, height, minerAddress, transactions in blocks:
			isAttackers.append((tStamp, minerAddress==attackMiner))
			for txid, voutId, sender, recipients, value in transactions:
				if attackWallet in recipients:
					attackerX.append(tStamp)
					attackerY.append(value)
				else:
					X.append(tStamp)
					Y.append(value)
				maxY = max(maxY, value)
				if value == lastValue and tStamp == lastStamp:
					print("duplicate found: %f at %s" % (value, time.strftime("%m/%d %H:%M", time.gmtime(tStamp))))
				lastValue = value
			lastStamp = tStamp
		dayStamp += 86400

	lastAttack = False
	attackRanges = []
	for i in range(len(isAttackers)):
		tStamp, isAttacker = isAttackers[i]
		if isAttacker:
			if not lastAttack:
				lastAttack = isAttackers[i-1][0] # Get the timestamp of the last block
		else:
			if lastAttack:
				attackRanges.append((lastAttack, isAttackers[i-1][0]))
			lastAttack = False
	for start, end in attackRanges:
		# ax.plot([start, start], [-maxY,maxY*2], color="#ff262644", linewidth=0.75)
		# ax.plot([end, end], [-maxY,maxY*2], color="#ff262644", linewidth=0.75)
		ax.add_patch(Rectangle((start, -maxY), end-start, 3*maxY, facecolor="#ff262622", linewidth=0))

	ax.scatter(X, Y, s=1, c="#555555", marker=".")
	ax.scatter(attackerX, attackerY, s=1, c="red", marker=".")
	plt.show()




# block = blockNinja.getBlockByHeight(symbol, 528645)
# msgs = []
# for txid in block["tx"][:]:
# 	tx = blockNinja.getRawTransaction(symbol, txid, 1)
# 	msgs.append(json.dumps(tx, indent=4, sort_keys=4))
# exit("\n".join(msgs))
# stamp  = mktime(2018, 5, 15)
# firstBlock = blockNinja.getFirstBlockOfDay(symbol, *yearmonthday(stamp))
# lastBlock = blockNinja.getLastBlockOfDay(symbol, *yearmonthday(stamp))
# # Equihash ASIC
# # "hashrate": 180000,
# # "power": 2200,
# # "price": 19900,

# # Ethash ASIC
# # "model": "Bitmain Antminer E3",
# # "hashrate": 190e6,
# # "power": 760,
# # "price": 1150,
# hashrate = (int(lastBlock["chainwork"], 16) - int(firstBlock["chainwork"], 16))/(lastBlock["time"] - firstBlock["time"])
# print(hashrate)
# exit(repr(hashrate/735*475))




addresses = ["GK18bp4UzC6wqYKKNLkaJ3hzQazTc3TWBw", "GQ6Btf3KmRz4VoMsEZi7WBdCYuY1XeXTrY", "GVQiajM9TTSNVATL3JEGLG9s48TWHTJg8S", "GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx"]
styles = {
	"GK18bp4UzC6wqYKKNLkaJ3hzQazTc3TWBw": (1.5, "-", "#5154ff"), 
	"GQ6Btf3KmRz4VoMsEZi7WBdCYuY1XeXTrY": (1.5, "-", "#ff4fff"), 
	"GVQiajM9TTSNVATL3JEGLG9s48TWHTJg8S": (1.5, "-", "#30b537"), 
	"GXXjRkdquAkyHeJ6ReW3v4FY3QbgPfugTx": (2, "-", "#ff2626"),
	"the rest": (1.5, "-", "#22d2d8"),
	"market": (2, "-", "black"),
	"net": (1, ":", "#555555")
}
attackStamp = mktime(2018, 5, 18)



def getJsonResponse(url):
	try:
		return json.loads(urlrequest.urlopen(url).read().decode())
	except Exception as e:
		print("urlrequest error encountered: %s \n %s" % (repr(e), traceback.print_tb(e.__traceback__)))
		return False
	 
def downloadBtgOrphans(getBlocks=True):
	# 306 missing transactions out of 4967
	blockUri = "http://btgexp.com/api/getblock?hash=%s"
	transactionUri = "http://btgexp.com/api/getrawtransaction?txid=%s&decrypt=1"
	blockNinja = getBlockNinja()
	outputPath = os.path.join("data","btg-orphaned-transactions.json")
	
	def getOrphan(symbol, blockhash):
		path = os.path.join("orphans", symbol, "%s.json" % blockhash)
		if os.path.isfile(path):
			with open(path, "r") as f:
				print("--file found")
				return json.loads(f.read())
		print("--downloading block")
		block = getJsonResponse(blockUri % tip["hash"])
		if not block:
			return block
		if block["confirmations"] > 0:
			print("Confirmed block found.")
			return False
		saveOrphan(symbol, block)
		time.sleep(0.5)
		return block
	
	def saveOrphan(symbol, block):
		dirpath = "orphans"
		mkdir(dirpath)
		dirpath = os.path.join("orphans", symbol)
		mkdir(dirpath)
		blockhash = block["hash"]
		print("saving orphaned block from height %i" % block["height"])
		with open(os.path.join(dirpath, "%s.json" % blockhash), "w") as f:
			f.write(json.dumps(block))

	def getTransaction(symbol, txid):
		path = os.path.join("orphans", symbol, "tx", "%s,json" % txid)
		if os.path.isfile(path):
			with open(path, "r") as f:
				return json.loads(f.read())
		transaction = blockNinja.getRawTransaction(symbol, txid, 1)
		if transaction:
			return transaction
		else:
			return False
		# print("attempting to download transaction %s" % txid)
		# transaction = getJsonResponse(transactionUri % txid)
		# if not transaction:
		# 	return transaction
		# saveTransaction(symbol, transaction)
		# time.sleep(0.5)
		# return transaction


	def saveTransaction(symbol, transaction):
		dirpath = "orphans"
		mkdir(dirpath)
		dirpath = os.path.join(dirpath, symbol)
		mkdir(dirpath)
		dirpath = os.path.join(dirpath, "tx")
		mkdir(dirpath)
		print("saving transaction %s" % transaction["txid"])
		with open(os.path.join(dirpath, "%s.json" % transaction["txid"]), "w") as f:
			f.write(json.dumps(transaction))
	if getBlocks:
		symbol = "BTG"
		totalTxs = 0
		missingTxs = []
		totalBlocks = sum([t["branchlen"] for t in revertedTips])
		numTips = len(revertedTips)
		i = 0
		for k, tip in enumerate(revertedTips):
			print("!!!!!!!!!!!!! beginning to parse chain %i/%i with length %i" % (k, len(revertedTips), tip["branchlen"]))
			blockhash = tip["hash"]
			branchlen = tip["branchlen"]
			m = 0
			for _ in range(branchlen):
				m += 1
				i += 1
				block = getOrphan(symbol, blockhash)
				if not block:
					break
				print("########### block %i/%i in chain- %i/%i total, %i confirmations ###########" % (m, branchlen, i, totalBlocks, block["confirmations"]))
				numTxs = len(block["tx"])
				totalTxs += numTxs
				for j, txid in enumerate(block["tx"]):
					transaction = getTransaction(symbol, txid)
					if not transaction:
						missingTxs.append((blockhash, block["height"], block["time"], txid))
					else:
						print(block["height"])
						blk = blockNinja.getBlock(symbol, transaction["blockhash"])
						exit(json.dumps(blk, indent=4, sort_keys=True))
				blockhash = block["previousblockhash"]
				print(json.dumps(block, indent=4, sort_keys=True))
		print("%i missing transactions out of %i" % (len(missingTxs), totalTxs))
		print("\n".join([repr(tx) for tx in missingTxs]))
		with open(outputPath, "w") as f:
			f.write(json.dumps(missingTxs))
	with open(outputPath, "r") as f:
		missingTxs = json.loads(f.read())


	exit("%i missing transactions" % len(missingTxs))


	for blockhash, height, tStamp, txid in missingTxs:
		transaction = getJsonResponse(transactionUri % txid)
		if transaction:
			exit(json.dumps(transaction, indent=4, sort_keys=True))
		else:
			print("no transaction found")
		time.sleep(1)






# blockNinja = getBlockNinja()
# symbol = "BTG"
# transaction = blockNinja.getRawTransaction(symbol, "46b840718bf64aae5eccb69fa1227c5f2c532127d42a09c29ac18b259d427880", 1)
# # tip = blockNinja.getTip(symbol)
# exit(json.dumps(transaction, indent=4, sort_keys=True))

# getFirstLastPairs("ETC")
# processRawData(["ETC"])
# plotThing("power", start=start, end=end)
# plotEnergyCurves()
# getMinerStats("BTG")
# plotAddresses("BTG", addresses, attackStamp-86400*9, attackStamp+86400*5, threshold=None, plotRemainder=True, styles=styles, rebuild=False)
# plotMinerStats(["ZEC", "BTG", "ETH", "ETC"], rebuild=True, startFrame=None, endFrame=None, snapshot=None, framesPerDay=2, averagingLength=7)
# plotGrid(["ETH", "ETC", "ZEC", "BTG"], plot="high", columns=1, func="dayblock", sharex=True)
# plotTheLeader(["ZEC", "BTG", "ETH", "ETC"])
# plotRetailCapital()
# followTheMoney("ETH", startStamp=mktime(2018, 1, 1), endStamp=None, integrationLength=7)
# plotTheMoney("ETH")
# plotBlockHistogram(rebuild=False)
# blockLog(rebuild=False)
blockNinja = getBlockNinja()
exit()
plotHashrateLengths(rebuild=False)
# plotTransactions("BTG")
# rawBlockUri = "http://explorer.bitcoingold.org/insight-api/tx/%s" 
# exit(json.dumps(getJsonResponse(rawBlockUri % "4ee06e82ee99615bc94ea4e390210491192c0b6c3db8482611411d138e6101fa")))

# blockNinja = getBlockNinja()
# symbol = "BTG"
# exit(json.dumps(blockNinja.getBlockByHeight(symbol, 529022), indent=4, sort_keys=True))

# downloadBtgOrphans()

