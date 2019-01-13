import os, sys, re, random, string, time, calendar
import math
import multiprocessing
import json
import logging
import traceback
import socket
from collections import OrderedDict
import sqlite3, psycopg2
import urllib.request as urlrequest

# A few globals
INF = float("inf")
VERBOSITY = 1 # 0->low, 1->normal, 2->high
PACKAGEDIR = os.path.dirname(os.path.realpath(__file__))
HEADERS = {'Content-Type': 'application/json'}
A_DAY = 86400
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

MODEL_DEVICE = {
	"model" : "INNOSILICON D9 Miner",
	"price" : 1699,
	"release" :  "2018-04-18",
	"hashrate" : 2.1e12,
	"power" : 900
}

MODEL_DEVICE["daily.power.cost"] = PRIME_POWER_RATE*MODEL_DEVICE["power"]/1000*24
MODEL_DEVICE["min.profitability"] = -1*MODEL_DEVICE["daily.power.cost"]/MODEL_DEVICE["price"]
MODEL_DEVICE["power.efficiency"] = MODEL_DEVICE["hashrate"]/MODEL_DEVICE["power"]
MODEL_DEVICE["relative.price"] = MODEL_DEVICE["price"]/MODEL_DEVICE["hashrate"]

# For AESCipher
import hashlib, base64
import pyaes

# For bcrypt functions
import bcrypt
import binascii

# For logging
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger("dcr-params")

def isList(o):
	#return isinstance(o,(list, tuple, np.ndarray, zip))
	return isinstance(o,(list, tuple, zip))

def isNumeric(o):
	#return isinstance(o, (int, float, np.integer, np.floating))
	return isinstance(o, (int, float))

def fancyFraction(num, denom):
	""" ZeroDivisionError goes to zero"""
	try:
		return num/denom
	except ZeroDivisionError as e:
		return 0

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

def abridgeString(ipStr, headLen, tailLen):
	""" Returns an abridged, ellipses-connected string"""
	strLen = len(ipStr)
	if(strLen > (headLen + tailLen+3)):
		return ipStr[0:headLen]+"..."+ipStr[strLen-tailLen:]
	return ipStr

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
	def __init__(self, atsDict={}, **kwargs):
		for k, v in atsDict.items():
			setattr(self, k, v)
		for k, v in kwargs.items():
			setattr(self, k, v)

class AESCipher(object):
	"""AES encryption and decryption class from user mnothic at http://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256"""
	def __init__(self): 
		self.bs = 32
		#self.iv = b'\xf5\xae3p@\xa8\xe9Z1\x8c\x87\x02\x9f\x11\xad2'
	def encrypt(self, pin, raw):
		N = random.randint(16,32)
		userKey = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(N))
		combinedKey = userKey+pin
		key = hashlib.sha256(combinedKey.encode()).digest()
		raw = self._pad(raw)
		cipher =  pyaes.AESModeOfOperationCTR(key)# This -> AES.new(key, AES.MODE_CBC, iv) is for pyCrypto, which might be better, but is huge and must be compiled.
		return (userKey, base64.b64encode(cipher.encrypt(raw)).decode('utf-8'))
	def decrypt(self, pin, userKey, enc):
		enc = base64.b64decode(enc)
		combinedKey = userKey+pin
		key = hashlib.sha256(combinedKey.encode()).digest()
		cipher = pyaes.AESModeOfOperationCTR(key)  # This -> AES.new(key, AES.MODE_CBC, iv) is for pyCrypto, which might be better, but is huge and must be compiled.
		return self._unpad(cipher.decrypt(enc)).decode('utf-8')
	def _pad(self, s):
		return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
	@staticmethod
	def _unpad(s):
		return s[:-ord(s[len(s)-1:])]

def bcryptHashPassword(password):
	""" BCrypt encryption"""
	return binascii.hexlify(bcrypt.hashpw(password.encode(), bcrypt.gensalt())).decode("utf8")

def bcryptCheckPassword(password, hashed):
	return bcrypt.checkpw(password.encode(), binascii.unhexlify(hashed))

def splitUri(uri):
		"""
		Split the uri into protocol, base, port
		"""
		m = re.match(r"^([^:/]+)://([^:]+):([0-9]+)$", uri)
		if m:
			return m.group(1), m.group(2), int(m.group(3))
		m = re.match(r"^([^:/]+)://([^:]+)$", uri)
		if m:
			return m.group(1), m.group(2), 80
		m = re.match(r"^([0-9a-zA-Z._-]+):([0-9]+)$", uri)
		if m:
			return "http", m.group(1), int(m.group(2))
		return None, uri, 80

def userHasInternet(host="8.8.8.8", port=53, timeout=3):
	"""
	Host: 8.8.8.8 (google-public-dns-a.google.com)
	OpenPort: 53/tcp
	Service: domain (DNS/TCP)
	"""
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except socket.timeout:
		logger.warning("No internet connection detected")
		return False
	except Exception as e:
		logger.warning("userHasInternet error: %s" % repr(e))
	return False

def pingAddress(host, port, timeout=3):
	"""
	Send a get request to the address and don't wait for the result
	"""
	try:
		socket.setdefaulttimeout(timeout)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		s.send(b"\n")
		return True
	except Exception as e:
		logger.warning("pingAddress error: %s" % repr(e))
	return False

def formatNumber(number, billions="B", spacer=" ", isMoney = False):
		""" 
		Format the number to a string with max 3 sig figs, and appropriate unit multipliers

		:param number:	The number to format
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
		# 	return "%.2f%s" % (absVal, spacer)
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

class Archivist:
	"""
	Database stuff
	"""
	def __init__(self, logger):
		self.logger = logger
		self.printQuerys = False
		self.tables = []
		self.connect()
	def connect(self):
		print("Archivist.connect must be implemented in subclass.")
	def errorParams(self, query, err):
		"""Generate a standard set of ArchiveError parameters from a query and error"""
		name = type(err).__name__
		message = (
			"An {errorType} exception occured when trying to perform the query {query}. \n"
			"The following error data was returned \n {args} : {traceback}"
			).format(
			errorType=name, 
			query = query, 
			args = err.args, 
			traceback = traceback.print_tb(err.__traceback__) 
		)
		return name, message
	def unimplimented(self, functionName):
		return "UNIMPLEMENTED", "%s must be implemented in an inheriting class"
	def addTable(self, table):
		self.tables.append(table)
		if not self.tableExists(table.name):
			self.makeTable(table)
		else:
			self.justifyTable(table)
	def getQueryResults(self, query, params=None, firstTry = True, dictKeys=None):
		"""perform the query and return the results as a list of tuples"""
		try:
			if self.printQuerys:
				print(query)
			cursor = self.conn.cursor()
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)
			if dictKeys:
				rows = cursor.fetchall()
				retList = []
				if rows and len(rows[0]) != len(dictKeys):
					raise ArchiveException("dictKeys.length.error", "getQueryResults result row size does not match the size of provided dictKeys for query\n{}".format(query)) 
				for row in rows:
					retList.append(dict(zip(dictKeys, row)))
				return retList
			return cursor.fetchall()
		except Exception as e:
			raise ArchiveException(*self.errorParams(query, e))
		finally:
			cursor.close()
	def performQuery(self, query, params=None, firstTry = True, returnId = False, commit = True):
		""" Perform query. Return True on success, false on failure"""
		try:
			if self.printQuerys:
				print(query)
			cursor = self.conn.cursor()
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)
			if commit:
				self.conn.commit()
			if returnId:
				return cursor.lastrowid
			return True
		except Exception as e:
			raise ArchiveException(*self.errorParams(query, e))
		finally:
			cursor.close()
	def batchInsert(self, query, paramsList):
		"""
		Similar to perform query, but doesn't commit until the end
		"""
		for params in paramsList:
			self.performQuery(query, params, commit=False)
		self.conn.commit()
		return True
	def tableExists(self, name):
		"""return True if the table exists, else false"""
		raise ArchiveException(*self.unimplemented("tableExists"))
	def makeTable(self, table):
		"""Make a table from the given structure"""
		raise ArchiveException(*self.unimplemented("tableExists"))
	def justifyTable(self, table):
		""" 
		Check that database structure matches structure of given table. Add columns if necessary.
		In switch to sqlite, disabled updating of primary keys. Fix that sometime. 
		"""
		raise ArchiveException(*self.unimplemented("tableExists"))

class SQLiteArchivist(Archivist):
	def __init__(self, filepath, logger):
		self.filepath = filepath
		super(SQLiteArchivist, self).__init__(logger)
	def connect(self):
		try:
			self.conn = sqlite3.connect(self.filepath)
		except Exception as e:
			raise ArchiveException(*self.errorParams("connect", e))
	def tableExists(self, name):
		"""return True if the table exists, else false"""

		cursor = self.conn.cursor()
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (name,))
	def makeTable(self, table):
		"""Make a table from the given structure"""
		columnDefs = []
		for column in table.columns:
			name = column['name']
			if name == table.primaryKey:
				if column["type"].lower() == "int":
					d = '%s INTEGER PRIMARY KEY NOT NULL' % name
				else:
					d = ' '.join([name, column["type"], 'PRIMARY KEY NOT NULL'])
			else:
				d = '%s %s' % (name, column['type'])
				if column['notNull']:
					d = ' '.join([d,'NOT NULL'])
				if column['autoIncrement']:
					d = ' '.join([d,'AUTOINCREMENT'])
				if column['default'] is not None:
					if isinstance(column['default'], stringType):
						column['default'] = "'%s'" % column['default']
					d = ' '.join([d,'default %s' % column['default']])
			columnDefs.append(d)
		for indices in table.uniqueIndices:
			columnDefs.append(
				"CONSTRAINT {} UNIQUE ({})".format(
					"_".join([table.name, *indices]),
					",".join(indices)
				)
			)
		for column, otherTable, otherColumn in table.foreignKeys:
			columnDefs.append(
				"FOREIGN KEY({}) REFERENCES {}({})".format(
					column,
					otherTable,
					otherColumn
				)
			)
		query = 'CREATE TABLE %s(%s)' % (table.name,','.join(columnDefs))
		self.logger.info('Creating new table. Performing query: %s' % query)
		if not self.performQuery(query):
			return False
		return True
	def justifyTable(self, table):
		""" 
		Check that database structure matches structure of given table. Add columns if necessary.
		In switch to sqlite, disabled updating of primary keys. Fix that sometime. 
		"""
		query = 'PRAGMA table_info([%s]);' % table.name
		columns = {}
		columnNames = []
		for cols in self.getQueryResults(query):
			colId, name, columnType, notNull, default, isPrimaryKey = cols
			columnType = columnType.replace("auto_increment", "").strip()
			columns[name]  = Generic_class({'type': columnType, 'notNull': bool(notNull), 'isPrimaryKey':bool(isPrimaryKey), 'default': default})
			columnNames.append(name)
		for column in table.columns:
			# sqlite does not let you add a primary key after table creation
			if column['name'] not in columnNames:
				self.logger.warning('Missing columns found in table %s. Recreating table.' % (table.name, ))
				query = "DROP TABLE IF EXISTS %s" % table.name
				self.performQuery(query)
				self.makeTable(table)
				return True
			else:
				columnNames.remove(column['name'])
		if len(columnNames) > 0:
			self.logger.warning('Extra columns found in table %s. Recreating table.' % (table.name, ))
			query = "DROP TABLE IF EXISTS %s" % table.name
			self.performQuery(query)
			self.makeTable(table)
			return True

class PostgreArchivist(Archivist):
	timeFmt = "%Y-%m-%d %H:%M:%S"
	def __init__(self, dbname, host, user, password, logger):
		self.dbname = dbname
		self.host = host
		self.user = user
		self.password = password
		super(PostgreArchivist, self).__init__(logger)
	def connect(self):
		try:
			self.conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (self.dbname, self.user, self.host, self.password))
		except Exception as e:
			raise ArchiveException(*self.errorParams("\\connect", e))
	@staticmethod
	def timeStringToUnix(fmtStr):
		return calendar.timegm(time.strptime(fmtStr, PostgreArchivist.timeFmt))

class ArchiveException(Exception):
	"""
	Custom exception to be thrown from Archivist
	"""
	def __init__(self, name, message):
		self.name = name
		self.message = message

class DatabaseTable:
	def __init__(self, name):
		self.name = name
		self.columns = []
		self.foreignKeys = []
		self.primaryKey = None
		# self.uniqueKeys = []
		self.uniqueIndices = []
	def addColumn(self, name, dataType, notNull=False, autoIncrement=False, default=None):
		column = {}
		column['name'] = name
		column['type'] = dataType
		column['notNull'] = notNull
		column['autoIncrement'] = autoIncrement
		column['default'] = default
		self.columns.append(column)
	def addForeignKey(self, column, otherTable, otherColumn):
		self.foreignKeys.append((column, otherTable, otherColumn))
	def addPrimaryKey(self, key):
		self.primaryKey = key
	def addUniqueKey(self, *keys):
		return self.addUniqueIndex(*keys)
	def addUniqueIndex(self, *indices):
		self.uniqueIndices.append(indices)

def mkdir(path):
	if os.path.isdir(path):
		return True
	if os.path.isfile(path):
		return False
	os.makedirs(path)
	return True

def yearmonthday(t):
	return tuple(int(x) for x in time.strftime("%Y %m %d", time.gmtime(t)).split())

def mktime(year, month=None, day=None):
	if month:
		if day:
			return calendar.timegm(time.strptime("%i-%s-%s" % (year, str(month).zfill(2), str(day).zfill(2)), "%Y-%m-%d"))
		return calendar.timegm(time.strptime("%i-%s" % (year, str(month).zfill(2)), "%Y-%m"))
	return calendar.timegm(time.strptime(str(year), "%Y"))

def dt2stamp(dt):
	return int(time.mktime(dt.timetuple()))

def stamp2dayStamp(stamp):
	return int(mktime(*yearmonthday(stamp)))

def ymdString(stamp):
	return ".".join([str(x).zfill(2) for x in yearmonthday(stamp)])

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

def hueGenerator():
	denominator = 2
	numerator = 1
# todo: translate from js
#	 this.generateHue = function(){
 #        // Generates colors on the sequence 0, 1/2, 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, 1/16, ...
 #        while(self.colorDenominator < 512){ //Should generate a little more than 100 unique values
 #            if(self.colorNumerator == 0){
 #                self.colorNumerator += 1
 #                return 0;
 #            }
 #            if(self.colorNumerator >= self.colorDenominator){
 #                self.colorNumerator = 1; // reset the numerator
 #                self.colorDenominator *= 2; // double the denominator
 #                continue;
 #            }
 #            hue = self.colorNumerator/self.colorDenominator*360
 #            self.colorNumerator += 2;
 #            return hue
 #        }
 #        self.colorNumerator = 0
 #        self.colorDenominator = 2
 #        return self.generateHue()
 #    }

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

# DCR Utilities

# def honestMult(stakeportion, winners=TICKETS_PER_BLOCK, participation=1):
# 	return ((1/stakeportion - 1)*participation)**winners

def binomial(n, k):
	f = math.factorial
	return f(n)/f(k)/f(n-k)

def honestMult(stakeportion, winners=TICKETS_PER_BLOCK, participation=1):
	halfN = winners/2.
	k = 0
	probability = 0
	while k < halfN:
		probability += binomial(winners, k)*stakeportion**(winners-k)*((1-stakeportion)*participation)**k
		k += 1
	if probability == 0:
		print("Quitting with parameters %s" % repr((stakeportion, winners, participation)))
	return 1/probability - 1

def hashportion(stakeportion, winners=TICKETS_PER_BLOCK, participation=1):
	m = honestMult(stakeportion, winners)
	return m/(m+1)

def grossEarnings(device, roi, energyRate=PRIME_POWER_RATE):
	return roi*device["price"] + 24*device["power"]*energyRate/1000

def blockReward(height):
	# https://docs.decred.org/advanced/inflation/
	return 31.19582664*(100/101)**int(height/6144)

def dailyPowRewards(height, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
	return A_DAY/blockTime*blockReward(height)*powSplit


def networkDeviceCount(device, xcRate, roi, height=3e5, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
	return dailyPowRewards(height, blockTime, powSplit)*xcRate/grossEarnings(device, roi)

def networkHashrate(device, xcRate, roi, height=3e5, blockTime=BLOCKTIME, powSplit=POW_SPLIT):
	return networkDeviceCount(device, xcRate, roi, height, blockTime, powSplit)*device["hashrate"]

def calcTicketPrice(apy, height, winners=TICKETS_PER_BLOCK, stakeSplit=STAKE_SPLIT):
	Rpos = stakeSplit*blockReward(height)
	return Rpos/(winners*((apy + 1)**(25/365.) - 1))

class Ay:
	def __init__(self, retailTerm, rentalTerm, stakeTerm, stakeOwnership):
		self.retailTerm = retailTerm
		self.rentalTerm = rentalTerm
		self.stakeTerm = stakeTerm
		self.workTerm = rentalTerm + retailTerm
		self.attackCost = retailTerm + rentalTerm + stakeTerm
		self.stakeOwnership = stakeOwnership
	def __str__(self):
		return "<AttackCost: stakeOwnership %.3f, workTerm %i, stakeTerm %i, attackCost %i>" % (self.stakeOwnership, self.workTerm, self.stakeTerm, self.attackCost)

def AttackCost(stakeOwnership=None, xcRate=None, blockHeight=None, roi=None, ticketPrice=None, blockTime=BLOCKTIME, powSplit=None, 
		stakeSplit=None, treasurySplit=TREASURY_SPLIT, rentability=None, nethash=None, winners=TICKETS_PER_BLOCK, participation=1., 
		poolSize=TICKETPOOL_SIZE, apy=None, attackDuration=A_DAY/2, device=None, rentalRatio=None, rentalRate=None):
	if any([x is None for x in (stakeOwnership, xcRate, blockHeight)]):
		raise Exception("stakeOwnership, xcRate, and blockHeight are required args/kwargs for AttackCost")
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
	stakeTerm = stakeOwnership*poolSize*ticketPrice*xcRate
	hashPortion = hashportion(stakeOwnership, winners, participation)
	attackHashrate = nethash*hashPortion
	rent = rentability if rentability is not None else attackHashrate*rentalRatio if rentalRatio is not None else 0
	rentalPart = min(rent, attackHashrate)
	retailPart = attackHashrate - rentalPart
	rentalTerm = rentalPart*rentalRate/86400*attackDuration
	retailTerm = retailPart*( device["relative.price"] + device["power"]/device["hashrate"]*PRIME_POWER_RATE/1000/3600*attackDuration )
	attackCost = rentalTerm + retailTerm + stakeTerm
	return Ay(retailTerm, rentalTerm, stakeTerm, stakeOwnership)

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