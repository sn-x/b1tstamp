redis_port = 6379

parameters  = {'start_amount_btc': 0.01, # 0.019
               'start_amount_ltc': 1.3, # 1.9
#	       'start_amount_xrp': 56,
#	       'start_amount_eth': 0.04,
               'start_amount_eur': 70, # 95
               'start_amount_usd': 70, # 95
               'commision': 0.25, # 0.255%
               'adjustment': 20 } # 1/10

conversions = {'btc': {'usd', 'eur'},
               'eur': {'usd'},
               'ltc': {'usd', 'eur', 'btc'} }
#	       'eth': {'usd', 'eur', 'btc'},
#	       'xrp': {'usd', 'eur', 'btc'}}

counters = {'success': {}, 'ratio': {}, 'highest_ratio':{} }

rounds = { 'btcusd': {'value': 2, 'amount': 5 },
           'btceur': {'value': 2, 'amount': 5 },
           'eurusd': {'value': 5, 'amount': 5 },
           'ltcusd': {'value': 2, 'amount': 5 },
           'ltceur': {'value': 2, 'amount': 5 },
           'ltcbtc': {'value': 8, 'amount': 8 },
           'ethusd': {'value': 2, 'amount': 8 },
           'etheur': {'value': 2, 'amount': 8 },
           'ethbtc': {'value': 8, 'amount': 8 } }

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

directions  = {'buy': buyDirections(),
	       'sell': conversions }
