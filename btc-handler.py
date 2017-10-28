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
		threading.Thread.__init__(self)
		self.redis = client_redis
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
    
        def work(self, item):
		trade = auth.trading_channel[item['channel']]
		if isinstance(item['data'], long):
			print "Subscription status for ", item['channel'], ": ", item['data']

		if isinstance(item['data'], str):
			trx = eval(item['data'])
			currency_pair = self.currencyPair(trx)
			self.placeOrder(trade, currency_pair, trx, item['channel'])

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

	def orderBookEntries(self, trade):
		count = 0
		for currency in config.conversions:
			for pair in config.conversions[currency]:
				open_orders = trade.open_orders(currency, pair)
				print currency, pair, ": ", open_orders
				count += len(open_orders)

		return count

	def placeOrder(self, trade, currency_pair, trx, channel):
		print "--------------------"
		print channel
        	print trx

		hash = random.getrandbits(128)
		print channel + ": Starting request: ", hash

       	        balance = trade.account_balance(currency_pair['base'], currency_pair['quote'])
		print channel + ": Request ", hash, ":", balance

		round_amount = config.rounds[currency_pair['base'] + currency_pair['quote']]['amount']
		round_value = config.rounds[currency_pair['base'] + currency_pair['quote']]['value']

		if trx['type'] == "sell":
			price = round((trx['to_amount'] / trx['from_amount']), round_value)
			print channel + ": price: ", price
			trade.sell_limit_order(round(trx['from_amount'], round_amount), price, currency_pair['base'], currency_pair['quote'])

                if trx['type'] == "buy":
                        price = round((trx['from_amount'] / trx['to_amount']), round_value)
                        print channel + ": price: ", price
                        trade.buy_limit_order(round(trx['to_amount'], round_amount), price, currency_pair['base'], currency_pair['quote'])

		print channel + ": Sleeping.."
		time.sleep(10)
		open_orders_count = self.orderBookEntries(trade)

                while open_orders_count != 0:
			print channel + ": Total open orders: ", open_orders_count
			print channel + ":  -> Sleeping for 60 sec..."
			time.sleep(60)
                        print channel + ":  -> Retrying.."
			open_orders_count = self.orderBookEntries(trade)

		thread.exit()
#		sys.exit(1)

## START HERE

def startListeners(redis_client):
        print "Building threads.."
        for currency in config.currencies:
                print " + " + currency
                client = Listener(redis_client, currency)
                client.start()

	print threading.active_count()
	while threading.active_count() != 1:
		time.sleep(1)

        print "All threads finished. Restarting.."
#	sys.exit(0)
        startListeners(redis_client)

if __name__ == "__main__":
        redis_client = redis.StrictRedis(host='localhost', port=config.redis_port, db=0)
        startListeners(redis_client)

