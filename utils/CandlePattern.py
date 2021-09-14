import pandas as pd
import numpy as np

class CandlePattern:

    def isBullish(self,df):
        print(df)
        bullish = False
        if df['close'] > df['open']:
            bullish = True
        return bullish