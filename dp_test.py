# from datetime import date
from tqsdk import TqApi, TqAuth,  BacktestFinished, tafunc

api = TqApi(auth=TqAuth("galahade", "211212"))
quote = api.get_quote("KQ.m@DCE.jd")
# quote = api.get_quote("SHFE.rb2309")
# klines = api.get_kline_serial("SHFE.rb2309", 60)
# kline = klines.iloc[-1]
# print(klines)
# klines.loc[kline.name, "s_matched"] = True
# print(klines.loc[klines['datetime'] < kline.datetime])
# print(klines[klines.datetime < kline.datetime].iloc[::-1])
print(len(quote.trading_time.night))
api.close()
