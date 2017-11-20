# Nick Schmandt (n.schmandt@gmail.com), CloudQuant, 11/13/17

# This is a demo strategy, loosely based on the breakout strategy described earlier, to show some of the different
# types of stock order and sale alogorithms that are available on the CloudQuant platform.

from cloudquant.interfaces import Strategy
from cloudquant.util import dt_from_muts
import numpy as np

end_delay = 20  # in minutes, how long before the end of the day to stop trading.
start_delay = 10  # in minutes, how long after market open before we start trading

index = 5  # how many days of highs to average over
stop_profit_ratio = 1.05  # what profit of the initial purchase price before exitting a trade
stop_loss_ratio = .95  # what loss of the initial purchase price before exitting a trade

purchase_amount = 25000  # dollar value that we want each purchase to be worth


class breakout_purchase(Strategy):
    @classmethod
    def is_symbol_qualified(cls, symbol, md, service, account):

        # S&P 500 stocks
        # handle_list = service.symbol_list.get_handle('9a802d98-a2d7-4326-af64-cea18f8b5d61') #this is all stocks on S&P500
        # return service.symbol_list.in_list(handle_list,symbol)

        return symbol in ['AAPL', 'EBAY', 'AMZN', 'ORCL', 'WMT']

    def __init__(self):

        self.IsPositionOn = False  # do we have a position on?
        self.entry_price = 0  # estimated price of our position
        self.model_start = 0  # time to start, set in on_start
        self.IsPurchasable = True  # OK to purchase? (not repurchasing what we already sold)

    def on_finish(self, md, order, service, account):
        pass

    def on_minute_bar(self, event, md, order, service, account, bar):

        # make sure it's not too late in the day
        if service.system_time < md.market_close_time - service.time_interval(minutes=end_delay, seconds=1):

            # gather some market statistics
            md_daily = md.bar.daily(start=-index)
            md_high = md_daily.high
            average_high = np.mean(md_high)
            md_low = md_daily.low
            average_low = np.mean(md_low)

            # bar values at the current minute
            bar_1 = bar.minute()
            bar_close = bar_1.close
            bar_askvol = bar_1.askvol
            bar_bidvol = bar_1.bidvol

            if len(bar_close) > 0 and bar_close[0] != 0:

                # if the stock has returned to its normal values, we would consider rentering a position on it.
                if (average_high) > bar_close[0] and (average_low) < bar_close[0]:
                    self.IsPurchasable = True

                # we want to have at least a certain amount of time left before entering positions
                if service.system_time > self.model_start:
                    # make sure we're not already in a position and the stock hasn't already been bought and resold recently.
                    if self.IsPositionOn == False and self.IsPurchasable == True:

                        # go long if stock is above its normal values
                        if (average_high) < bar_close[0]:
                            
                            #Now that we know we are going long, we have to figure out how many shares to purchase
                            
                            #One option is to just use a fixed number of shares
                            num_shares=100
                            
                            #Another is to allocate the amount you purchase based on the volume at the last minute.
                            #You have options that include md[self.symbol].L1.ask_size and md[self.symbol].L1.minute_volume
                            #For this example I use the bar's askvol, which I have found to be the most accurate.
                            num_shares=int(bar_askvol[0]*.1)
                            
                            #Finally, we have the option of purchasing a fixed dollar amount of a particular share.
                            #This is the recommended way. You can adjust the amount based on how much risk you want to take.
                            num_shares=np.round(purchase_amount/md[self.symbol].L1.last)

                            # Play around with the different volumes and see how they affect the performance.
                            
                            

                            order_id = order.algo_buy(self.symbol, algorithm="market", intent="init", order_quantity=num_shares)

                            print('Purchasing {0} after breakout at {1}, purchased {2} shares at {3}' \
                                  .format(self.symbol, service.time_to_string(service.system_time), num_shares,
                                          bar_close[0]))
                            self.IsPositionOn = True
                            self.entry_price = bar_close[0]


                    elif self.IsPositionOn == True:
                        # there is a position on, therefore we want to check to see if
                        # we should realize a profit or stop a loss

                        # the stock has dropped too low, exit out of this position
                        if self.entry_price * stop_loss_ratio > bar_close[0]:

                            sell_order_id = order.algo_sell(self.symbol, algorithm="market", intent="exit")

                            print('selling out of {0} at {1} due to stock dropping below average high at {1}'.format(
                                self.symbol, service.time_to_string(service.system_time), bar_close[0]))
                            self.IsPositionOn = False
                            self.IsPurchasable = False

                        # we've made our target profit, let's back out of the trade now
                        elif self.entry_price * stop_profit_ratio < bar_close[0]:

                            sell_order_id = order.algo_sell(self.symbol, algorithm="market", intent="exit")

                            print('selling out of {0} at {1} due to stock reaching target profit at {2}'.format(
                                self.symbol, service.time_to_string(service.system_time), bar_close[0]))
                            self.IsPositionOn = False
                            self.IsPurchasable = False

        else:

            # close out of our long positions at the end of the day.
            if self.IsPositionOn == True:
                sell_order_id = order.algo_sell(self.symbol, "market", intent="exit")
                self.IsPositionOn = False

    def on_start(self, md, order, service, account):

        self.model_start = service.system_time + service.time_interval(minutes=start_delay, seconds=1)
