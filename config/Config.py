import json
import os

def getHolidays():
  with open('../config/holidays.json', 'r') as holidays:
    holidaysData = json.load(holidays)
    return holidaysData

