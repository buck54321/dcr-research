from commonfunctions import *
import os, json, datetime, time, random
from bs4 import BeautifulSoup
import urllib.request as urlrequest

def getUriAsJson(uri):
	req = urlrequest.Request(uri, headers=HEADERS, method="GET")
	return json.loads(urlrequest.urlopen(req).read().decode())

class CMCClient:
	def __init__(self, dataDir):
		self.dataDir = dataDir
		mkdir(dataDir)
		self.historyTemplate = "https://coinmarketcap.com/currencies/%s/historical-data/?start=%s&end=%s"
		self.tickerTemplate = "https://api.coinmarketcap.com/v1/ticker/%s/"
		self.maxCacheAge = A_DAY / 12
		self.settingsPath = os.path.join(dataDir, "settings.json")
		self.tempSettingsPath = os.path.join(dataDir, "settings.tmp.json")
		self.settings = fetchSettingsFile(self.settingsPath)
		if "price.cache" not in self.settings:
			self.settings["price.cache"] = []
		self.cache = self.settings["price.cache"]
	def saveSettings(self):
		with open(self.tempSettingsPath, 'w') as f:
			f.write(json.dumps(self.settings))
			f.flush()
			os.fsync(f.fileno())
		os.replace(self.tempSettingsPath, self.settingsPath)
	def historyPath(self, symbol):
		return os.path.join(self.dataDir, "%s.json" % symbol)
	def fetchPrice(self, token):
		i = 0
		cache = self.cache
		cacheLen = len(self.cache)
		stamp = time.time()
		minStamp = stamp - self.maxCacheAge
		data = None
		while True:
			if i >= cacheLen:
				break
			cacheToken, cacheStamp, cacheData = cache[i]
			if cacheStamp < minStamp:
				print("CMClient: expired cache data for %s" % cacheToken)
				cache.pop(i)
				cacheLen -= 1
				continue
			if token == cacheToken:
				data = cacheData
			i += 1
		if data:
			print("CMClient: returning cached data for %s" % token)
			return data
		data = getUriAsJson(self.tickerTemplate % token)
		cache.insert(0, (token, stamp, data))
		self.saveSettings()
		print("CMClient: returning new data for %s" % token)
		return data
	def loadHistory(self, symbol, keys=None):
		filepath = self.historyPath(symbol)
		if not os.path.isfile(filepath):
			return []
		with open(filepath, "r") as f:
			pts = json.loads(f.read())
			if not keys:
				return pts
			rows = []
			for pt in pts:
				row = [pt["timestamp"]]
				for key in keys:
					row.append(pt[key])
				rows.append(row)
			return rows
		return []
	def saveHistory(self, symbol, history):
		# see https://stackoverflow.com/a/2333979
		filename = self.historyPath(symbol)
		tmpName = "%s.tmp" % symbol
		with open(tmpName, "w") as f:
			f.write(json.dumps(history))
			f.flush()
			os.fsync(f.fileno())
			f.close()
		os.replace(tmpName, filename)
	def fetchHistory(self, symbol, token):
		""" Fetches historical data for a currency, and returns it as a list of data points"""
		history = self.loadHistory(symbol)
		if len(history):
			startStamp = history[-1]["timestamp"] + 1000 + random.random()*1000 # Add some random number of seconds
			startDateStr = time.strftime("%Y%m%d", time.gmtime(int(startStamp)))
		else:
			startDateStr = "20130428" # Date of the first bitcoin valuation ?
		dateStr = time.strftime("%Y%m%d")
		uri = self.historyTemplate % (token, startDateStr, dateStr)
		print("Fetching history")
		html = BeautifulSoup(urlrequest.urlopen(uri).read().decode(), "html.parser")
		print("parsing html")
		dataRows = html.find("div", {"id": "historical-data"}).find("table",{"id","table"}).find("tbody").find_all("tr",{"class":"text-right"})
		headers = ["date.string","open","high","low","close","volume","market.cap"]
		dataPts = []
		print("translating data")
		for row in dataRows:
			rowObj = {}
			for i, td in enumerate(row.find_all("td")):
				if i == 0:
					try:
						rowObj[headers[i]] = td.get_text()
						rowObj["timestamp"] = stamp2dayStamp(datetime.datetime.strptime(td.get_text(), "%b %d, %Y").timestamp())
					except Exception as e:
						print("failed to parse float from `%s`" % td.get_text())
						rowObj[headers[i]] = "Dec 31, 1999"
				elif i < 5:
					try:
						rowObj[headers[i]] = float(td.get_text())
					except Exception as e:
						print("failed to parse float from `%s`" % td.get_text())
						rowObj[headers[i]] = 0.0
				else:
					try:
						rowObj[headers[i]] = int(td.get_text().replace(",",""))
					except Exception as e:
						print("failed to parse integer from `%s`" % td.get_text())
						rowObj[headers[i]] = 0
			dataPts.append(rowObj)
		for pt in sorted(dataPts, key = lambda p: p["timestamp"]):
			if len(history) == 0 or pt["timestamp"] > history[-1]["timestamp"]:
				history.append(pt)
		# randoTime = 2.0 + random.random()*8 # Wait some random amount of time between 2 and 10 seconds
		# print("Processed %i new dates for %s. Fetching next symbol in %.2f seconds" % (len(dataPts), symbol, randoTime))
		# time.sleep(randoTime)
		print("saving history")
		self.saveHistory(symbol, history)
		return history




