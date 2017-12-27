import socket
import time
import sys

import config
import auth

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('2c5e7058.carbon.hostedgraphite.com', 2003))
api_key = "7a24de6e-98ea-40ed-9d7c-ebd3f8c0ccbd" # nobody cares
ticker = "ltc"
balance = {}

count = 0
#for currency in config.conversions:
#	for pair in config.conversions[currency]:
#		count += len(auth.trading_client.open_orders(currency, pair))

#if count != 0:
#	print "Open trades.."
#	sys.exit(1)

for currency in config.conversions:
	for pair in config.conversions[currency]:
		result = auth.trading_client.account_balance(currency, pair)
		balance[currency] = result[currency + '_balance']
		balance[pair]     = result[pair + '_balance']


for currency in balance:
	message = api_key + ".balance." + ticker + "." + currency + " " + balance[currency]
	print message
	s.sendto(message, ('b8dbc4a5.carbon.hostedgraphite.com', 2003))

s.shutdown(socket.SHUT_WR)
s.close()

print ""
