import itertools
import datetime
import wsclient
import logging
import redis
import time
import sys
import os

parameters  = {'start_amount_btc': 0.025,
	       'start_amount_eur': 100,
	       'start_amount_usd': 100,
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
#client_redis = redis.StrictRedis(host='localhost', port=6379, db=0)

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
		print "Empty orderbook. Resubscribing.. " + currency + " : " + conversion
                subscribe(currency, conversion)
                time.sleep(1)

def subscribe(currency, conversion):
        client_bitstamp_ws.subscribe("order_book", currency, conversion)

def possibletrasactions():
	currencies = []
	transactions = []

	for type in directions:
		type_dic = directions[type]
		for currency in type_dic:
			currency_dic = type_dic[currency]
			for trx in currency_dic:
				currencies.append(trx)

	currencies = list(set(currencies))
	permutations = list(itertools.permutations(currencies))

	for trx_flow in permutations:
		trx_flow = list(trx_flow)
		currency = trx_flow[0]
		trx_flow.append(currency)
		transactions.append(trx_flow)

	return transactions

def evaluateConversion(history):
	global counters

	print history

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
	transactions = possibletrasactions()

	for transaction in transactions:
		trx_details = {}
		for currency in transaction:
			if 'from_currency' in trx_details:
				trx_details['to_currency'] = currency
				trx_details = checkProfitability(order_book, trx_details)
			else:
				trx_details['from_currency'] = currency
				trx_details['from_amount'] = parameters['start_amount_' + currency]
				trx_details['start_amount'] = parameters['start_amount_' + currency]

		updateCounters(transaction, trx_details)
		print trx_details
		print "---------------------------------------------------------------------------------------"

def updateCounters(transaction, trx_details):
	global counters
	string = ""
                
	for currency in transaction:
		string += str(currency)

	if 'sucess_' + string not in counters:
		counters['sucess_' + string] = 0

	if 'ratio_' + string not in counters:
		counters['ratio_' + string] = 0

	if 'highest_ratio_' + string not in counters:
		counters['highest_ratio_' + string] = 0

	counters['sucess_' + string] = increaseValue(trx_details['start_amount'], trx_details['from_amount'], counters['sucess_' + string])
	counters['ratio_' + string] = trx_details['from_amount'] / trx_details['start_amount']
	counters['highest_ratio_' + string] = compare_and_update(counters['highest_ratio_' + string],  counters['ratio_' + string])


def checkProfitability(order_book, trx_details):
	global parameters

	print trx_details

	from_amount = trx_details['from_amount']
	from_currency = trx_details['from_currency']
	to_currency = trx_details['to_currency']
	directions_buy = directions['buy']
	directions_sell = directions['sell']

	if from_currency in directions_buy:
		if to_currency in directions_buy[from_currency]:
			for conversion in directions_buy[from_currency]:
				to_amount = buy(order_book, from_currency, to_currency, parameters['adjustment'], from_amount)

	if from_currency in directions_sell:
		if to_currency in directions_sell[from_currency]:
        	        for conversion in directions_sell[from_currency]:
                	        to_amount = sell(order_book, from_currency, to_currency, parameters['adjustment'], from_amount)

	trx_details['from_amount'] = to_amount
	trx_details['from_currency'] = to_currency

	return trx_details

# ------ START HERE

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()
		doStuff(order_book)
		for key in sorted(counters):
		    print "%s: %s" % (key, counters[key])
