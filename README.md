# ordering_method_demo

Demonstrates different ways to place stock orders in CloudQuant

This repository demonstrates different ways to determine the volumes of shares that are purchased.

Trade volume refers to the number of shares to purchase, and thus the total dollar amount for each purchase. 

One common way to determine volume is simply to purchase a fixed number of shares: num_shares=100 This way is great for its simplicity, but it's really not recommended because high-priced stocks will represent a much larger percentage of your gains and losses than lower priced stocks.

Another way is to base the volume purchased on some fraction of the volume of ask price in the previous minute. For example: num_shares=int(bar_askvol[0]*.1) This is useful if you want to order a large number of shares quickly without ordering so many that you actually change the price of the shares. Be careful, though. The dollar value of the trade can be wildly different with this strategy, anywhere from less than $1000 to over $500000. Again, your algorithm will be dominated by high-price and high-volume shares.

Finally, the commonly recommended way, is with a dollar amount: num_shares=np.round(purchase_amount/md[self.symbol].L1.last) where "purchase_amount" is the dollar value of a stock you want to purchase. Usually between $10000 and $25000 is a good amount, and you won't disrupt anything on the Russell 2000 with those numbers. This will keep your total amount of money invested in different stocks consistent regardless of their share price.

Check the demo scripts for examples of implementation.
