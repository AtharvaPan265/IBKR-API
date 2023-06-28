
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract, ContractDetails
from ibapi.contract import ComboLeg
from ibapi.order import Order
import threading
import time


class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.conIds = []
    # def error(self, reqId, errorCode, errorString):
   #     print("Error {} {} {}".format(reqId,errorCode,errorString))

    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        conId = contractDetails.contract.conId
        self.conIds.append(conId)
        print(conId)

    def contractDetailsEnd(self, reqId):
        super().contractDetailsEnd(reqId)
        print("ContractDetailsEnd. ReqId:", reqId)


def websocket_con():
    app.run()


app = TradingApp()
app.connect("127.0.0.1", 7497, clientId=1)

# starting a separate daemon thread to execute the websocket connection
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1)  # some latency added to ensure that the connection is established

# creating object of the Contract class - will be used as a parameter for other function calls


def comboOptContract(symbol, conID, action, sec_type="BAG", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    # print(conID[0])
    leg1 = ComboLeg()
    leg1.conId = conID[0]
    leg1.ratio = 1
    leg1.action = action[0]
    leg1.exchange = exchange
    # print(conID[1])
    leg2 = ComboLeg()
    leg2.conId = conID[1]
    leg2.ratio = 1
    leg2.action = action[1]
    leg2.exchange = exchange

    contract.comboLegs = [leg1, leg2]
    return contract

# creating object of the limit order class - will be used as a parameter for other function calls


def limitOrder(direction, quantity, lmt_price):
    order = Order()
    order.action = direction
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order


def genConIdList(symbol, strikes, right, expiry):
    #conIDlist = []
    contract1 = Contract()
    contract1.symbol = symbol
    contract1.secType = "OPT"
    contract1.exchange = "Smart"
    contract1.currency = "USD"
    contract1.lastTradeDateOrContractMonth = expiry
    contract1.strike = strikes[0]
    contract1.right = right
    app.reqContractDetails(1, contract1)
    contract2 = Contract()
    contract2.symbol = symbol
    contract2.secType = "OPT"
    contract2.exchange = "Smart"
    contract2.currency = "USD"
    contract2.lastTradeDateOrContractMonth = expiry
    contract2.strike = strikes[1]
    contract2.right = right
    app.reqContractDetails(2, contract2)


def placeOrderStrat(app, symbol, expiry, strat, strikes: list, right=None):
    strikes.sort()
    rights = []
    match strat:
        case "call spread":
            CP = "C"
            match right:
                case "bear":
                    rights = ["SELL", "BUY"]
                case "bull":
                    rights = ["BUY", "SELL"]
                case _:
                    print("you must delare call/put")
        case "put spread":
            CP = "P"
            match right:
                case "bear":
                    rights = ["BUY", "SELL"]
                case "bull":
                    rights = ["SELL", "BUY"]
                case _:
                    print("you must delare call/put")
                    
    order_id = app.nextValidOrderId
    genConIdList(symbol, strikes, CP, expiry)
    time.sleep(1)
    app.placeOrder(order_id, comboOptContract(symbol, app.conIds, rights), limitOrder("BUY", 1, 1.4))  # EClient function to request contract details
    # some latency added to ensure that the contract details request has been processed
    time.sleep(5)
    app.conIds.clear()

'''
bull call spread = call  debit  spread
bear call spread = call  credit spread
bull put  spread  = put  credit spread
bear put  spread  = put  debit  spread
'''
placeOrderStrat(app, "AMD", "20230721", "call spread", [111, 110],  "bull")

app.reqIds(-1)
time.sleep(2)

placeOrderStrat(app, "INTC", "20230721", "put spread", [33, 32.5],  "bear")
