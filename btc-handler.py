import threading
import wsclient
import config
import redis
import auth
import sys

class Listener(threading.Thread):
	def __init__(self, client_redis, channels):
		threading.Thread.__init__(self)
		self.redis = client_redis
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
    
        def work(self, item):
                trx = dict(item['data'])
		print trx
                if trx['type'] == "buy":
                       currency_pair = (toCurrency + fromCurrency)

  #              if trx['type'] == "sell":
   #                     currency_pair = fromCurrency + toCurrency

#		print currency_pair
 #               print item['channel'], ":", trx

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

	

