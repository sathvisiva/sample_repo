import logging
import json

from ticker.BaseTicker import BaseTicker
from instruments import Instruments
from models.TickData import TickData

class ZerodhaTicker():
    def __init__(self, kite,exchange):
        self.ticker = kite.kws()
        self.Instrument = Instruments.Instruments(kite)
        self.tickListeners = []

    def startTicker(self):
        ticker = self.ticker
        ticker.on_connect = self.on_connect
        ticker.on_close = self.on_close
        ticker.on_error = self.on_error
        ticker.on_reconnect = self.on_reconnect
        ticker.on_noreconnect = self.on_noreconnect
        ticker.on_ticks = self.on_ticks
        ticker.on_order_update = self.on_order_update

        logging.info('ZerodhaTicker: Going to connect..')
        self.ticker.connect(threaded=True)

    def registerListener(self, listener):
    # All registered tick listeners will be notified on new ticks
        self.tickListeners.append(listener)

    def stopTicker(self):
        logging.info('ZerodhaTicker: stopping..')
        self.ticker.close(1000, "Manual close")

    def registerSymbols(self, tokens):
        """tokens = []
        for symbol in symbols:
            isd = self.Instrument.getInstrumentDataBySymbol(symbol)
            token = isd
            
            logging.info('ZerodhaTicker registerSymbol: %s token = %s', symbol, token)
            tokens.append(token)
        print(tokens)
        logging.info('ZerodhaTicker Subscribing tokens %s', tokens)"""
        self.ticker.subscribe(tokens)

    
    def unregisterSymbols(self, symbols):
        tokens = []
        for symbol in symbols:
            isd = self.Instrument.getInstrumentDataBySymbol(symbol)
            token = isd['instrument_token']
            logging.info('ZerodhaTicker unregisterSymbols: %s token = %s', symbol, token)
            tokens.append(token)
        logging.info('ZerodhaTicker Unsubscribing tokens %s', tokens)
        self.ticker.unsubscribe(tokens)

    def on_ticks(self, ws, brokerTicks):
        ticks = []
        for bTick in brokerTicks:
            #isd = Instruments.getInstrumentDataByToken(bTick['instrument_token'])
            #tradingSymbol = isd['tradingsymbol']
            tick = TickData("CRUDE")
            tick.lastTradedPrice = bTick['last_price']
            tick.lastTradedQuantity = bTick['last_quantity']
            tick.avgTradedPrice = bTick['average_price']
            tick.volume = bTick['volume']
            tick.totalBuyQuantity = bTick['buy_quantity']
            tick.totalSellQuantity = bTick['sell_quantity']
            tick.open = bTick['ohlc']['open']
            tick.high = bTick['ohlc']['high']
            tick.low = bTick['ohlc']['low']
            tick.close = bTick['ohlc']['close']
            tick.change = bTick['change']
            ticks.append(tick)
            print(tick.close)

        #self.onNewTicks(ticks)

    def on_connect(self, ws, response):
        self.ticker.subscribe([58546951])

    def on_close(self, ws, code, reason):
        #self.onDisconnect(code, reason)
        pass

    def on_error(self, ws, code, reason):
        pass
        #self.onError(code, reason)

    def on_reconnect(self, ws, attemptsCount):
        pass
        #self.onReconnect(attemptsCount)

    def on_noreconnect(self, ws):
        pass
        #self.onMaxReconnectsAttempt()

    def on_order_update(self, ws, data):
        print(data)
        #self.onOrderUpdate(data)


    
