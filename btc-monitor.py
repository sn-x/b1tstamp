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

	permutations = list(itertools.permutations(config.currencies, 2))

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

def conversionMath(trx_details, orderbook, adjustment):
	self = {}
	type = trx_details['type']
	self['from_amount'] = trx_details['from_amount']
	from_currency = trx_details['from_currency']
	to_currency = trx_details['to_currency']

	currency_pair   = currencyPair(type, from_currency, to_currency)
	orderbook_value = orderbookValue(type, orderbook, currency_pair)

	round_amount    = config.rounds[currency_pair['base'] + currency_pair['quote']]['amount']
	round_value     = config.rounds[currency_pair['base'] + currency_pair['quote']]['value']

	fee_rounding = 100
	if (to_currency == "btc" and from_currency == "ltc") or (to_currency == "ltc" and from_currency == "btc"):
		fee_rounding = 100000

	if type == "buy":
		self['orderbook_v'] = orderbook_value
		self['adjusted_orderbook_v'] = self['orderbook_v'] + adjustment
		self['rounded_orderbook_v'] = round(orderbook_value, round_value)
		self['rounded_adjusted_orderbook_v'] = round((self['orderbook_v'] + adjustment), round_value)

		# NORMAL
		self['fee'] = calculateFee(self['from_amount'])
		self['fee'] = math.ceil(self['fee'] * fee_rounding) / fee_rounding
		self['from_amount'] = round((self['from_amount'] - self['fee']), round_amount)
		self['new_amount'] = round((self['from_amount'] / self['rounded_adjusted_orderbook_v']), round_amount)


		# RECALCULATED
		self['modified_start_amount'] = round((self['fee'] / (config.parameters['commision'] / 100)), round_amount)
		self['modified_new_amount'] = round(((self['modified_start_amount'] - self['fee']) / (orderbook_value + adjustment)), round_amount)

	if type == "sell":
		self['orderbook_v'] = orderbook_value
		self['adjusted_orderbook_v'] = self['orderbook_v'] - adjustment
		self['rounded_orderbook_v'] = round(orderbook_value, round_value)
		self['rounded_adjusted_orderbook_v'] = round((self['orderbook_v'] - adjustment), round_value)

		# NORMAL
		new_amount_full = (self['from_amount'] * self['rounded_adjusted_orderbook_v'])
		self['fee'] = calculateFee(new_amount_full)
		self['fee'] = math.ceil(self['fee'] * fee_rounding) / fee_rounding
		self['new_amount'] = round(new_amount_full, round_amount) - self['fee']

		# RECALCULATED
		self['modified_new_amount'] = round((self['fee'] / (config.parameters['commision'] / 100)), round_amount) - self['fee']
		self['modified_start_amount'] = round(((self['modified_new_amount'] + self['fee']) / self['rounded_adjusted_orderbook_v']), round_amount)

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

def alignPrice(type, amount, currency_pair, round_amount, orderbook_value):
	fee_rounding = 100
	if (currency_pair['base'] == "ltc" and currency_pair['quote'] == "btc") or (currency_pair['base'] == "btc" and currency_pair['quote'] == "ltc"):
		fee_rounding = 100000

	if type == 'buy':
		fee = calculateFee(amount)
		#print "buy fee: ", fee
		rounded_fee = math.ceil(fee * fee_rounding) / fee_rounding
		#print "buy rounded fee: ", rounded_fee
		modified_amount = round(rounded_fee / (config.parameters['commision'] / 100), round_amount)
		#print "buy modified_amount: ", modified_amount
		modified_amount = modified_amount

	if type == 'sell':
		new_amount_full = (amount * orderbook_value)
		fee = calculateFee(new_amount_full)
		#print "sell fee: ", fee
		rounded_fee = math.ceil(fee * fee_rounding) / fee_rounding
		#print "sell rounded fee: ", rounded_fee
		modified_amount = round(rounded_fee / (config.parameters['commision'] / 100), round_amount)
		modified_amount = round(((modified_amount) / (orderbook_value)), round_amount)
		#print "sell modified_amount: ", modified_amount

	return modified_amount

def startingAmount(type, from_currency, currency_pair, orderbook):

	round_amount = config.rounds[currency_pair['base'] + currency_pair['quote']]['amount']
	orderbook_value = orderbookValue(type, orderbook, currency_pair)

	if from_currency == "btc":
		start_amount = config.parameters['start_amount_btc']
		aligned_amount = alignPrice(type, start_amount, currency_pair, round_amount, orderbook_value)
		return	aligned_amount

	if from_currency == "ltc":
		temp_currency_pair = {'base': 'ltc',  'quote': 'btc'} # we need a currency pair betwen btc and ltc, because we do start amount calc.
		temp_orderbook_value = orderbookValue(type, orderbook, temp_currency_pair)
		start_amount = config.parameters['start_amount_btc'] / temp_orderbook_value
		aligned_amount = alignPrice(type, start_amount, currency_pair, round_amount, orderbook_value)
		return aligned_amount

	if from_currency == "eur":
		temp_currency_pair = {'base': 'btc',  'quote': 'eur'}
		temp_orderbook_value = orderbookValue(type, orderbook, temp_currency_pair)
		start_amount = config.parameters['start_amount_btc'] * temp_orderbook_value
		aligned_amount = alignPrice(type, start_amount, currency_pair, round_amount, orderbook_value)
		return aligned_amount

	if from_currency == "usd":
		temp_currency_pair = {'base': 'btc',  'quote': 'usd'}
		temp_orderbook_value = orderbookValue(type, orderbook, temp_currency_pair)
		start_amount = config.parameters['start_amount_btc'] * temp_orderbook_value
		aligned_amount = alignPrice(type, start_amount, currency_pair, round_amount, orderbook_value)
		return aligned_amount

def doStuff():
	history = {}
	orderbook = fetchOrderBook()
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
				trx_details['type'] = calculateType(trx_details['from_currency'], trx_details['to_currency'])
				trx_details['currency_pair'] = currencyPair(trx_details['type'], trx_details['from_currency'], trx_details['to_currency'])

				if trx_details['start_amount'] == "null":
					trx_details['start_amount'] = startingAmount(trx_details['type'], trx_details['from_currency'], trx_details['currency_pair'], orderbook)
					#print "starting_amount:", trx_details['start_amount']
					trx_details['from_amount'] = trx_details['start_amount']

				results = calculateProfitability(orderbook, trx_details, trx_string)
				history[trx_string][trx_step].update(results['history'])
				trx_details = results['trx_details']
			else:
				#print
				trx_details['from_currency'] = currency
				trx_details['start_amount'] = "null"

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

	adjustment = calculateAdjustment(order_book, trx_details['currency_pair'])
	result = conversionMath(trx_details, order_book, adjustment)

	history = {
		'type': trx_details['type'],
		'from_currency': trx_details['from_currency'],
		'from_amount': result['from_amount'],
		'to_currency': trx_details['to_currency'],
		'to_amount': result['new_amount'],
		'trx_fee': result['fee'],
		'orderbook': result['orderbook_v'],
		'adjusted_orderbook': result['adjusted_orderbook_v'],
		'rounded_adjusted_orderbook': result['rounded_adjusted_orderbook_v']
	}
	#print result['from_amount'], trx_details['from_currency']
	#print result['fee'], ":", result['rounded_fee']
	# PREPARE FOR NEW TRX STEP
	trx_details['from_amount'] = result['new_amount']
	trx_details['from_currency'] = trx_details['to_currency']

	return {'trx_details': trx_details, 'history': history}

def validateProfitability(history):
	highest_value_transaction = highestValueTransaction(config.counters)
	transaction = history[highest_value_transaction]

	first_transaction = 1
	last_transaction = len(transaction.keys())

	before_amount = transaction[first_transaction]['from_amount']
	after_amount = transaction[last_transaction]['to_amount']

	if config.counters['ratio'][highest_value_transaction] > 1:
		if (after_amount - before_amount) > (after_amount * config.parameters['increase']):
			executeTransaction(transaction)
		else:
			string = (after_amount - before_amount), "<", (after_amount * config.parameters['increase']), transaction[last_transaction]['to_currency'], "(", config.counters['ratio'][highest_value_transaction], ")"
			logger.warning("Not enough juice: %s", string)
			print "Nope: Not enough juice: ", string
	else:
		counter = str(config.counters['ratio'][highest_value_transaction])
		logger.warning("Highest value transaction has ratio: %s", counter)
		print "Highest value transaction has ratio: ", config.counters['ratio'][highest_value_transaction]

def executeTransaction(transaction_steps):
	logger.warning(transaction_steps)

	all_currencies = config.currencies
	client_redis.set('currencies', transaction_steps.keys)

	for step in transaction_steps:
		all_currencies.remove(transaction_steps[step]['from_currency'])
		print transaction_steps[step]['from_currency']
		client_redis.publish(transaction_steps[step]['from_currency'], str(transaction_steps[step]))

	for currency in all_currencies:
		client_redis.publish(currency, "KILL")

	sys.exit(1)

# ------ START HERE

logger = customLogger()

while True:
	order_book = fetchOrderBook()
	if order_book != fetchOrderBook():
		timestamp = datetime.datetime.now()
		logger.warning("-------------------------------------------------------")
		logger.warning(timestamp)
		print "-------------------------------------------------------"
		print timestamp

		history = doStuff()
		validateProfitability(history)
