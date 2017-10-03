from auth import trading_client
import bitstamp.client
import datetime
import wsclient
import logging
import time
import os

start_money = 100 # EUR
commision = 0.0025 # 0.25%
adjustment = 0.00001 # smallest value on b1tstamp?

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
logger.setLevel(logging.WARNING) # TODO: This doesn't work

client = wsclient.BitstampWebsocketClient()
time.sleep(1) # lame hack - we can subscribe only after connection is established
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
	global success_eur
	global highest_ratio_eur
	adjustment = 'false'

	self = {}
	self['btc'] = buy(price, 'eur', 'btc', commision, adjustment, start_money) # buy btc with eur
	self['usd'] = sell(price, 'btc', 'usd', commision, adjustment, self['btc']) # sell btc for usd
	self['eur'] = buy(price, 'usd', 'eur', commision, adjustment, self['usd']) # buy eur with usd

	success_eur       = increaseValue(start_money, self['eur'], success_eur)
	ratio_eur         = self['eur'] / start_money
	highest_ratio_eur = compare_and_update(highest_ratio_eur, ratio_eur)

	conversionPrinter("EUR", start_money,
			  "BTC", self['btc'],
			  "USD", self['usd'],
			  "EUR", self['eur'],
			  ratio_eur, highest_ratio_eur, success_eur)


def eur2btc_c(start_money, price):
	global success_eur_c
	global highest_ratio_eur_c

	self = {}
        self['btc_c'] = buy(price, 'eur', 'btc', commision, adjustment, start_money) # buy btc with eur
        self['usd_c'] = sell(price, 'btc', 'usd', commision, adjustment, self['btc_c']) # sell btc for usd
        self['eur_c'] = buy(price, 'usd', 'eur', commision, adjustment, self['usd_c']) # buy eur with usd

	success_eur_c       = increaseValue(start_money, self['eur_c'], success_eur_c)
	ratio_eur_c         = self['eur_c'] / start_money
	highest_ratio_eur_c = compare_and_update(highest_ratio_eur_c, ratio_eur_c)


        conversionPrinter("EUR", start_money,
                          "BTC", self['btc_c'],
                          "USD", self['usd_c'],
                          "EUR", self['eur_c'],
                          ratio_eur_c, highest_ratio_eur_c, success_eur_c)

def eur2usd(start_money, price):
	global success_usd
        global highest_ratio_usd
	adjustment = 'false'

	self = {}
	self['usd'] = sell(price, 'eur', 'usd', commision, adjustment, start_money) # sell eur for usd
	self['btc'] = buy(price, 'usd', 'btc', commision, adjustment, self['usd']) # buy btc with usd
	self['eur'] = sell(price, 'btc', 'eur', commision, adjustment, self['btc']) # sell btc for eur

	success_usd       = increaseValue(start_money, self['eur'], success_usd)
	ratio_usd         = self['eur'] / start_money
	highest_ratio_usd = compare_and_update(highest_ratio_usd, ratio_usd)

        conversionPrinter("EUR", start_money,
                          "USD", self['usd'],
                          "BTC", self['btc'],
                          "EUR", self['eur'],
                          ratio_usd, highest_ratio_usd, success_usd)

def eur2usd_c(start_money, price):
	global success_usd_c
	global highest_ratio_usd_c

        self = {}
        self['usd_c'] = sell(price, 'eur', 'usd', commision, adjustment, start_money) # sell eur for usd
        self['btc_c'] = buy(price, 'usd', 'btc', commision, adjustment, self['usd_c']) # buy btc with usd
        self['eur_c'] = sell(price, 'btc', 'eur', commision, adjustment, self['btc_c']) # sell btc for eur

	success_usd_c       = increaseValue(start_money, self['eur_c'], success_usd_c)
	ratio_usd_c         = self['eur_c'] / start_money
	highest_ratio_usd_c = compare_and_update(highest_ratio_usd_c, ratio_usd_c)

        conversionPrinter("EUR", start_money,
                          "USD", self['usd_c'],
                          "BTC", self['btc_c'],
                          "EUR", self['eur_c'],
                          ratio_usd_c, highest_ratio_usd_c, success_usd_c)

def conversionPrinter(startCur, start_money, firstX, firstV, secondX, secondV, thirdX, thirdV, ratio, ratioH, success):
	output = (startCur,": ",start_money,
		    firstX,": ",round(firstV, 5),
		   secondX,": ",round(secondV, 5),
		    thirdX,": ",round(thirdV, 5),
		     "(ratio: ",ratio,
		", max ratio: ",ratioH,
		  ", success: ",success)

	print output

def increaseValue(first, second, third):
	self = third
        if second > first:
		self += 1

	return self

def compare_and_update(first, second):
	if second > first:
		self = second
	else:
		self = first

        return self

def buy(orderbook, fromCurrency, toCurrency, commision, adjustment, amount):
	if adjustment == 'false':
		self = (amount / orderbook[toCurrency + fromCurrency + '_ask_v']) - ((amount / orderbook[toCurrency + fromCurrency + '_ask_v']) * commision)
		return self

	self = ((amount / orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) - ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) * commision)
	return self

def sell(orderbook, fromCurrency, toCurrency, commision, adjustment, amount):
	if adjustment == 'false':
		self = (amount * orderbook[fromCurrency + toCurrency + '_bid_v']) - ((amount * orderbook[fromCurrency + toCurrency + '_bid_v']) * commision)
		return self

	self = (amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) - ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) * commision)
	return self

def doStuff(start_money, price):
	eur2btc(start_money, price)
	eur2btc_c(start_money, price)
	eur2usd(start_money, price)
	eur2usd_c(start_money, price)


# ------ START HERE

#while ('asks' and 'bids') not in client.orderbook['btc']['usd']:
#	time.sleep(0.1)
#while ('asks' and 'bids') not in client.orderbook['btc']['eur']:
#	time.sleep(0.1)
#while ('asks' and 'bids') not in client.orderbook['eur']['usd']:
#	time.sleep(0.1)

print(trading_client.account_balance()['fee'])

while True:
	price = fetchPrice()
	if price != fetchPrice():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()
#		doStuff(start_money, price)
