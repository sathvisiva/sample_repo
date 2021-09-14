import pandas as pd
import numpy as np


class SupportResistance:

    @staticmethod
    def isSupport(df,i):
        support = df['low'][i] < df['low'][i-1]  and df['low'][i] < df['low'][i+1] \
            and df['low'][i+1] < df['low'][i+2] and df['low'][i-1] < df['low'][i-2]
        return support

    @staticmethod
    def isResistance(df,i):
        resistance = df['high'][i] > df['high'][i-1]  and df['high'][i] > df['high'][i+1] \
        and df['high'][i+1] > df['high'][i+2] and df['high'][i-1] > df['high'][i-2] 
        return resistance

    @staticmethod
    def isFarFromLevel(l,levels,s):
        return np.sum([abs(l-x) < s  for x in levels]) == 0


    def calculateSupportResistance(self,df):
        s =  np.mean(df['high'] - df['low'])
        levels = []
        for i in range(2,df.shape[0]-2):
            if self.isSupport(df,i):
                l = df['low'][i]
                if self.isFarFromLevel(l,levels,s):
                    levels.append((i,l))
            elif self.isResistance(df,i):
                l = df['high'][i]
                if self.isFarFromLevel(l,levels,s):
                    levels.append((i,l))
        support_res = []
        for level in levels:
            support_res.append(level[1])

        return support_res