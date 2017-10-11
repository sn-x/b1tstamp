import redis
import threading

class Listener(threading.Thread):
	def __init__(self, client_redis, channels):
		threading.Thread.__init__(self)
		self.redis = client_redis
		self.pubsub = self.redis.pubsub()
		self.pubsub.subscribe(channels)
    
	def work(self, item):
		print item['channel'], ":", item['data']
    
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
	client = Listener(redis_client, ['btc'])
	client.start()
