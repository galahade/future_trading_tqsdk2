# from datetime import date
# from tqsdk2 import TqApi, TqAuth

# quote = api.get_quote("SHFE.rb2309")
# klines = api.get_kline_serial("SHFE.rb2309", 60)
# kline = klines.iloc[-1]
# print(klines)
# klines.loc[kline.name, "s_matched"] = True
# print(klines.loc[klines['datetime'] < kline.datetime])
# print(klines[klines.datetime < kline.datetime].iloc[::-1])
# print(len(quote.trading_time.night))
# api.close()
