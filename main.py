from pandas.io.pytables import AppendableFrameTable
from requests.api import get
from wrapper.kiteext import KiteExt
from utils import Login
from utils import SupportResistance
from utils import Telegrambot
from utils import CandlePattern
from instruments import Instruments
import json
import pandas as pd
import logging
from time import sleep
from datetime import datetime as dt
from datetime import timedelta as td
import schedule
import numpy as np
from utils import Utils
from ticker import ZerodhaTicker
import time
from multiprocessing import Process
from threading import Thread
from threading import Timer


LoginWrapper = Login.Login()
kite = LoginWrapper.loginkite()
SupportResistanceWrapper = SupportResistance.SupportResistance()
CandlePatternWrapper = CandlePattern.CandlePattern()
TelegrambotWrapper = Telegrambot.Telegrambot()
Instruments = Instruments.Instruments(kite)
Utils = Utils.Utils()
logging.basicConfig(filename='example.log',level=logging.INFO)
sup_res = []
sup_res_4 = []
resistance = 0
resistance_4 = []
support = 0
support_4 = []

token = 12476930
dayslag = 10
mod_reminder = 5
tf = '10minute'
tf1 = '4minute'


######################################################################################################################
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
############################################################################################################################
   
def getdata(kite,token, dayslag,tf):
    df = pd.DataFrame(kite.historical_data(token, dt.today() - td(days=dayslag), dt.today(), tf))
    return df

def get_support_resistance(df):
    support_res = SupportResistanceWrapper.calculateSupportResistance(df)
    return support_res

def get_nearest_suppport_resistance(SupRes, close, tf = '10minute'):
    logging.info('nearest support resistance') 
    logging.info(close)
    global resistance, support
    supports = []
    resistances = []
    for val in SupRes:
        if val < close:
            supports.append(val)
        else:
            resistances.append(val)
    print(resistances)
    if resistances:
        print("inside if")
        resistance = min(resistances)
    
    else:
        print("inside else")
        data = getdata(kite,token,20,tf)
        SupRes = get_support_resistance(data)
        for val in SupRes:
            if val > close:
                resistances.append(val)
        if resistances:
            print("inside else if")
            resistance = min(resistances)
        if not resistances:
            resistance = Utils.getNearestStrikePrice(close+130)
    
        
        
    if supports:
        support = max(supports)

    else:
        data = getdata(kite,token,20,tf)
        SupRes = get_support_resistance(data)
        for val in SupRes:
            if val < close:
                supports.append(val)
        if not supports:
            support = Utils.getNearestStrikePrice(close-100)
    

    return resistance,support
####################################################################################################################
def checkorder_status_palce_gtt(mins,orderId,tradingsymbol,price,sl,orders,tf,trigger_price = None,target = None):
    timeout = time.time() + mins*60
    
    while True:
        order_df = pd.DataFrame(kite.orders())
        order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == tradingsymbol) ]['status'].values[0]

        if order_status == 'COMPLETE':
            TelegrambotWrapper.send_message("Order placed tf: "+tf+ tradingsymbol+"price "+ str(price))
            try:
                gtt = kite.place_gtt(
                    trigger_type= kite.GTT_TYPE_OCO,
                    tradingsymbol= tradingsymbol,
                    exchange= kite.EXCHANGE_NFO,
                    trigger_values= [sl+2,trigger_price],
                    last_price= price-2,
                    orders= orders,
                    )
                TelegrambotWrapper.send_message(" GTT Order placed tf :"+tf+" target "+ str(target)+"SL "+ str(sl))
                return gtt['trigger_id']
            except Exception as e:
                logging.info("Some Error Occured : {}".format(e))
                TelegrambotWrapper.send_message("Some Error Occured : {}, please stepin and Manually squareoff".format(e))
            break
        elif time.time() > timeout:
            if order_status == 'OPEN':
                kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                TelegrambotWrapper.send_message("Order Not Trigerred"+ tf+ "tf, Cancelling the Order")
                logging.info("order cancelled")
                break
            elif order_status == 'REJECTED':
                break
            else:
                break
        sleep(1)
##################################################################################################################################
def run4minsstrategy(data,sup_res_4):
    print("4mins strategy")
    logging.info("Running 4 mins strategy")
    if True:
        if data['date'].iloc[-1].minute == (dt.now().minute):
            data = data.iloc[:-1]
        close  = data.iloc[-1].close
        resistance_4,support_4 = get_nearest_suppport_resistance(sup_res_4,data.iloc[-2].close,'4minute')
        print("close",close)
        print("resistance",resistance_4)
        print("support", support_4)
        strike_price = Utils.getNearestStrikePrice(close-100)
        atm_ce,atm_pe = Instruments.get_nearest_expiry_options("BANKNIFTY",strike_price,"NFO")
        isBullish = CandlePatternWrapper.isBullish(data.iloc[-1])
        logging.info("Close : "+str(close) + "Resistance :"+str(resistance_4)+"Support" + str(support_4))
        if (isBullish and close > resistance_4) & (data.iloc[-2].close < resistance_4):
            ce_opt_data = getdata(kite,atm_ce.instrument_token,2,tf1)
            ce_opt_data = ce_opt_data[ce_opt_data['date'] == data['date'].iloc[-1]]
            price = ce_opt_data.iloc[-1]['high'] +1
            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : ce_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : ce_opt_data.iloc[-1]['high'] +6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]

            timeout = time.time() + 60*3
            previous_high = ce_opt_data.iloc[-1]['high']
            while True:
                ltp = kite.ltp(atm_ce['instrument_token'])[str(atm_ce['instrument_token'])]['last_price']
                if ((ltp > previous_high)):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_ce['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=50,
                        price=ce_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    checkorder_status_palce_gtt(mins = 3,orderId = orderId,tradingsymbol = atm_ce['tradingsymbol']
                                        ,price= price,sl = ce_opt_data.iloc[-1]['low']-2 ,orders = orders,tf="4mins",trigger_price=ce_opt_data.iloc[-1]['high'] +5, target = ce_opt_data.iloc[-1]['high'] +6)
                    break
                if time.time() > timeout:
                    logging.info("Timeout")
                    break
                sleep(1)
           
        if (~isBullish and close < support_4) & (data.iloc[-2].close > support_4):
            pe_opt_data = getdata(kite,atm_pe.instrument_token,2,tf1)
            pe_opt_data = pe_opt_data[pe_opt_data['date'] == data['date'].iloc[-1]]
            price = pe_opt_data.iloc[-1]['high'] + 1

            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : pe_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : pe_opt_data.iloc[-1]['high'] + 6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]
            timeout = time.time() + 60*3
            previous_high = pe_opt_data.iloc[-1]['high']
            while True:
                ltp = kite.ltp(atm_pe['instrument_token'])[str(atm_pe['instrument_token'])]['last_price']
                if (ltp > previous_high):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_pe['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=50,
                        price=pe_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    checkorder_status_palce_gtt(mins = 3,orderId = orderId,tradingsymbol = atm_pe['tradingsymbol']
                                        ,price= price,sl = pe_opt_data.iloc[-1]['low']-2 ,orders = orders,tf = "4mins",trigger_price=pe_opt_data.iloc[-1]['high'] +5,target = pe_opt_data.iloc[-1]['high'] + 6)
                    break
                if time.time() > timeout:
                    logging.info("Timeout")
                    break
                sleep(1)


####################################################################################################################
def runstrategy(data,sup_res):

    logging.info("Running 10 mins Strategy")
    data['date'] = pd.to_datetime(data['date'])
    logging.info(dt.now())
    if True:
        if data['date'].iloc[-1].minute == (dt.now().minute):
            data = data.iloc[:-1]
        
        close  = data.iloc[-1].close
        resistance,support = get_nearest_suppport_resistance(sup_res,data.iloc[-2].close)
        print("10mins strategy")
        print("close",close)
        print("resistance",resistance)
        print("support", support)

        logging.info("Close : "+str(close) + "Resistance :"+str(resistance)+"Support" + str(support))
        strike_price = Utils.getNearestStrikePrice(close)
        atm_ce,atm_pe = Instruments.get_nearest_expiry_options("BANKNIFTY",strike_price,"NFO")
        isBullish = CandlePatternWrapper.isBullish(data.iloc[-1])
        if (isBullish and close > resistance) & (data.iloc[-2].close < resistance):
            ce_opt_data = getdata(kite,atm_ce.instrument_token,2,tf)
            ce_opt_data = ce_opt_data[ce_opt_data['date'] == data['date'].iloc[-1]]
            price = ce_opt_data.iloc[-1]['high'] +1
            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : ce_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : ce_opt_data.iloc[-1]['high'] +9,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]

            timeout = time.time() + 5*60
            previous_high = ce_opt_data.iloc[-1]['high']
            while True:
                ltp = kite.ltp(atm_ce['instrument_token'])[str(atm_ce['instrument_token'])]['last_price']
                if (ltp > previous_high):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_ce['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=50,
                        price=ce_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    checkorder_status_palce_gtt(mins = 3,orderId = orderId,tradingsymbol = atm_ce['tradingsymbol']
                                        ,price= price,sl = ce_opt_data.iloc[-1]['low']-2 ,orders = orders,tf="10mins",trigger_price = ce_opt_data.iloc[-1]['high'] +8, target = ce_opt_data.iloc[-1]['high'] +9 )
                    break
                if time.time() > timeout:
                    logging.info("Timeout")
                    break
                sleep(1)
            
                
                
        if (~isBullish and close < support) & (data.iloc[-2].close > support):
            pe_opt_data = getdata(kite,atm_pe.instrument_token,2,tf)
            pe_opt_data = pe_opt_data[pe_opt_data['date'] == data['date'].iloc[-1]]
            price = pe_opt_data.iloc[-1]['high'] + 1

            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : pe_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 50,
                "price" : pe_opt_data.iloc[-1]['high'] + 9,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]
            timeout = time.time() + 60*5
            previous_high = pe_opt_data.iloc[-1]['high']
            while True:
                
                ltp = kite.ltp(atm_pe['instrument_token'])[str(atm_pe['instrument_token'])]['last_price']
                if ltp > previous_high:
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_pe['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=50,
                        price=pe_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    checkorder_status_palce_gtt(mins = 2,orderId = orderId,tradingsymbol = atm_pe['tradingsymbol']
                                        ,price= price,sl = pe_opt_data.iloc[-1]['low']-2 ,orders = orders,tf="10mins",trigger_price = pe_opt_data.iloc[-1]['high'] +8,target = pe_opt_data.iloc[-1]['high'] + 9)
                    break
                if time.time() > timeout:
                    logging.info("Timeout")
                    break
                sleep(1)
##################################################################################################################################
def runstrategies():
    logging.info(dt.now())
    data = getdata(kite,token,2,tf)
    if dt.now().minute % 10 == mod_reminder:
        runstrategy(data,sup_res)
  
    if dt.now().minute % 4 == 3:
        data = getdata(kite,token,2,tf1)
        run4minsstrategy(data,sup_res_4)
    
if __name__=="__main__":
    data = getdata(kite,token,dayslag,tf)
    sup_res = get_support_resistance(data)
    print("10mins support resistance")
    print(sup_res)
    data1 = getdata(kite,token,dayslag,tf1)
    sup_res_4 = get_support_resistance(data1)
    print("4mins support resistance")
    print(sup_res_4)
    start_time = dt.today()
    print(start_time)
    start_time = start_time.replace(hour = 9, minute=15)
    end_time = start_time.replace(hour = 15, minute=0)
    rt = RepeatedTimer(120, runstrategies) # it auto-starts, no need of rt.start()
    try:
        sleep(19080) # your long-running job goes here...
    finally:
        rt.stop()
   
    