# Arbitrage trade on Milkomeda

This project builds on techniques used in SimpleTrader and FindTrades.  
The project consists of a smart contract deployed on Milkomeda that is used to execute an arbitrage trade within specific requirements based on a scan of the blockchain controlled by functions in a python script.

The code has yet to make a profit but it has also not made a loss; not accounting for the marginal cost (0.02431541 milkADA) for gas used prior to transaction reversion. It has found viable trades and attempted execution but somewhere between identification and execution, the value of the trade drops below the threshold defined by the python script so the transactions were reverted.

This is most probably due to small caps in the trade pools that could result in larger than tolerated slippage.  
On further testing, limited to pool caps greater than A100,000, no trades have been found.  
This is likely because Milkomeda has a low Total Value Locked (TVL) and therefore mostly small cap pools.  
However, it is also likely that strategy improvments may yield better results.
