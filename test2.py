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


LoginWrapper = Login.Login()
kite = LoginWrapper.loginkite()
SupportResistanceWrapper = SupportResistance.SupportResistance()
CandlePatternWrapper = CandlePattern.CandlePattern()
TelegrambotWrapper = Telegrambot.Telegrambot()

TelegrambotWrapper.send_message("GTT Order place 10mins tf : target 237:0SL 202.05" )

