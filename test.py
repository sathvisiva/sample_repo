
import json
import pandas as pd
import logging
from time import sleep
from datetime import datetime as dt

from datetime import timedelta as td

from requests.api import get
from wrapper.kiteext import KiteExt
from utils import Login
from utils import SupportResistance
from utils import CandlePattern
import json
import pandas as pd
import logging
from time import sleep

import schedule
import numpy as np
from utils import Utils


"""LoginWrapper = Login.Login()
kite = LoginWrapper.loginkite()



    
kws = kite.kws()


tokens = [12996098]



# RELIANCE BSE
tokens = [58546951]


# Callback for tick reception.
def on_ticks(ws, ticks):
    if len(ticks) > 0:
        logging.info("Current mode: {}".format(ticks[0]["mode"]))
        print(ticks)


# Callback for successful connection.
def on_connect(ws, response):
    logging.info("Successfully connected. Response: {}".format(response))
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL, tokens)
    logging.info("Subscribe to tokens in Full mode: {}".format(tokens))


# Callback when current connection is closed.
def on_close(ws, code, reason):
    logging.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


# Callback when connection closed with error.
def on_error(ws, code, reason):
    logging.info("Connection error: {code} - {reason}".format(code=code, reason=reason))


# Callback when reconnect is on progress
def on_reconnect(ws, attempts_count):
    logging.info("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
def on_noreconnect(ws):
    logging.info("Reconnect failed.")


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error
kws.on_connect = on_connect
kws.on_reconnect = on_reconnect
kws.on_noreconnect = on_noreconnect"""

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.

        
        


    

gtt = {'id': 57389935, 'user_id': 'ZK2474', 'parent_trigger': None, 
'type': 'two-leg', 'created_at': '2021-08-26 12:35:18', 
'updated_at': '2021-08-26 12:50:18', 'expires_at': '2021-08-27 00:00:00', 
'status': 'triggered', 
'condition': {'exchange': 'NFO', 'last_price': 115.1, 'tradingsymbol': 'BANKNIFTY21AUG35700PE', 
    'trigger_values': [84.05, 122.1]}, 
'orders': [{'exchange': 'NFO', 'tradingsymbol': 'BANKNIFTY21AUG35700PE', 'product': 'CNC', 
    'order_type': 'LIMIT', 'transaction_type': 'SELL', 'quantity': 25, 'price': 84.05, 'result': None}, 
            {'exchange': 'NFO', 'tradingsymbol': 'BANKNIFTY21AUG35700PE', 'product': 'CNC', 'order_type': 'LIMIT', 
            'transaction_type': 'SELL', 'quantity': 25, 'price': 125.1, 'result': {'account_id': 'ZK2474', 
                        'exchange': 'NFO', 'tradingsymbol': 'BANKNIFTY21AUG35700PE', 'validity': 'DAY', 'product': 'CNC',
                         'order_type': 'LIMIT', 'transaction_type': 'SELL', 'quantity': 25, 'price': 125.1, 'ltp_atp': 'LTP', 
                         'squareoff_abs_tick': 'absolute', 'stoploss_abs_tick': 'absolute', 'timestamp': '2021-08-26 12:50:17',
                          'triggered_at': 122.95, 'order_result': {'status': 'success', 'order_id': '210826002780891', 'rejection_reason': ''}}}], 'meta': None}

pd.DataFrame(gtt['orders']).to_csv("orders.csv")
print(pd.DataFrame(gtt['orders']))
