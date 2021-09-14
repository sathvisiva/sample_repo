import math
import uuid
import time
import logging
import calendar
from datetime import date, datetime, timedelta
from config.Config import getHolidays
from models.Direction import Direction
from trademgmt.TradeState import TradeState
import json

class Utils:
    dateFormat = "%Y-%m-%d"
    timeFormat = "%H:%M:%S"
    dateTimeFormat = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def getHolidays():
        with open('../config/holidays.json', 'r') as holidays:
            holidaysData = json.load(holidays)
            return holidaysData

    @staticmethod
    def roundoff(price):
        return round(price,2)

    @staticmethod
    def roundToNSEPrice(price):
        x = round(price,2)*20
        y = math.ceil
        return y/20

    @staticmethod
    def isHoliday(datetimeObj):
        dayOfWeek = calendar.day_name[datetimeObj.weekday()]
        if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
            return True
        dateStr = Utils.convertToDateStr(datetimeObj)
        holidays = getHolidays()
        if (dateStr in holidays):
            return True
        else:
            return False

    @staticmethod
    def isTodayHoliday():
        return Utils.isHoliday(datetime.now())

    @staticmethod
    def getTimeOfDay(hours, minutes, seconds, dateTimeObj = None):
        if dateTimeObj == None:
            dateTimeObj = datetime.now()
        dateTimeObj  = dateTimeObj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
        return dateTimeObj

    @staticmethod
    def getTimeOfToDay(hours, minutes, seconds):
        return Utils.getTimeOfDay(hours, minutes, seconds, datetime.now())

    @staticmethod
    def getTodayDateStr():
        return Utils.convertToDateStr(datetime.now())

    @staticmethod
    def convertToDateStr(datetimeObj):
        return  datetimeObj.strftime(Utils.dateFormat)

    @staticmethod
    def convertToDateStr(datetimeObj):
        return datetimeObj.strftime(Utils.dateFormat)

    @staticmethod
    def getMarketStartTime(dateTimeObj = None):
        return None


    @staticmethod
    def isTodayHoliday():
        return Utils.isHoliday(datetime.now())

    @staticmethod
    def getMarketStartTime(dateTimeObj = None):
        return Utils.getTimeOfDay(9, 15, 0, dateTimeObj)

    @staticmethod
    def getMarketEndTime(dateTimeObj = None):
        return Utils.getTimeOfDay(15,30,0,dateTimeObj)

    @staticmethod
    def isMarketOpen():
        if Utils.isTodayHoliday():
            return False
        now = datetime.now()
        marketStartTime = Utils.getMarketStartTime()
        marketEndTime = Utils.getMarketEndTime()
        return now >= marketStartTime and now <= marketEndTime

    @staticmethod
    def isMarketClosedForTheDay():
        if Utils.isTodayHoliday():
            return True
        now = datetime.now()
        marketEndTime = Utils.getMarketEndTime
        return now > marketEndTime

    @staticmethod
    def getEpoch(datetimeObj = None):
        if datetimeObj == None:
            datetimeObj = datetime.now()
        epochSeconds = datetime.timestamp(datetimeObj)
        return int(epochSeconds)

    
    @staticmethod
    def waitTillMarketOpens():
        nowEpoch = Utils.getEpoch(datetime.now())
        marketStartTimeEpoch = Utils.getEpoch(Utils.getMarketStartTime())
        waitSeconds = marketStartTimeEpoch - nowEpoch
        if waitSeconds > 0 :
            #logging.info("%s: Waiting for %d seconds till market opens...", context, waitSeconds)
            time.sleep(waitSeconds)

    @staticmethod
    def generateTradeID():
        return str(uuid.uuid4())

    @staticmethod
    def calculateTradePnl(trade):
        if trade.tradeState == TradeState.ACTIVE:
            if trade.cmp > 0:
                if trade.direction == Direction.LONG:
                    trade.pnl = Utils.roundoff(trade.filledQty * (trade.cmp - trade.entry))
                else:
                    trade.pnl = Utils.roundOff(trade.filledQty * (trade.entry - trade.cmp))
        else:
            if trade.exit > 0:
                if trade.direction == Direction.LONG:
                    trade.pnl = Utils.roundOff(trade.filledQty * (trade.exit - trade.entry))
                else:
                    trade.pnl = Utils.roundOff(trade.filledQty * (trade.entry - trade.exit))
        tradeValue = trade.entry * trade.filledQty
        if tradeValue > 0:
            trade.pnlPercentage = Utils.roundOff(trade.pnl * 100 / tradeValue)
        return trade

    @staticmethod
    def getNearestStrikePrice(price, nearestMultiple = 100):
        strikeprice = 0.0
        inputPrice = int(price)
        remainder = int(inputPrice % nearestMultiple)
        if remainder < int(nearestMultiple/2):
            return inputPrice - remainder
        else:
            return inputPrice + (nearestMultiple - remainder)

    
    

    
    
    
    


