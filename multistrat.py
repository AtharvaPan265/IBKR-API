import threading
import time

from ibapi.client import EClient
from ibapi.contract import ComboLeg
from ibapi.contract import Contract, ContractDetails
from ibapi.order import Order
from ibapi.wrapper import EWrapper


class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.conIds = []

    # def error(self, reqId, errorCode, errorString):
    #     print("Error {} {} {}".format(reqId,errorCode,errorString))

    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        # print("NextValidId:", orderId)

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        conId = contractDetails.contract.conId
        self.conIds.append(conId)
        # print(conId)

    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        # print("ContractDetailsEnd. ReqId:", reqId)


def websocket_con():
    app.run()


app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

# starting a separate daemon thread to execute the websocket connection
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1)  # some latency added to ensure that the connection is established


def comboOptContract(symbol, conIDs, actions, sec_type="BAG", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange

    combo_legs = []
    for i in range(len(conIDs)):
        leg = ComboLeg()
        leg.conId = conIDs[i]
        leg.ratio = 1
        leg.action = actions[i]
        leg.exchange = exchange
        combo_legs.append(leg)

    contract.comboLegs = combo_legs
    return contract


def limitOrder(direction, quantity, lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order


def genConIdList(symbol, strikes, right, expiry):
    # conIDlist = []
    for idx, strike in enumerate(strikes):
        contract1 = Contract()
        contract1.symbol = symbol
        contract1.secType = "OPT"
        contract1.exchange = "Smart"
        contract1.currency = "USD"
        contract1.lastTradeDateOrContractMonth = expiry
        contract1.strike = strike
        contract1.right = right[idx]
        app.reqContractDetails(idx + 1, contract1)


def placeOrderStrat(app: TradingApp, symbol: str, expiry: str, strat: str, strikes: list, right=""):
    strikes.sort()
    rights = []
    CP = []
    temp = 0
    match strat.lower():
        case "call spread":
            CP = ["C", "C"]
            match right:
                case "bear":
                    rights = ["SELL", "BUY"]
                case "bull":
                    rights = ["BUY", "SELL"]
                case _:
                    temp = 1
                    print("you must delare call/put")
        case "put spread":
            CP = ["P", "P"]
            match right:
                case "bull":
                    rights = ["BUY", "SELL"]
                case "bear":
                    rights = ["SELL", "BUY"]
                case _:
                    temp = 1
                    print("you must delare call/put")
        case "iron condor":
            if len(strikes) == 4:
                CP = ["P", "P", "C", "C"]
                rights = ["BUY", "SELL", "SELL", "BUY"]
                strikes = [strikes[0], strikes[1], strikes[2], strikes[3]]
            else:
                temp = 1
                print("you need 4 strikes to place an iron condor")
        case "iron butterfly":
            if len(strikes) == 3 or (len(strikes) == 4 and strikes[1] == strikes[2]):
                CP = ["P", "P", "C", "C"]
                rights = ["BUY", "SELL", "SELL", "BUY"]
                strikes = [strikes[0], strikes[1], strikes[1], strikes[2]]
            else:
                temp = 1
                print("you need 3 strikes to place an iron butterfly")
    if (temp == 0):
        print("placing " + right + " " + strat)
    order_id = app.nextValidOrderId
    genConIdList(symbol, strikes, CP, expiry)
    time.sleep(1)
    app.placeOrder(order_id, comboOptContract(symbol, app.conIds, rights),
                   limitOrder("BUY", 1, 1.4))  # EClient function to request contract details
    # some latency added to ensure that the contract details request has been processed
    time.sleep(5)
    app.conIds.clear()
    app.reqIds(-1)
    time.sleep(2)


placeOrderStrat(app, "AMD", "20230721", "call spread", [111, 110], "bull")
placeOrderStrat(app, "INTC", "20230721", "put spread", [33, 32.5], "bear")
placeOrderStrat(app, "XOM", "20230721", "iron condor", [104, 106, 102, 100])
placeOrderStrat(app, "SNAP", "20230721", "iron butterfly", [11, 10, 12])

app.disconnect()
exit()
