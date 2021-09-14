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


LoginWrapper = Login.Login()
kite = LoginWrapper.loginkite()
SupportResistanceWrapper = SupportResistance.SupportResistance()
CandlePatternWrapper = CandlePattern.CandlePattern()
TelegrambotWrapper = Telegrambot.Telegrambot()
Instruments = Instruments.Instruments(kite)
Utils = Utils.Utils()
sup_res = []
sup_res_4 = []
resistance = 0
resistance_4 = []
support = 0
support_4 = []

token = 12476930
tokens = [12476930]
dayslag = 10
mod_reminder = 5
tf = '10minute'
tf1 = '4minute'

def on_ticks(ws, ticks):
    global ltp, end_time,  target, stoploss
    ltp = ticks[0]["last_price"]

def on_connect(ws, response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_LTP, tokens)  # Set all token tick in `full` mode.

def on_order_update(ws, data):
    print(data)
   
def getdata(kite,token, dayslag,tf):
    df = pd.DataFrame(kite.historical_data(token, dt.today() - td(days=dayslag), dt.today(), tf))
    return df

def get_support_resistance(df):
    support_res = SupportResistanceWrapper.calculateSupportResistance(df)
    return support_res

def get_nearest_suppport_resistance(SupRes, close, tf = '10minute'):
    global resistance, support
    supports = []
    resistances = []
    for val in SupRes:
        if val < close:
            supports.append(val)
        else:
            resistances.append(val)
    if resistances:
        resistance = min(resistances)
    else:
        data = getdata(kite,token,20,tf)
        SupRes = get_support_resistance(data)
        for val in SupRes:
            if val > close:
                resistances.append(val)
        if not resistances:
            resistance = Utils.getNearestStrikePrice(close+50)
        
        
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
def checkorder_status_palce_gtt(timeout):
    


def run4minsstrategy(data,sup_res_4):
    print("running 4 mins strategy")
    if True:
        if data['date'].iloc[-1].minute == (dt.now().minute):
            data = data.iloc[:-1]
        close  = data.iloc[-1].close
        resistance_4,support_4 = get_nearest_suppport_resistance(sup_res_4,data.iloc[-2].close,'4minute')
        strike_price = Utils.getNearestStrikePrice(close-100)
        atm_ce,atm_pe = Instruments.get_nearest_expiry_options("BANKNIFTY",strike_price,"NFO")
        isBullish = CandlePatternWrapper.isBullish(data.iloc[-1])
        print("close",close)
        print("resistance", resistance_4)
        print("support", support_4)
        if (isBullish and close > resistance_4) & (data.iloc[-2].close < resistance_4):
            ce_opt_data = getdata(kite,atm_ce.instrument_token,1,tf1)
            ce_opt_data = ce_opt_data[ce_opt_data['date'] == data['date'].iloc[-1]]
            price = ce_opt_data.iloc[-1]['high'] +1
            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['high'] +6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]

            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_ce['instrument_token'])[str(atm_ce['instrument_token'])]['last_price']
            while True:
                if (ltp > ce_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_ce['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=ce_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_ce['tradingsymbol']) ]['status'].values[0]

                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 4mins tf: "+ atm_ce['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                            trigger_type= kite.GTT_TYPE_OCO,
                            tradingsymbol= atm_ce['tradingsymbol'],
                            exchange= kite.EXCHANGE_NFO,
                            trigger_values= [ce_opt_data.iloc[-1]['low']-2,price+5],
                            last_price= price-2,
                            orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed 4mins tf : target "+ str(price+5)+"SL "+ str(ce_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred 4mins tf, Cancelling the Order")
                            print("order cancelled")
                        break
                    elif order_status == 'REJECTED':
                        break
                if time.time() > timeout:
                    break
                sleep(1)
            
                
                
        if (~isBullish and close < support_4) & (data.iloc[-2].close > support_4):
            pe_opt_data = getdata(kite,atm_pe.instrument_token,1,tf1)
            pe_opt_data = pe_opt_data[pe_opt_data['date'] == data['date'].iloc[-1]]
            price = pe_opt_data.iloc[-1]['high'] + 1

            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['high'] + 6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]
            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_pe['instrument_token'])[str(atm_pe['instrument_token'])]['last_price']
            while True:
                if (ltp > pe_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_pe['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=pe_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_pe['tradingsymbol']) ]['status'].values[0]
                    
                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 4mins tf : "+ atm_pe['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                                trigger_type= kite.GTT_TYPE_OCO,
                                tradingsymbol= atm_pe['tradingsymbol'],
                                exchange= kite.EXCHANGE_NFO,
                                trigger_values= [pe_opt_data.iloc[-1]['low']-2,price+5],
                                last_price= price-2,
                                orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed  4mins tf: target "+ str(price+8)+"SL "+ str(pe_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred, Cancelling the Order")
                        break
                    elif order_status == 'REJECTED':
                        TelegrambotWrapper.send_message("Order Rejected")
                        break
                    sleep(1)







####################################################################################################################
def runstrategy(data,sup_res):
    print("runstrategy")
    #data = getdata(kite,token,1,tf)
    data['date'] = pd.to_datetime(data['date'])
    subscribed_tokens = list()
    print(dt.now())
    """
    if dt.now().minute % 4 == 3:
        print("inside 4 mins")
        data = getdata(kite,token,1,tf1)
        if data['date'].iloc[-1].minute == (dt.now().minute):
            data = data.iloc[:-1]
        close  = data.iloc[-1].close
        resistance_4,support_4 = get_nearest_suppport_resistance(sup_res_4,data.iloc[-2].close,'4minute')
        strike_price = Utils.getNearestStrikePrice(close-100)
        atm_ce,atm_pe = Instruments.get_nearest_expiry_options("BANKNIFTY",strike_price,"NFO")
        isBullish = CandlePatternWrapper.isBullish(data.iloc[-1])
        print("close",close)
        print("resistance", resistance_4)
        print("support", support_4)
        if (isBullish and close > resistance_4) & (data.iloc[-2].close < resistance_4):
            ce_opt_data = getdata(kite,atm_ce.instrument_token,1,tf1)
            ce_opt_data = ce_opt_data[ce_opt_data['date'] == data['date'].iloc[-1]]
            price = ce_opt_data.iloc[-1]['high'] +1
            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['high'] +6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]

            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_ce['instrument_token'])[str(atm_ce['instrument_token'])]['last_price']
            while True:
                if (ltp > ce_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_ce['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=ce_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_ce['tradingsymbol']) ]['status'].values[0]

                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 4mins tf: "+ atm_ce['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                            trigger_type= kite.GTT_TYPE_OCO,
                            tradingsymbol= atm_ce['tradingsymbol'],
                            exchange= kite.EXCHANGE_NFO,
                            trigger_values= [ce_opt_data.iloc[-1]['low']-2,price+5],
                            last_price= price-2,
                            orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed 4mins tf : target "+ str(price+5)+"SL "+ str(ce_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred 4mins tf, Cancelling the Order")
                            print("order cancelled")
                        break
                    elif order_status == 'REJECTED':
                        break
                if time.time() > timeout:
                    break
                sleep(1)
            
                
                
        if (~isBullish and close < support_4) & (data.iloc[-2].close > support_4):
            pe_opt_data = getdata(kite,atm_pe.instrument_token,1,tf1)
            pe_opt_data = pe_opt_data[pe_opt_data['date'] == data['date'].iloc[-1]]
            price = pe_opt_data.iloc[-1]['high'] + 1

            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['high'] + 6,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]
            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_pe['instrument_token'])[str(atm_pe['instrument_token'])]['last_price']
            while True:
                if (ltp > pe_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_pe['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=pe_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_pe['tradingsymbol']) ]['status'].values[0]
                    
                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 4mins tf : "+ atm_pe['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                                trigger_type= kite.GTT_TYPE_OCO,
                                tradingsymbol= atm_pe['tradingsymbol'],
                                exchange= kite.EXCHANGE_NFO,
                                trigger_values= [pe_opt_data.iloc[-1]['low']-2,price+5],
                                last_price= price-2,
                                orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed  4mins tf: target "+ str(price+8)+"SL "+ str(pe_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred, Cancelling the Order")
                        break
                    elif order_status == 'REJECTED':
                        TelegrambotWrapper.send_message("Order Rejected")
                        break
                    sleep(1)"""



    if True:
        print("inside 10mins tf")
        if data['date'].iloc[-1].minute == (dt.now().minute):
            data = data.iloc[:-1]
        
        close  = data.iloc[-1].close
        resistance,support = get_nearest_suppport_resistance(sup_res,data.iloc[-2].close)
        print("close",close)
        print("resistance", resistance)
        print("support", support)
        strike_price = Utils.getNearestStrikePrice(close)
        atm_ce,atm_pe = Instruments.get_nearest_expiry_options("BANKNIFTY",strike_price,"NFO")
        isBullish = CandlePatternWrapper.isBullish(data.iloc[-1])
        if (isBullish and close > resistance) & (data.iloc[-2].close < resistance):
            ce_opt_data = getdata(kite,atm_ce.instrument_token,1,tf)
            ce_opt_data = ce_opt_data[ce_opt_data['date'] == data['date'].iloc[-1]]
            price = ce_opt_data.iloc[-1]['high'] +1
            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : ce_opt_data.iloc[-1]['high'] +9,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]

            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_ce['instrument_token'])[str(atm_ce['instrument_token'])]['last_price']
            while True:
                if (ltp > ce_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_ce['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=ce_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_ce['tradingsymbol']) ]['status'].values[0]

                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 10mins tf: "+ atm_ce['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                            trigger_type= kite.GTT_TYPE_OCO,
                            tradingsymbol= atm_ce['tradingsymbol'],
                            exchange= kite.EXCHANGE_NFO,
                            trigger_values= [ce_opt_data.iloc[-1]['low']-2,price+5],
                            last_price= price-2,
                            orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed 10mins tf : target "+ str(price+8)+"SL "+ str(ce_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred 10mins tf, Cancelling the Order")
                            print("order cancelled")
                        break
                    elif order_status == 'REJECTED':
                        break
                if time.time() > timeout:
                    break
                sleep(1)
            
                
                
        if (~isBullish and close < support) & (data.iloc[-2].close > support):
            pe_opt_data = getdata(kite,atm_pe.instrument_token,1,tf)
            pe_opt_data = pe_opt_data[pe_opt_data['date'] == data['date'].iloc[-1]]
            price = pe_opt_data.iloc[-1]['high'] + 1

            orders = [
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['low']-2,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                },
                {
                "transaction_type" : "SELL",
                "quantity" : 25,
                "price" : pe_opt_data.iloc[-1]['high'] + 9,
                "order_type" : kite.ORDER_TYPE_LIMIT,
                "product" : kite.PRODUCT_NRML
                }
            ]
            timeout = time.time() + 60*6
            ltp = kite.ltp(atm_pe['instrument_token'])[str(atm_pe['instrument_token'])]['last_price']
            while True:
                if (ltp > pe_opt_data.iloc[-1]['high']):
                    orderId = kite.place_order(
                        variety=kite.VARIETY_REGULAR,
                        exchange=kite.EXCHANGE_NFO,
                        tradingsymbol=atm_pe['tradingsymbol'],
                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                        quantity=25,
                        price=pe_opt_data.iloc[-1]['high'] +1,
                        product=kite.PRODUCT_NRML,
                        order_type=kite.ORDER_TYPE_LIMIT)
                    order_df = pd.DataFrame(kite.orders())
                    order_status =order_df[(order_df['order_id'] == str(orderId)) & (order_df['tradingsymbol'] == atm_pe['tradingsymbol']) ]['status'].values[0]
                    
                    if order_status == 'COMPLETE':
                        TelegrambotWrapper.send_message("Order placed 10mins tf: "+ atm_pe['tradingsymbol']+"price "+ str(price))
                        try:
                            gtt = kite.place_gtt(
                                trigger_type= kite.GTT_TYPE_OCO,
                                tradingsymbol= atm_pe['tradingsymbol'],
                                exchange= kite.EXCHANGE_NFO,
                                trigger_values= [pe_opt_data.iloc[-1]['low']-2,price+5],
                                last_price= price-2,
                                orders= orders,
                            )
                            TelegrambotWrapper.send_message(" GTT Order placed 10mins tf : target "+ str(price+8)+"SL "+ str(pe_opt_data.iloc[-1]['low']-2))
                            return gtt['trigger_id']
                        except Exception as e:
                            print("Some Error Occured : {}".format(e))
                        break
                    elif time.time() > timeout:
                        if order_status == 'OPEN':
                            kite.cancel_order(kite.VARIETY_REGULAR, orderId, parent_order_id=None)
                            TelegrambotWrapper.send_message("Order Not Trigerred 10mins tf, Cancelling the Order")
                        break
                    elif order_status == 'REJECTED':
                        TelegrambotWrapper.send_message("Order Rejected")
                        break
                    sleep(1)

def runstrategies():
    print(dt.now())
    data = getdata(kite,token,1,tf)
    if dt.now().minute % 10 == mod_reminder:
        data = getdata(kite,token,1,tf)
        runstrategy(data,sup_res)
    if dt.now().minute % 4 == 3:
        print(sup_res_4)
        data = getdata(kite,token,1,tf1)
        run4minsstrategy(data,sup_res_4)


def main():
    schedule.every(2).minutes.do(runstrategies)

    
if __name__=="__main__":
    """kws = kite.kws()
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_order_update = on_order_update
    kws.connect(threaded=True)"""
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
    main()
    while 1:
        schedule.run_pending()
        sleep(1)
        if dt.now() > end_time:
            print("program Ended")
            break