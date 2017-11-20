# Nick Schmandt (n.schmandt@gmail.com), CloudQuant, 11/13/17

# This is a demo strategy, loosely based on the breakout strategy described earlier, to show some of the different
# types of stock order and sale alogorithms that are available on the CloudQuant platform.

from cloudquant.interfaces import Strategy
from cloudquant.util import dt_from_muts
import numpy as np

# These functions are for the midpoint peg, they will only work in the ELITE Cloudquant Version. Delete or Comment out for Lite.
lime_midpoint_limit_buy = "4e69745f-5410-446c-9f46-95ec77050aa5"
lime_midpoint_limit_sell = "23d56e4a-ca4e-47d0-bf60-7d07da2038b7"

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
                            # Now that we know we are going long, we have to figure out the best way to do it. First, we determine
                            # the number of shares
                            
                            num_shares = np.round(purchase_amount / md[self.symbol].L1.last)

                            # To execute the trade, we have a few options. First, we could just purchase at market value,
                            # which means we buy at the price someone says they are willing to pay.
                            # You probably wouldn't do this live trading but it works for backtesting.

                            # order_id = order.algo_buy(self.symbol, algorithm="market", intent="init", order_quantity=num_shares)

                            # Alternatively, we can use a limit order. Exactly what limit you choose depends on how aggressively
                            # you want to place your position. Placing a limit at the ask is probably going to be very similar
                            # to a market order in backtesting, but will avoid a pull to higher values if the stock swings up.
                            # you can go higher than the market price as well, if you want to be extra sure your order will fill
                            # in a price range that is controlled. If you don't need your order filled immediately, you can pick
                            # a limit value that is between the bid and ask price. You'll get a better price for your shares, but
                            # your order may not fill.
                            # Currently in the CQ environment, my limit orders seem to fill pretty readily below ask price, which
                            # would not reflect real trading. So be careful to pick realistic numbers for your limits.

                            # order_id = order.algo_buy(self.symbol, algorithm="limit", price=md[self.symbol].L1.ask-.01, intent="init", order_quantity=num_shares)
                            # order_id = order.algo_buy(self.symbol, algorithm="limit", price=md[self.symbol].L1.ask*.99, intent="init", order_quantity=num_shares)

                            # Finally, we can do what is called a midpoint-peg. Check the references for a mathematical description, but
                            # it's essentially the midpoint between bid and ask prices. It is only available in ELITE. You can also set
                            # the price as well, though I'm not entirely sure how the algorithm incorporates that price into its what it
                            # predicts. It works very well, but if your algorithm requires getting your stocks quickly, it may not be the
                            # best choice. It will make your algorithm look better than it is because it has unrealistic price points for
                            # your purchases.

                            # order_id = order.algo_buy(self.symbol, algorithm=lime_midpoint_limit_buy, price=md[self.symbol].L1.ask*1.05, intent="init", order_quantity=num_shares)
                            order_id = order.algo_buy(self.symbol, algorithm=lime_midpoint_limit_buy,
                                                      price=md[self.symbol].L1.ask + .05, intent="init",
                                                      order_quantity=num_shares)

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

                            # We have the same options for selling that we had for purchasing. We can do a market order.

                            # sell_order_id = order.algo_sell(self.symbol, algorithm="market", intent="exit")

                            # Or a limit order, some value around the ask and bid prices.

                            # sell_order_id = order.algo_sell(self.symbol, algorithm="limit", price=md[self.symbol].L1.bid-.05, intent="exit")
                            # sell_order_id = order.algo_sell(self.symbol, algorithm="limit", price=md[self.symbol].L1.bid*.95, intent="exit")

                            # Finally, a midpoint peg, again, this only works in CloudQuant Elite.

                            sell_order_id = order.algo_sell(self.symbol, algorithm=lime_midpoint_limit_sell,
                                                            intent="exit")

                            print('selling out of {0} at {1} due to stock dropping below average high at {1}'.format(
                                self.symbol, service.time_to_string(service.system_time), bar_close[0]))
                            self.IsPositionOn = False
                            self.IsPurchasable = False

                        # we've made our target profit, let's back out of the trade now
                        elif self.entry_price * stop_profit_ratio < bar_close[0]:

                            # We have the same options for selling that we had for purchasing. We can do a market order.

                            # sell_order_id = order.algo_sell(self.symbol, algorithm="market", intent="exit")

                            # Or a limit order, some value around the ask and bid prices.

                            # sell_order_id = order.algo_sell(self.symbol, algorithm="limit", price=md[self.symbol].L1.bid-.05, intent="exit")
                            # sell_order_id = order.algo_sell(self.symbol, algorithm="limit", price=md[self.symbol].L1.bid*.95, intent="exit")

                            # Finally, a midpoint peg, again, this only works in CloudQuant Elite.

                            sell_order_id = order.algo_sell(self.symbol, algorithm=lime_midpoint_limit_sell,
                                                            intent="exit")

                            print('selling out of {0} at {1} due to stock reaching target profit at {2}'.format(
                                self.symbol, service.time_to_string(service.system_time), bar_close[0]))
                            self.IsPositionOn = False
                            self.IsPurchasable = False

        else:

            # close out of our long positions at the end of the day, I always use market for this, because it must fill.
            if self.IsPositionOn == True:
                sell_order_id = order.algo_sell(self.symbol, "market", intent="exit")
                self.IsPositionOn = False

    def on_start(self, md, order, service, account):

        self.model_start = service.system_time + service.time_interval(minutes=start_delay, seconds=1)
