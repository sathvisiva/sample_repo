
import os
import logging
import json

from utils.Utils import Utils
import pandas as pd

class Instruments:
    instrumentsList = None
    symbolToInstrumentMap = None
    tokenToInstrumentMap = None

    def __init__(self,kite):
        exchanges = ["NSE","NFO","MCX"]
        """for exchange in exchanges:
            self.instruments = pd.DataFrame(kite.instruments(exchange=exchange))
            self.instruments.to_csv("./config/instruments"+exchange+".csv", index = False)"""

    def getInstrumentDataBySymbol(self,tradingSymbol,exchange):
        instruments = pd.read_csv("./config/instruments"+exchange+".csv")
        return instruments[instruments['tradingsymbol'] == tradingSymbol]['instrument_token'].values[0]


    def getInstrumentDataByToken(self,instrumentToken,exchange):
        instruments = pd.read_csv("./config/instruments"+exchange+".csv")
        return instruments[instruments['instrument_token'] == instrumentToken]['tradingsymbol'].values[0]

    @staticmethod
    def get_nearest_expiry_options(name,strikeprice,exchange):
        instruments = pd.read_csv("./config/instruments"+exchange+".csv")
        regex = "^"+name+".*"+str(strikeprice)
        #print(instruments[instruments['tradingsymbol'].str.contains(regex+"CE$")].sort_values(by = 'expiry'))
        atm_ce = instruments[instruments['tradingsymbol'].str.contains(regex+"CE$")].sort_values(by = 'expiry').iloc[0]
        atm_pe = instruments[instruments['tradingsymbol'].str.contains(regex+"PE$")].sort_values(by = 'expiry').iloc[0]
        return atm_ce,atm_pe
           