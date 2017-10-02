import datetime
import wsclient
import logging
import time
import os

start_money = 100 # EUR
commision = 0.0025 # 0.25%

success_eur = 0
success_eur_c = 0
success_usd = 0
success_usd_c = 0
highest_ratio_eur = 0
highest_ratio_eur_c = 0
highest_ratio_usd = 0
highest_ratio_usd_c = 0

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)
loggerHandler = logging.FileHandler('/tmp/bitstamp-' + os.path.basename(__file__) + '.log')
logger.addHandler(loggerHandler) 
logger.setLevel(logging.WARNING)

client = wsclient.BitstampWebsocketClient()
time.sleep(1) # we can subscribe only after connection is established
client.subscribe("order_book", "btc", "usd")
client.subscribe("order_book", "btc", "eur")
client.subscribe("order_book", "eur", "usd")

def fetchPrice():
	self = {}
        self['btcusd_ask_v'] = float(client.orderbook['btc']['usd']['asks'][0][0])
        self['btcusd_bid_v'] = float(client.orderbook['btc']['usd']['bids'][0][0])
        self['btceur_ask_v'] = float(client.orderbook['btc']['eur']['asks'][0][0])
        self['btceur_bid_v'] = float(client.orderbook['btc']['eur']['bids'][0][0])
        self['eurusd_ask_v'] = float(client.orderbook['eur']['usd']['asks'][0][0])
        self['eurusd_bid_v'] = float(client.orderbook['eur']['usd']['bids'][0][0])

        return self

def eur2btc(start_money, price):
	self = {}
	self['eur2btc'] = (start_money / price['btceur_ask_v']) - ((start_money / price['btceur_ask_v']) * commision)
	self['btc2usd'] = (self['eur2btc'] * price['btcusd_bid_v']) - ((self['eur2btc'] * price['btcusd_bid_v']) * commision)
	self['usd2eur'] = (self['btc2usd'] / price['eurusd_bid_v']) - ((self['btc2usd'] / price['eurusd_bid_v']) * commision)

	return self

def eur2btc_c(start_money, price):
	self = {}
        self['eur2btc_c'] = (start_money / (price['btceur_bid_v'] + 0.0000001)) - ((start_money / (price['btceur_bid_v'] + 0.0000001)) * commision)
        self['btc2usd_c'] = (self['eur2btc_c'] * (price['btcusd_ask_v'] - 0.01)) - ((self['eur2btc_c'] * (price['btcusd_bid_v'] - 0.01)) * commision)
        self['usd2eur_c'] = (self['btc2usd_c'] / (price['eurusd_bid_v'] + 0.001)) - ((self['btc2usd_c'] / (price['eurusd_bid_v'] + 0.001)) * commision)

	return self

def eur2usd(start_money, price):
	self = {}
	self['eur2usd'] = (start_money * price['eurusd_bid_v']) - ((start_money * price['eurusd_bid_v']) * commision)
	self['usd2btc'] = (self['eur2usd'] / price['btcusd_ask_v']) - ((self['eur2usd'] / price['btcusd_ask_v']) * commision)
	self['btc2eur'] = (self['usd2btc'] * price['btceur_bid_v']) - ((self['usd2btc'] * price['btceur_bid_v']) * commision)

	return self

def eur2usd_c(start_money, price):
	self = {}
        self['eur2usd_c'] = (start_money * (price['eurusd_bid_v'] + 0.0000001)) - ((start_money * (price['eurusd_bid_v'] + 0.0000001)) * commision)
        self['usd2btc_c'] = (self['eur2usd_c'] / (price['btcusd_ask_v'] - 0.01)) - ((self['eur2usd_c'] / (price['btcusd_ask_v'] - 0.01)) * commision)
        self['btc2eur_c'] = (self['usd2btc_c'] * (price['btceur_bid_v'] + 0.001)) - ((self['usd2btc_c'] * (price['btceur_bid_v'] + 0.001)) * commision)

	return self

def compare_and_update2more1(first, second, third):
	self = ""

	if third == "acme":
	        if second > first:
			self = second
		else:
			self = first
	else:
		self = third
	        if second > first:
			third += 1

	return self

# ------ START HERE

while 'asks' not in client.orderbook['btc']['usd']:
	time.sleep(0.1)
while 'bids' not in client.orderbook['btc']['usd']:
	time.sleep(0.1)
while 'asks' not in client.orderbook['btc']['eur']:
	time.sleep(0.1)
while 'bids' not in client.orderbook['btc']['eur']:
	time.sleep(0.1)
while 'asks' not in client.orderbook['eur']['usd']:
	time.sleep(0.1)
while 'bids' not in client.orderbook['eur']['usd']:
	time.sleep(0.1)

while True:
	price = fetchPrice()
	if price != fetchPrice():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()

		usd2eur = eur2btc(start_money, price)
		btc2eur = eur2usd(start_money, price)
		usd2eur_c = eur2btc_c(start_money, price)
		btc2eur_c = eur2usd_c(start_money, price)

		success_eur = compare_and_update2more1(start_money, usd2eur['usd2eur'], success_eur)
		success_usd = compare_and_update2more1(start_money, btc2eur['btc2eur'], success_usd)
		success_eur_c = compare_and_update2more1(start_money, usd2eur_c['usd2eur_c'], success_eur_c)
		success_usd_c = compare_and_update2more1(start_money, btc2eur_c['btc2eur_c'], success_usd_c)

		ratio_eur = usd2eur['usd2eur'] / start_money
		ratio_usd = btc2eur['btc2eur'] / start_money
		ratio_eur_c = usd2eur_c['usd2eur_c'] / start_money
		ratio_usd_c = btc2eur_c['btc2eur_c'] / start_money

		highest_ratio_eur = compare_and_update2more1(highest_ratio_eur, ratio_eur, "acme") # ACME from RoadRunner cartoons
		highest_ratio_usd = compare_and_update2more1(highest_ratio_usd, ratio_usd, "acme")
		highest_ratio_eur_c = compare_and_update2more1(highest_ratio_eur_c, ratio_eur_c, "acme")
		highest_ratio_usd_c = compare_and_update2more1(highest_ratio_usd_c, ratio_usd_c, "acme")

		print ""
                print datetime.datetime.now()
                print "EUR: ", start_money, " -> BTC:   ", round(usd2eur['eur2btc'], 5),     "-> USD:   ", round(usd2eur['btc2usd'], 5),     "\t-> EUR:   ", round(usd2eur['usd2eur'], 5),     "\t(ratio: ", ratio_eur,   ", success: ", success_usd, ", highest: ", highest_ratio_eur, ")"
                print "EUR: ", start_money, " -> BTC_c: ", round(usd2eur_c['eur2btc_c'], 5), "-> USD_c: ", round(usd2eur_c['btc2usd_c'], 5), "\t-> EUR_c: ", round(usd2eur_c['usd2eur_c'], 5), "\t(ratio: ", ratio_eur_c, ", success: ", success_usd_c, ", highest: ", highest_ratio_eur_c, ")"
	       	print datetime.datetime.now()
	        print "EUR: ", start_money, " -> USD:   ", round(btc2eur['eur2usd'], 5)    , "-> BTC:   ", round(btc2eur['usd2btc'], 5)    , "\t-> EUR:   ", round(btc2eur['btc2eur'], 5),     "\t(ratio: ", ratio_usd,   ", success: ", success_usd, ", highest: ", highest_ratio_usd, ")"
        	print "EUR: ", start_money, " -> USD_c: ", round(btc2eur_c['eur2usd_c'], 5), "-> BTC_c: ", round(btc2eur_c['usd2btc_c'], 5), "\t-> EUR_c: ", round(btc2eur_c['btc2eur_c'], 5), "\t(ratio: ", ratio_usd_c, ", success: ", success_usd_c, ", highest: ", highest_ratio_usd_c, ")"
