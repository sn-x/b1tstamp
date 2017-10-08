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

directions  = {'buy': {'eur': {'btc'},
                       'usd': {'btc', 'eur'}},
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

def executeConversion(basics, order_book, adjustment, history):
	global directions
	notice = ''

	if history == 'false':
		history = {}
		history['depth'] = 0
		history['adjustment'] = adjustment
		history['start_value'] = basics['start_value']
		history['start_currency'] = basics['start_currency']
		history['working_value'] = basics['start_value']
		history['working_currency'] = basics['start_currency']

                basics['working_value'] = basics['start_value']
                basics['working_currency'] = basics['start_currency']

	working_value = basics['working_value']
	working_currency = basics['working_currency']
	directions_buy = directions['buy']
	directions_sell = directions['sell']
	depth = history['depth']

        if (history['depth'] > 10):
		evaluateConversion(history)
                sys.exit(1)

        if (history['depth'] > 3) and (history['start_currency'] == working_currency):
                evaluateConversion(history)
		sys.exit(1)

	if working_currency in directions_buy:
		for conversion in directions_buy[working_currency]:
			history[working_currency,"2",conversion,depth] = buy(order_book, working_currency, conversion, adjustment, working_value)
			basics['working_value']['buy'] = history[working_currency,"2",conversion,depth]
			basics['working_currency']['buy'] = conversion

        if working_currency in directions_sell:
                for conversion in directions_sell[working_currency]:
                        history[working_currency,"2",conversion,depth] = sell(order_book, working_currency, conversion, adjustment, working_value)
                        basics['working_value']['sell'] = history[working_currency,"2",conversion,depth]
                        basics['working_currency']['sell'] = conversion

	history['depth'] += 1
	executeConversion(basics, order_book, adjustment, history)

def evaluateConversion(history):
	global counters

	print history

#        if (start_currency +  notice) not in counters:
#                counters[start_currency + "-to-" +  ] = ''

#	if adjustment != 'false':
#        	        notice = 'ADJUSTED'

def buy(orderbook, fromCurrency, toCurrency, adjustment, amount):
	global parameters

	if adjustment == 'false':
		self = ((amount / orderbook[toCurrency + fromCurrency + '_ask_v']) - ((amount / orderbook[toCurrency + fromCurrency + '_ask_v']) * parameters['commision']))
		return self

	self = ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) - ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) * parameters['commision']))

	return self

def sell(orderbook, fromCurrency, toCurrency, adjustment, amount):
	if adjustment == 'false':
		self = ((amount * orderbook[fromCurrency + toCurrency + '_bid_v']) - ((amount * orderbook[fromCurrency + toCurrency + '_bid_v']) * parameters['commision']))
		return self

	self = ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) - ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) * parameters['commision']))

	return self

def executeBuy(start_money, conversions):
	print "nope"	

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

def doStuff(order_book):
	global parameters
	global directions

	basics = {}

	for type in directions:
		basics['type'] = type
		for currency in directions[type]:
			basics['start_currency'] = currency
			basics['start_value'] = parameters['start_money_value']
			for conversion in directions[type][currency]:
				basics['conversion'] = conversion
				adjustment = parameters['adjustment']
				executeConversion(basics, order_book, adjustment, 'false')
				sys.exit(0)

# ------ START HERE

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()
		doStuff(order_book)
