from kiteconnect import KiteConnect
import datetime
import time
from wrapper.kiteext import KiteExt

from common import *


from datetime import datetime


#now = datetime.datetime.now()
#now = now.strftime("%Y-%m-%d %H:%M:%S")

class My_Class:
    def __init__(self):
        LoginWrapper = Login.Login()
        kite = LoginWrapper.loginkite()

    def get_instruments(self,exchange="NFO"):
        #get instruments and stored into file(instruments.txt)
        instruments = self.kite.instruments(exchange=exchange)
        with open("instruments.txt","w+") as writer:
            writer.write(",".join(str(li) for li in instruments))

        #logging.info("Instrumets stored into instruments file... ")
    def get_instrument_id(self,listofsymbols):
        with open("instruments.txt","r") as reader:
            lines = reader.readlines()
            #print(lines)

    def get_ltp(self ,symbol):
        data = self.kite.ltp(symbol)
        if len(symbol) == 1:
            return data[symbol[0]]["last_price"]
        else:
            return data

    def get_ohcl(self,symbol):
        data = self.kite.ohlc(symbol)
        return data

    def get_quote(self,symbol):
        data = self.kite.ohlc(symbol)
        return data
    def get_gtt(self,tr_id):
        tr_id = tr_id["trigger_id"]
        return self.kite.get_gtt(tr_id)
    def get_gtt_status(self,gtt_id):
        res = self.get_gtt(gtt_id)
        return res["status"]

    def get_active_gtts(self):
        resli = []
        res = self.kite.get_gtts()
        for i in res:
            if i["status"] == "active":
                resli.append(i)
        return resli

    def get_gtts(self):
        return self.kite.get_gtts()

    def delete_gtt(self,trigger_id):
        return self.kite.delete_gtt(trigger_id)

    def check_gtt_status(self,trigger_id):
        res = self.get_gtt(trigger_id)
        return res["status"]

    def delete_all_active_gtt(self,gtt_list):
        for i in gtt_list:
            status = i["status"]
            if status == "active":
                self.delete_gtt(i['id'])
        return True

    def place_gtt(self,trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders):
        return self.kite.place_gtt(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)

    def modify_gtt(self,trigger_id, trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders):
        trigger_id = trigger_id["trigger_id"]
        return self.kite.modify_gtt(trigger_id, trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)
    def order_trades(self,order_id):
        print("inside order trades")
        print(self.kite.order_trades(order_id))
        return self.kite.order_trades(order_id)
    def get_order_id(self,gtt):
        or_id = gtt["orders"][0]["result"]["order_result"]["order_id"]
        return or_id

    def new_modify_gtt(self,trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders,gtt_id=None,\
            new_gtt=False,modify=False,modify_val=2):
        if new_gtt:
            last_price = self.get_ltp(["NFO:"+str(tradingsymbol)])
            trigger_values = [last_price+modify_val]
            orders[0]["price"] = last_price + modify_val
            try:
                gtt_id = self.kite.place_gtt(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)
                print("created new gtt details:")
                print("symbol: "+str(tradingsymbol),end =", ")
                print("Trigger type: " +str(orders[0]["transaction_type"]),end =", ")
                print("ltp: "+str(last_price),end =", ")
                print("price: "+str(trigger_values),end =", ")
                print("quantity: "+str(orders[0]["quantity"]))

            except Exception as e:
                print(e)
                #Trigger already met
        elif modify:
            print("modify Gtt: ")
            print("modify Gtt details: ")
            last_price = self.get_ltp(["NFO:"+str(tradingsymbol)])
            trigger_values = [last_price+modify_val]
            orders[0]["price"] = last_price + modify_val
            try:
                gtt_id = self.modify_gtt(gtt_id,trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)
                print("symbol: "+str(tradingsymbol),end =", ")
                print("ltp: "+str(last_price),end =", ")
                print("price: "+str(trigger_values),end =", ")
                print("Trigger type: " +str(orders[0]["transaction_type"]))
            except Exception as e:
                    print(e)
                    print(type(e))
                    print(type(str(e)))
        return gtt_id

    def place_oco_gtt(self,gtt_id,trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders,target_stoploss):
        oco_trns_type = None
        target = 0
        stoploss = 0
        t_vals = []
        oco_id = None
        gtt_details = self.get_gtt(gtt_id)
        oco_quantity = gtt_details["orders"][0]["quantity"]
        order_transaction_type = gtt_details["orders"][0]["transaction_type"]
        oco_price = gtt_details["orders"][0]["price"]
        oco_trigger_type = "two-leg"
        if order_transaction_type == "BUY":
            oco_trns_type = "SELL"
        else:
            oco_trns_type = "BUY"
        t_vals.append(round(oco_price)-target_stoploss)
        t_vals.append(round(oco_price)+target_stoploss)
        target = round(oco_price)-target_stoploss
        stoploss = round(oco_price)+target_stoploss
        order_dict = [{"transaction_type":oco_trns_type ,\
                "quantity": oco_quantity,"order_type": "LIMIT",\
                "product": "NRML" , "price":target },\
                {"transaction_type": oco_trns_type, \
                "quantity": oco_quantity,"order_type": "LIMIT", \
                "product": "NRML" , "price": stoploss}]
        print("place oco gtt order:")
        #print("self.kite.place_gtt(oco_trigger_type, tradingsymbol, exchange, [target,stoploss], last_price,order_dict)")
        #print("self.kite.place_gtt("+str(oco_trigger_type)+","+str(tradingsymbol)+","+str( exchange)+","+str( [target,stoploss])\
        #        +","+str( last_price)+","+str(order_dict)+")")
        oco_id = self.kite.place_gtt(oco_trigger_type, tradingsymbol, exchange, t_vals, last_price,order_dict)
        print("oco GTT details:")
        print("symbol: "+str(tradingsymbol),end =", ")
        print("quantity: "+str(oco_quantity),end =", ")
        print("oco transaction type: "+str(oco_trns_type),end =", ")
        print("trigger price:"+str(t_vals),end =", ")
        print("price: "+str(target)+","+str(stoploss))
        return oco_id

    def place_order_and_place_oco(self,trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders,\
            target_stoploss,modify_val=2,modify=True):
        gtt_id = None
        oco_id = ""
        order_id = ""
        order_placed = False
        oco_placed = False
        first = True
        oco = False
        while True:
            if first:
                while(gtt_id is None):
                    gtt_id = self.new_modify_gtt(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders,\
                            new_gtt=True,modify=False,modify_val=modify_val)
            i = 1
            while(i<=5):
                time.sleep(1)
                gtt = self.get_gtt(gtt_id)
                status = gtt["status"]
                if status == "active":
                    i = i+1
                    if i == 5:
                        print("checked gtt status for 5s, not triggered:")
                    #order_placed = True
                    #modify = False
                    #oco = True
                    #order_id = gtt_id
                elif status == "triggered":
                    print("order placed...")
                    order_id = self.get_order_id(gtt)
                    order_details = self.order_trades(order_id)
                    order_placed = True
                    modify = False
                    oco = True
                    break
                else:
                    break
            if modify == True:
                print("waited for 5s Gtt not placed, try to modify gtt:")
                gtt_id = self.new_modify_gtt(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders,gtt_id,\
                            new_gtt=False,modify=True,modify_val=modify_val)
                first = False
                print("Gtt modified...")
            if oco == True:
                for i in range(3):
                    #print("create oco Gtt:")
                    oco_id = self.place_oco_gtt(gtt_id,trigger_type, tradingsymbol, exchange, trigger_values, last_price, \
                            orders,target_stoploss)
                    oco_status = self.check_gtt_status(oco_id)
                    if oco_status == "active":
                        oco_placed = True
                        print("oco gtt placed:")
                        break

            if order_placed and oco_placed:
                #return order_id,oco_id
                return gtt_id,oco_id


    def check_gtt_triggered(self,gtt_id):
        now = datetime.now()
        #now_time = now.strftime("%H:%M:%S")
        print("Monitring oco gtt result from: "+str(now))
        while(True):
            res = self.check_gtt_status(gtt_id)
            time.sleep(2)
            if res == "triggered":
                now1 = datetime.now()
                print("oco gtt triggered: "+str(now1))
                print(self.get_gtt(gtt_id))
                return True
    def check_target_sp(self,order_id,oco_id):
        price = 0
        ex_price = 0
        order = self.get_gtt(order_id)
        oco = self.get_gtt(oco_id)
        side = order["orders"][0]["transaction_type"]
        ex_side = oco["orders"][0]["transaction_type"]
        sym = order["orders"][0]["tradingsymbol"]
        ex_sym = oco["orders"][0]["tradingsymbol"]
        if order["status"] == "triggered":
            price = order["orders"][0]["price"]
        if oco["status"] == "triggered":
            ex_price = oco["orders"][0]["price"]
        if side == "BUY":
            if ex_price > price:
                return True
            else:
                return False
        elif side == "SELL":
            if price > ex_price:
                return True
            else:
                return False