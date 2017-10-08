import datetime
import wsclient
import logging
import redis
import time
import sys
import os

parameters  = {'start_money_value': 1,
	       'commision': 0.0025,  # 0.25%
	       'adjustment': 0.00001, } # smallest value on b1tstamp?

conversions = {'btc': {'usd', 'eur'}, 
               'eur': {'usd'}}

directions  = {'buy': {'eur': {'btc', 'usd'}, 
                       'usd': {'btc'}},
	       'sell': {'btc': {'eur', 'usd'},
                        'eur': {'usd'}}}

counters = {}

logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)
loggerHandler = logging.FileHandler('/tmp/bitstamp-' + os.path.basename(__file__) + '.log')
logger.addHandler(loggerHandler)
logger.setLevel(logging.WARNING) # TODO: This doesn't work

client_bitstamp_ws = wsclient.BitstampWebsocketClient()
client_redis = redis.StrictRedis(host='localhost', port=6379, db=0)

def fetchOrderBook():
        self = {}

	for currency in conversions:
		for conversion in conversions[currency]:
			checkOrderBook(currency, conversion)
			self[currency + conversion + '_ask_v'] = float(client_bitstamp_ws.orderbook[currency][conversion]['asks'][0][0])
			self[currency + conversion + '_bid_v'] = float(client_bitstamp_ws.orderbook[currency][conversion]['bids'][0][0])

        return self

def checkOrderBook(currency, conversion):
        while ('asks' and 'bids') not in client_bitstamp_ws.orderbook[currency][conversion]:
		print "Empty orderbook. Resubscribing.." + currency + " : " + conversion
                subscribe(currency, conversion)
                time.sleep(1)

def subscribe(currency, conversion):
        client_bitstamp_ws.subscribe("order_book", currency, conversion)

def eur2btc(start_money, order_book, adjustment):
	global counters
	notice = ''

	if adjustment != 'false':
		notice = 'ADJUSTED'

	self = {}
	self['btc'] = buy(order_book, 'eur', 'btc', adjustment, start_money) # buy btc with eur
	self['usd'] = sell(order_book, 'btc', 'usd', adjustment, self['btc']) # sell btc for usd
	self['eur'] = buy(order_book, 'usd', 'eur', adjustment, self['usd']) # buy eur with usd

	ratio_eur = self['eur'] / start_money
	if ratio_eur > 1:
		executeBuy(start_money, self)

	counters['highest_ratio_eur'] = compare_and_update(counters['highest_ratio_eur'], ratio_eur)
	counters['success_eur'] = increaseValue(start_money, self['eur'], counters['success_eur'])

	if adjustment != 'false':
		notice = 'ADJUSTED'

	conversionPrinter("EUR", start_money,
			  "BTC", self['btc'],
			  "USD", self['usd'],
			  "EUR", self['eur'],
			  ratio_eur, highest_ratio_eur, success_eur, notice)

def eur2usd(start_money, order_book, adjustment):
	global success_usd
        global highest_ratio_usd
	notice = ''

	self = {}
	self['usd'] = sell(order_book, 'eur', 'usd', commision, adjustment, start_money) # sell eur for usd
	self['btc'] = buy(order_book, 'usd', 'btc', commision, adjustment, self['usd']) # buy btc with usd
	self['eur'] = sell(order_book, 'btc', 'eur', commision, adjustment, self['btc']) # sell btc for eur

	ratio_usd = self['eur'] / start_money
	if ratio_usd > 1:
                executeBuy(start_money, self)

	counters['highest_ratio_usd'] = compare_and_update(highest_ratio_usd, ratio_usd)
	counters['success_usd'] = increaseValue(start_money, self['eur'], success_usd)

        if adjustment != 'false':
                notice = 'ADJUSTED'

        conversionPrinter("EUR", start_money,
                          "USD", self['usd'],
                          "BTC", self['btc'],
                          "EUR", self['eur'],
                          ratio_usd, highest_ratio_usd, success_usd, notice)

def conversionPrinter(startCur, start_money, firstX, firstV, secondX, secondV, thirdX, thirdV, ratio, ratioH, success, notice):
	print (startCur,": ",start_money,
	         firstX,": ",round(firstV, 5),
	        secondX,": ",round(secondV, 5),
		 thirdX,": ",round(thirdV, 5),
		  "(ratio: ",ratio,
	     ", max ratio: ",ratioH,
	       ", success: ",success,notice)

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

def buy(orderbook, fromCurrency, toCurrency, adjustment, amount):
	global parameters

	if adjustment == 'false':
		self = ((amount / orderbook[toCurrency + fromCurrency + '_ask_v']) - 
		       ((amount / orderbook[toCurrency + fromCurrency + '_ask_v']) * parameters['commision']))
		return self

	self = ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) - 
	       ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) * parameters['commision']))

	return self

def sell(orderbook, fromCurrency, toCurrency, adjustment, amount):
	if adjustment == 'false':
		self = ((amount * orderbook[fromCurrency + toCurrency + '_bid_v']) - 
		       ((amount * orderbook[fromCurrency + toCurrency + '_bid_v']) * parameters['commision']))
		return self

	self = ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) - 
	       ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) * parameters['commision']))

	return self

def doStuff(order_book):
	global parameters
	global directions

	eur2btc(parameters['start_money_value'], order_book, 'false')
	eur2btc(parameters['start_money_value'], order_book, parameters['adjustment'])
	eur2usd(parameters['start_money_value'], order_book, 'false')
	eur2usd(parameters['start_money_value'], order_book, parameters['adjustment'])

# ------ START HERE

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()
		doStuff(order_book)
