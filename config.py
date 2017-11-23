redis_port = 6379
counters = {'success': {}, 'ratio': {}, 'highest_ratio':{} }

parameters  = {
	'start_amount_btc': 0.0020, # smallest amount
	'commision': 0.25, #
	'adjustment': 20 } # 1/10

conversions = {
	'btc': {'usd', 'eur'},
	'eur': {'usd'},
	'ltc': {'usd', 'eur', 'btc'} }
#	'eth': {'usd', 'eur', 'btc'} }
#	'xrp': {'usd', 'eur', 'btc'} }

min_order_size = {
	'btcusd': 5,
	'btceur': 5,
	'eurusd': 5,
	'ltcusd': 5,
	'ltceur': 5,
	'ltcbtc': 0.002 }

rounds = {
	'btcusd': {'value': 2, 'amount': 5 },
	'btceur': {'value': 2, 'amount': 5 },
	'eurusd': {'value': 5, 'amount': 5 },
	'ltcusd': {'value': 2, 'amount': 5 },
	'ltceur': {'value': 2, 'amount': 5 },
	'ltcbtc': {'value': 8, 'amount': 5 },
	'ethusd': {'value': 2, 'amount': 5 },
	'etheur': {'value': 2, 'amount': 5 },
	'ethbtc': {'value': 8, 'amount': 5 } }

def fetchCurrencies():
	currencies = list()
        for currency in conversions:
		currencies.append(currency)
                for conversion in conversions[currency]:
			currencies.append(conversion)
	return set(currencies)

currencies = fetchCurrencies()

def buyDirections():
	buy = {}
	buy_2 = {}

	for quote in currencies:
		buy[quote] = {}
		list = []
		for base in conversions:
			if quote in conversions[base]:
				list.append(base)
		if list:
			buy.update({quote: tuple(list)})

	for currency in buy:
		if buy[currency]:
			buy_2.update({currency: buy[currency]})

	return buy_2

directions  = {
	'buy': buyDirections(),
	'sell': conversions}
