import sys
from datetime import datetime, timedelta
from market_maker.market_maker import OrderManager

LEVERAGE = 25

class NakedPerpOrderManager(OrderManager):

    def __init__(self, *args, **kwargs):
        super(NakedPerpOrderManager, self).__init__(*args, **kwargs)

        #set lvg
        self.exchange.bitmex.isolate_margin(self.exchange.symbol, LEVERAGE)

    def place_orders(self) -> None:
        WINDOW_S = 600
        MIN_RATE = .0005
        ORDER_QUANTITY = 25
        LEVERAGE = 50

        td_h = lambda h : timedelta(hours=h)


        # calculate time to funding
        utc_t = datetime.utcnow().time()
        utc_td = timedelta(hours=utc_t.hour, minutes=utc_t.minute, seconds=utc_t.second)
        time_to_funding = (td_h(24) - (utc_td + td_h(4))) % td_h(8)
        print('TIME TO FUNDING:',time_to_funding)
        delta = self.exchange.get_delta()
        print('DELTA:', delta)
        ticker = self.exchange.get_ticker()
        bid = ticker['buy']
        ask = ticker['sell']
        print('BID:', bid)
        print('ASK:', ask)

        buy_orders = []
        sell_orders = []

        # if before and good funding rate, enter or adjust short
        if time_to_funding.total_seconds() < WINDOW_S:
            funding_rate = self.exchange.get_instrument()['fundingRate']
            print('FUNDING RATE:', funding_rate)
            if funding_rate > MIN_RATE:
                if delta > -1 * ORDER_QUANTITY:
                    sell_orders.append({'price': ask , 'orderQty': ORDER_QUANTITY + delta, 'side': "Sell"})
        # if after and short, buy back short, if after and order still open, close order
        else:
            num_orders = len(self.exchange.get_orders())
            if delta == 0 and num_orders > 0:
                self.exchange.cancel_all_orders()
            if delta < 0:
                buy_orders.append({'price': bid, 'orderQty': -1 * delta, 'side': "Buy"})

        self.converge_orders(buy_orders, sell_orders)

def run() -> None:
    order_manager = NakedPerpOrderManager()
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
