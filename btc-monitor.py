import itertools
import datetime
import wsclient
import logging
import config
import redis
import math
import time
import sys
import os

client_bitstamp_ws = wsclient.BitstampWebsocketClient()
client_redis = redis.StrictRedis(host='localhost', port=config.redis_port, db=0)

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

	for currency in config.conversions:
		for conversion in config.conversions[currency]:
			checkOrderBook(currency, conversion)
			self[currency + conversion + '_ask_v'] = float(client_bitstamp_ws.orderbook[currency][conversion]['asks'][0][0])
			self[currency + conversion + '_bid_v'] = float(client_bitstamp_ws.orderbook[currency][conversion]['bids'][0][0])

        return self

def currencyPair(type, from_currency, to_currency):
	if type == 'buy':
		return {'base': to_currency,  'quote': from_currency}
	if type== 'sell':
		return {'base': from_currency, 'quote': to_currency}

def checkOrderBook(currency, conversion):
        while ('asks' and 'bids') not in client_bitstamp_ws.orderbook[currency][conversion]:
		print "Empty orderbook. Resubscribing.. " + currency + " : " + conversion
                subscribe(currency, conversion)
                time.sleep(1)

def subscribe(currency, conversion):
        client_bitstamp_ws.subscribe("order_book", currency, conversion)

def possibletrasactions():
	transactions = []
	permutations = list(itertools.permutations(config.currencies))

	# append starting currency
	for trx_flow in permutations:
		trx_flow = list(trx_flow)
		currency = trx_flow[0]
		trx_flow.append(currency)
		transactions.append(trx_flow)

	return transactions

def orderbookValue(type, orderbook, currency_pair):
	if type == "buy":
		return orderbook[currency_pair['base'] + currency_pair['quote'] + '_bid_v']

	if type == "sell":
		return orderbook[currency_pair['base'] + currency_pair['quote'] + '_ask_v']

def calculateFee(value):
        return value * (config.parameters['commision'] / 100)

def calculateAdjustment(orderbook, currency_pair):
	ask = orderbook[currency_pair['base'] + currency_pair['quote'] + '_ask_v']
	bid = orderbook[currency_pair['base'] + currency_pair['quote'] + '_bid_v']
	adjustment = config.parameters['adjustment']
	return (ask - bid) / adjustment

def conversionMath(type, orderbook, fromCurrency, toCurrency, adjustment, amount):
	self = {}
	currency_pair   = currencyPair(type, fromCurrency, toCurrency)
	orderbook_value = orderbookValue(type, orderbook, currency_pair)

	round_amount    = config.rounds[currency_pair['base'] + currency_pair['quote']]['amount']

	fee_rounding    = 100
	if (toCurrency == "btc" and fromCurrency == "ltc") or (toCurrency == "ltc" and fromCurrency == "btc"):
		fee_rounding = 100000

	if type == "buy":
		# NORMAL
		self['fee'] = calculateFee(amount)
		self['new_amount'] = round(((amount - self['fee']) / (orderbook_value + adjustment)), round_amount)

		# RECALCULATED
		self['rounded_fee'] = math.ceil(self['fee'] * fee_rounding) / fee_rounding
		self['modified_start_amount'] = round((self['rounded_fee'] / (config.parameters['commision'] / 100)), round_amount)
		self['modified_new_amount'] = round(((self['modified_start_amount'] - self['rounded_fee']) / (orderbook_value + adjustment)), round_amount)

	if type == "sell":
		# NORMAL
		new_amount_full = (amount * (orderbook_value - adjustment))
		self['fee'] = calculateFee(new_amount_full)
		self['new_amount'] = round((new_amount_full - self['fee']), round_amount)

		# RECALCULATED
		self['rounded_fee'] = math.ceil(self['fee'] * fee_rounding) / fee_rounding
		self['modified_new_amount'] = round((self['rounded_fee'] / (config.parameters['commision'] / 100)), round_amount)
		self['modified_start_amount'] = round(((self['modified_new_amount'] + self['fee']) / (orderbook_value - adjustment)), round_amount)

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
				trx_details['from_amount'] = config.parameters['start_amount_' + currency]
				trx_details['start_amount'] = config.parameters['start_amount_' + currency]

		updateCounters(transaction, trx_details, trx_string)

	return history

def highestValueTransaction(counters):
	transaction_values = []

	for transaction, value in config.counters['ratio'].items():
		transaction_values.append(value)

	transaction_values.sort(reverse=True)

	for transaction, value in config.counters['ratio'].items():
		if value == transaction_values[0]:
			return transaction

	print "Couldn't find highest value transaction. Fatal error. Bug?"
	sys.exit(1)

def transactionString(transaction):
	string = ""
        for currency in transaction:
                string += str(currency)

	return string

def updateCounters(transaction, trx_details, string):
	if string not in config.counters['success']:
		config.counters['success'][string] = 0

	if string not in config.counters['ratio']:
		config.counters['ratio'][string] = 0

	if string not in config.counters['highest_ratio']:
		config.counters['highest_ratio'][string] = 0

	config.counters['success'][string] = increaseValue(trx_details['start_amount'], trx_details['from_amount'], config.counters['success'][string])
	config.counters['ratio'][string] = trx_details['from_amount'] / trx_details['start_amount']
	config.counters['highest_ratio'][string] = compare_and_update(config.counters['highest_ratio'][string],  config.counters['ratio'][string])

def calculateType(from_currency, to_currency):
        directions_buy = config.directions['buy']
        directions_sell = config.directions['sell']

        if from_currency in directions_buy:
                if to_currency in directions_buy[from_currency]:
                        return "buy"

        if from_currency in directions_sell:
                if to_currency in directions_sell[from_currency]:
                        return 'sell'

def calculateProfitability(order_book, trx_details, trx_string):
	logger.debug(trx_details)

	from_amount = trx_details['from_amount']
	from_currency = trx_details['from_currency']
	to_currency = trx_details['to_currency']
	type = calculateType(from_currency, to_currency)
        currency_pair = currencyPair(type, from_currency, to_currency)
	adjustment = calculateAdjustment(order_book, currency_pair)

	result = conversionMath(type, order_book, from_currency, to_currency, adjustment, from_amount)

	history = {'from_currency': trx_details['from_currency'],
		   'from_amount': trx_details['from_amount'],
		   'to_currency': trx_details['to_currency'],
		   'to_amount': result['new_amount'],
		   'trx_fee': result['fee'],
		   'trx_rounded_fee': result['rounded_fee'],
		   'modified_start_amount': result['modified_start_amount'],
		   'modified_new_amount': result['modified_new_amount'],
		   'type': type }

        trx_details['from_amount'] = result['new_amount']
        trx_details['from_currency'] = to_currency

	return {'trx_details': trx_details, 'history': history}

def validateProfitability(history):
	highest_value_transaction = highestValueTransaction(config.counters)
	transaction = history[highest_value_transaction]

	first_transaction = 1
	last_transaction = len(transaction.keys())

	before_amount = transaction[first_transaction]['from_amount']
	after_amount = transaction[last_transaction]['to_amount']

	if after_amount > before_amount:
		executeTransaction(transaction)
	else:
		print "Nope: Highest value transaction has ratio: ", config.counters['ratio'][highest_value_transaction]

def executeTransaction(transaction_steps):
	print transaction_steps
	client_redis.set('currencies', transaction_steps.keys)
	for step in transaction_steps:
		print transaction_steps[step]['from_currency']
		client_redis.publish(transaction_steps[step]['from_currency'], str(transaction_steps[step]))
#	sys.exit(1)

# ------ START HERE

logger = customLogger()

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		print "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
		print datetime.datetime.now()

		history = doStuff()

		for type in sorted(config.counters):
			logger.debug(config.counters[type])

		validateProfitability(history)
		print datetime.datetime.now()
