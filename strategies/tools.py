from datetime import datetime
import numpy as np
from pandas import Series
from tqsdk2.ta import EMA, MACD
from tqsdk2 import tafunc
from utils.common_tools import sendPushDeerMsg
from utils import global_var as gvar


def sendTradePosMsg(
    custom_symbol: str,
    symbol: str,
    direction: bool,
    pos: int,
    price: float,
    t_time: str,
):
    if direction:
        dir_str = "买入"
    else:
        dir_str = "卖出"
    title = f"## {gvar.ENV_NAME}环境 {custom_symbol} {dir_str}"
    content = f"{t_time} **{symbol}** {dir_str} **{pos}** 手，价格 **¥{price}**"
    sendPushDeerMsg(title, content)


def fill_macd(klines):
    macd = MACD(klines, 12, 24, 4).round({"bar": 3})
    # 用 K 线图模拟 MACD 指标柱状图
    klines["MACD.open"] = 0.0
    klines["MACD.close"] = macd["bar"]
    klines["MACD.high"] = klines["MACD.close"].where(
        klines["MACD.close"] > 0, 0
    )
    klines["MACD.low"] = klines["MACD.close"].where(
        klines["MACD.close"] < 0, 0
    )
    klines["diff"] = macd["diff"]
    klines["dea"] = macd["dea"]


def fill_bottom_indicators(klines):
    """为K线填充摸底策略指标"""
    fill_macd(klines)
    fill_ema5(klines)
    fill_ema20(klines)
    fill_ema60(klines)
    # _draw_main_lines(klines)


def fill_main_indicators(klines):
    fill_macd(klines)
    fill_ema9(klines)
    fill_ema22(klines)
    fill_ema60(klines)

    # _draw_main_lines(klines)


def _draw_bottom_lines(klines):
    """当需要视觉效果时使用该方法将指标绘制到K线图上"""
    klines["ema20.board"] = "MAIN"
    klines["ema20.color"] = "red"
    klines["ema60.board"] = "MAIN"
    klines["ema60.color"] = "green"
    klines["ema5.board"] = "MAIN"
    klines["ema5.color"] = "blue"
    _draw_macd_line(klines)


def _draw_main_lines(klines):
    """当需要视觉效果时使用该方法将指标绘制到K线图上"""
    klines["ema22.board"] = "MAIN"
    klines["ema22.color"] = "red"
    klines["ema60.board"] = "MAIN"
    klines["ema60.color"] = "green"
    klines["ema9.board"] = "MAIN"
    klines["ema9.color"] = "blue"
    _draw_macd_line(klines)


def _draw_macd_line(klines):
    klines["MACD.board"] = "MACD"
    # 在 board=MACD 上添加 diff、dea 线
    klines["diff.board"] = "MACD"
    klines["diff.color"] = "gray"
    klines["dea.board"] = "MACD"
    klines["dea.color"] = "rgb(255,128,0)"


def fill_ema5(klines):
    ema = EMA(klines, 5).round(3)
    klines["ema5"] = ema.ema


def fill_ema9(klines):
    ema = EMA(klines, 9).round(3)
    klines["ema9"] = ema.ema


def fill_ema20(klines):
    ema = EMA(klines, 20).round(3)
    klines["ema20"] = ema.ema


def fill_ema22(klines):
    ema22 = EMA(klines, 22).round(3)
    klines["ema22"] = ema22.ema


def fill_ema60(klines):
    ema = EMA(klines, 60).round(3)
    klines["ema60"] = ema.ema


def is_nline(kline) -> bool:
    """判断K线是否是阴线"""
    if kline.open > kline.close:
        return True
    return False


def is_decline_2p(kline, l_kline) -> bool:
    # logger = get_logger()
    # log_str = ('当前K线生成时间{},上一根K线生成时间{},'
    #            '当前K线收盘价{},上一根K线收盘价{}, 跌幅{}')

    result = (l_kline.close - kline.close) / l_kline.close
    # logger.debug(log_str.format(
    #     get_date(kline.datetime),
    #     get_date(l_kline.datetime),
    #     kline.close, l_kline.close, result))
    if result > 0.02:
        return True
    return False


def is_trading_time(api, symbol):
    """判断是否在交易时间内的方法，如果购买专业版，可以使用天勤提供的方法判断
    否则，使用简单的时间段进行判断
    """
    result = False
    ts = api.get_trading_status(symbol)
    if ts.trade_status == "CONTINOUS":
        result = True
    return result


def is_after_execute_time(api, symbol):
    """判断是否在交易时间内的方法，如果购买专业版，可以使用天勤提供的方法判断
    否则，使用简单的时间段进行判断
    """
    result = False
    now = datetime.now()
    dkline = api.get_kline_serial(symbol, 60 * 60 * 24, 1).iloc[0]
    k_dt = tafunc.time_to_datetime(dkline.datetime)
    if now.hour >= 16 and now.hour < 21 and now.day == k_dt.day:
        result = True
    return result


def get_52060_values(kline) -> tuple:
    ema5 = kline.ema5
    ema20 = kline.ema20
    ema60 = kline.ema60
    macd = kline["MACD.close"]
    close = kline.close
    open_p = kline.open
    kline_time = tafunc.time_to_datetime(kline.datetime)
    return (ema5, ema20, ema60, macd, close, open_p, kline_time)


def has_set_k_attr(kline: Series, attr_value: str) -> bool:
    """判断K线是否设置了attr_value属性值，如果设置了，返回True，否则返回False"""
    return kline.get(attr_value) is not None and not (
        np.isnan(kline.get(attr_value))
    )  # type: ignore


def diff_two_value(first: float, second: float) -> float:
    """计算两个值的差值，返回差值的绝对值"""
    return round(abs(first - second) / second * 100, 3)
