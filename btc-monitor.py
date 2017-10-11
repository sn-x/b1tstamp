import itertools
import datetime
import wsclient
import logging
import redis
import time
import sys
import os


parameters  = {'start_amount_btc': 0.025,
	       'start_amount_ltc': 0.25,
	       'start_amount_eur': 100,
	       'start_amount_usd': 100,
	       'commision': 0.0025,  # 0.25%
	       'adjustment': 0.00001 } # smallest value on b1tstamp?

conversions = {'btc': {'usd', 'eur'},
               'eur': {'usd'},
               'ltc': {'usd', 'eur', 'btc'}}

directions  = {'buy': {'eur': {'btc', 'ltc'},
                       'usd': {'btc', 'eur', 'ltc'},
                       'btc': {'ltc'} },
               'sell': conversions }

counters = {'success': {}, 'ratio': {}, 'highest_ratio':{} }

client_bitstamp_ws = wsclient.BitstampWebsocketClient()
client_redis = redis.StrictRedis(host='localhost', port=6379, db=0)

def customLogger():
	logger = logging.getLogger()
	for handler in logger.handlers:
		logger.removeHandler(handler)
	loggerHandler = logging.FileHandler('/tmp/bitstamp-' + os.path.basename(__file__) + '.log')
	loggerHandler.setLevel(logging.WARNING)
	logger.addHandler(loggerHandler)

	return logger

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

def buy(orderbook, fromCurrency, toCurrency, adjustment, amount):
	self = ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) - 
	       ((amount / (orderbook[toCurrency + fromCurrency + '_bid_v']) + adjustment) * parameters['commision']))

	return self

def sell(orderbook, fromCurrency, toCurrency, adjustment, amount):
	self = ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) - 
	       ((amount * (orderbook[fromCurrency + toCurrency + '_ask_v']) - adjustment) * parameters['commision']))

	return self

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

def doStuff():
	history = {}
	order_book = fetchOrderBook()
	transactions = possibletrasactions()

	for transaction in transactions:
		trx_string = transactionString(transaction)
		trx_details = {}
		history.update({trx_string: {}})
		trx_step = 0
		for currency in transaction:
			if 'from_currency' in trx_details:
				trx_step += 1
				history[trx_string][trx_step] = {}
				trx_details['to_currency'] = currency
				results = calculateProfitability(order_book, trx_details, trx_string)
		                history[trx_string][trx_step].update(results['history'])
				trx_details = results['trx_details']
			else:
				trx_details['from_currency'] = currency
				trx_details['from_amount'] = parameters['start_amount_' + currency]
				trx_details['start_amount'] = parameters['start_amount_' + currency]

		updateCounters(transaction, trx_details, trx_string)

	return history

def highestValueTransaction(counters):
	transaction_values = []

	for transaction, value in counters['ratio'].items():
		transaction_values.append(value)

	transaction_values.sort(reverse=True)

	for transaction, value in counters['ratio'].items():
		if value == transaction_values[0]:
			return transaction

	print "Couldn't find highest value transaction. Fatal error."
	sys.exit(1)

def transactionString(transaction):
	string = ""
        for currency in transaction:
                string += str(currency)

	return string

def updateCounters(transaction, trx_details, string):
	global counters
                
	if string not in counters['success']:
		counters['success'][string] = 0

	if string not in counters['ratio']:
		counters['ratio'][string] = 0

	if string not in counters['highest_ratio']:
		counters['highest_ratio'][string] = 0

	counters['success'][string] = increaseValue(trx_details['start_amount'], trx_details['from_amount'], counters['success'][string])
	counters['ratio'][string] = trx_details['from_amount'] / trx_details['start_amount']
	counters['highest_ratio'][string] = compare_and_update(counters['highest_ratio'][string],  counters['ratio'][string])

def calculateProfitability(order_book, trx_details, trx_string):
	global parameters

	logger.debug(trx_details)

	from_amount = trx_details['from_amount']
	from_currency = trx_details['from_currency']
	to_currency = trx_details['to_currency']
	directions_buy = directions['buy']
	directions_sell = directions['sell']

	if from_currency in directions_buy:
		if to_currency in directions_buy[from_currency]:
			to_amount = buy(order_book, from_currency, to_currency, parameters['adjustment'], from_amount)
			type = 'buy'

	if from_currency in directions_sell:
		if to_currency in directions_sell[from_currency]:
               	        to_amount = sell(order_book, from_currency, to_currency, parameters['adjustment'], from_amount)
			type = 'sell'

	history = {'from_currency': trx_details['from_currency'],
		   'from_amount': trx_details['from_amount'],
		   'to_currency': trx_details['to_currency'],
		   'to_amount': to_amount,
		   'type': type }

        trx_details['from_amount'] = to_amount
        trx_details['from_currency'] = to_currency

	return {'trx_details': trx_details, 'history': history}

def validateProfitability(history):
	highest_value_transaction = highestValueTransaction(counters)
	transaction = history[highest_value_transaction]

	first_transaction = 1
	last_transaction = len(transaction.keys())

	before_amount = transaction[first_transaction]['from_amount']
	after_amount = transaction[last_transaction]['to_amount']

	if after_amount > before_amount:
		executeTransaction(transaction)
	else:
		print "Nope: Highest value transaction has ratio: ", counters['ratio'][highest_value_transaction]

def executeTransaction(transaction_steps):
	print transaction_steps
	for trx in transaction_steps:
		client_redis.publish(trx, transaction_steps[trx])

# ------ START HERE

logger = customLogger()

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()

		history = doStuff()

		for type in sorted(counters):
			#print "%s: %s" % (type, counters[type])
			logger.debug(counters[type])

		validateProfitability(history)
		print datetime.datetime.now()
