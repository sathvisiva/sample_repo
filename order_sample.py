from wrapper.kiteext import KiteExt
from utils import Login
import logging
import time

from ticker.ZerodhaTicker import ZerodhaTicker


LoginWrapper = Login.Login()
kite = LoginWrapper.loginkite()


def tickerListener(tick):
    logging.info('tickerLister: onNewTick %s', vars(tick));



   


def place_gtt(tradingsymbol, exchange, trigger_values, last_price, orders):
    try:
        gtt = kite.place_gtt(
            trigger_type= kite.GTT_TYPE_OCO,
            tradingsymbol= tradingsymbol,
            exchange= exchange,
            trigger_values= [110,190],
            last_price= last_price,
            orders= orders,
        )
        print("Gtt Response is {}".format(gtt['trigger_id']))
        return gtt['trigger_id']
    except Exception as e:
        print("Some Error Occured : {}".format(e))


orders = [
        {
        "transaction_type" : "SELL",
        "quantity" : 25,
        "price" : 110,
        "order_type" : kite.ORDER_TYPE_LIMIT,
        "product" : kite.PRODUCT_CNC
        },
        {
        "transaction_type" : "SELL",
        "quantity" : 25,
        "price" : 190,
        "order_type" : kite.ORDER_TYPE_LIMIT,
        "product" : kite.PRODUCT_CNC
        }
    ]


    

place_gtt(
        tradingsymbol= 'BANKNIFTY21AUG35700CE',
        exchange= kite.EXCHANGE_NFO,
        trigger_values=[130,190],
        last_price = 170,
        orders = orders
    )

    kite.cancel_order()



