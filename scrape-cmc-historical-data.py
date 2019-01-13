import os, json, datetime, time, random
from bs4 import BeautifulSoup
import urllib.request as urlrequest
from urllib.parse import urlencode as encodeUrl

class CMCScraper:
	def __init__(self, dataDir):
		self.dataDir = dataDir
		self.uriTemplate = "https://coinmarketcap.com/currencies/%s/historical-data/?start=%s&end=%s"
	def historyPath(self, symbol):
		return os.path.join(self.dataDir, symbol, "daily.json")
	def loadHistory(self, symbol):
		with open(self.historyPath(symbol), "r") as f:
			return json.loads(f.read())
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
		os.rename(tmpName, filename)
	def fetchHistory(self, symbol, token):
		""" Fetches historical data for a currency, and returns it as a list of data points"""
		history = self.loadHistory(symbol)
		if len(history):
			startStamp = history[-1]["timestamp"] + 1000 + random.random()*1000 # Add some random number of seconds
			startDateStr = time.strftime("%Y%m%d", time.gmtime(int(startStamp)))
		else:
			startDateStr = "20130428" # Date of the first bitcoin valuation ?
		dateStr = time.strftime("%Y%m%d")
		uri = self.uriTemplate % (token, startDateStr, dateStr)
		html = BeautifulSoup(urlrequest.urlopen(uri).read().decode(), "html.parser")
		dataRows = html.find("div", {"id": "historical-data"}).find("table",{"id","table"}).find("tbody").find_all("tr",{"class":"text-right"})
		headers = ["date.string","open","high","low","close","volume","market.cap"]
		dataPts = []
		for row in dataRows:
			rowObj = {}
			for i, td in enumerate(row.find_all("td")):
				if i == 0:
					try:
						rowObj[headers[i]] = td.get_text()
						rowObj["timestamp"] = datetime.datetime.strptime(td.get_text(),"%b %d, %Y").timestamp()
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
		self.saveHistory(symbol, history)
		return history




