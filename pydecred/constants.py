import os

# A few usefule constants.
INF = float("inf")
PACKAGEDIR = os.path.dirname(os.path.realpath(__file__))
HEADERS = {'Content-Type': 'application/json'}
MINUTE = 60
DAY = 86400
HOUR = 3600
PRIME_POWER_RATE = 0.05
SYMBOL = "DCR"
CMC_TOKEN = "decred"

# MODEL_DEVICE is edited in calc.py
MODEL_DEVICE = {
    "model": "INNOSILICON D9 Miner",
    "price": 1699,
    "release":  "2018-04-18",
    "hashrate": 2.1e12,
    "power": 900
}