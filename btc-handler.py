import threading
import wsclient
import config
import redis
import time
import auth
import sys

class Listener(threading.Thread):
	def __init__(self, client_redis, channels):
		threading.Thread.__init__(self)
		self.redis = client_redis
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
    
        def work(self, item):
		if isinstance(item['data'], long):
			print "Subscription status for ", item['channel'], ": ", item['data']

		if isinstance(item['data'], str):
			trx = eval(item['data'])
			currency_pair = currencyPair(trx)
			placeOrder(currency_pair, trx)
#        	        print item['channel'], ":", trx

        def run(self):
                for item in self.pubsub.listen():
                        if item['data'] == "KILL":
                                self.pubsub.unsubscribe()
                                print self, "unsubscribed and finished"
                                break
                        else:
                                self.work(item)

if __name__ == "__main__":
	redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
	print(auth.trading_client.account_balance()['fee'])
	for currency in config.currencies:
		client = Listener(redis_client, currency)
		client.start()

def currencyPair(trx):
	if trx['type'] == 'buy':
		return {'base': trx['to_currency'],  'quote': trx['from_currency']}
	if trx['type'] == 'sell':
		return {'base': trx['from_currency'], 'quote': trx['to_currency']}

def placeOrder(currency_pair, trx):
#	while
	print(auth.trading_client.account_balance(currency_pair['base'], currency_pair['quote']))
	time.sleep(15)
