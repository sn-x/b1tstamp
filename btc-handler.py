import threading
import random
import redis
import time
import sys

import wsclient

import config
import auth

class Listener(threading.Thread):
	def __init__(self, client_redis, channels):
		time.sleep(1)
		threading.Thread.__init__(self)
		self.redis = client_redis
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
    
        def work(self, item):
		if isinstance(item['data'], long):
			print "Subscription status for ", item['channel'], ": ", item['data']
			print(auth.trading_client.account_balance()['fee'])

		if isinstance(item['data'], str):
			trx = eval(item['data'])
			currency_pair = self.currencyPair(trx)
			self.placeOrder(currency_pair, trx, item['channel'])

        def run(self):
                for item in self.pubsub.listen():
                        if item['data'] == "KILL":
                                self.pubsub.unsubscribe()
                                print self, "unsubscribed and finished"
                                break
                        else:
                                self.work(item)

	def currencyPair(self, trx):
        	if trx['type'] == 'buy':
                	return {'base': trx['to_currency'],  'quote': trx['from_currency']}
	        if trx['type'] == 'sell':
        	        return {'base': trx['from_currency'], 'quote': trx['to_currency']}

	def placeOrder(self, currency_pair, trx, channel):
		print "--------------------"
		print channel
        	print trx

		hash = random.getrandbits(128)
		print "Starting request: ", hash

		if channel == "ltc":
			time.sleep(1)

		if channel == "eur":
			time.sleep(2)

		if channel == "usd":
			time.sleep(3)

       	        balance = auth.trading_client.account_balance(currency_pair['base'], currency_pair['quote'])
		print "Request ", hash, ":", balance

		round_amount = config.rounds[currency_pair['base'] + currency_pair['quote']]['amount']
		round_value = config.rounds[currency_pair['base'] + currency_pair['quote']]['value']

		if trx['type'] == "sell":
			price = round((trx['to_amount'] / trx['from_amount']), round_value)
			print "price: ", price
			auth.trading_client.sell_limit_order(round(trx['from_amount'], round_amount), price, currency_pair['base'], currency_pair['quote'])

                if trx['type'] == "buy":
                        price = round((trx['from_amount'] / trx['to_amount']), round_value)
                        print "price: ", price
                        auth.trading_client.buy_limit_order(round(trx['to_amount'], round_amount), price, currency_pair['base'], currency_pair['quote'])

		sys.exit(0)

print(auth.trading_client.account_balance()['fee'])

if __name__ == "__main__":
	redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
	for currency in config.currencies:
		client = Listener(redis_client, currency)
		client.start()

