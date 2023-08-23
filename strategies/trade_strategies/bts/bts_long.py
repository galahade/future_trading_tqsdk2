from typing import Tuple
from tqsdk.objs import Order
from dao.odm.future_trade import BottomOpenCondition, BottomOpenVolumeTip
import strategies.tools as tools
from strategies.trade_strategies.bts.bottom_trade_strategy import BottomTradeStrategy
from strategies.trade_strategies.trade_strategies import (
    LongTradeStrategy
)


class BottomLongTradeStrategy(BottomTradeStrategy, LongTradeStrategy):
    '''摸底做多交易策略'''

    def _has_traded(self) -> bool:
        '''交易时段是否已经根据盘前提示判断过是否开仓'''
        kline = self._get_last_dkline()
        if tools.has_set_k_attr(kline, 'l_traded'):
            return True
        self._set_klines_value(self._d_klines, kline.name, 'l_traded', True)
        return False

    def _is_dk_macd_matched(self, is_in=True) -> bool:
        kline = self._get_last_dkline(is_in)
        if tools.has_set_k_attr(kline, 'l_macd_matched'):
            return bool(kline.l_matched)
        return False

    def _match_dk_condition(self, is_in=True) -> bool:
        logger = self.logger
        kline = self._get_last_dkline(is_in)
        if tools.has_set_k_attr(kline, 'l_matched'):
            return kline.l_matched
        s = self.ts.symbol
        e5, e20, e60, macd, close, trade_time, k_date_str_short, _ =\
            self._get_indicators(kline)
        log_str = ('{} {} <摸底做多> 满足日线 K线时间:{} ema5:{} ema20:{} '
                   'ema60:{} 收盘:{} MACD:{}')
        if e5 < e20 < e60 and close > e5:
            if macd > 0:
                self._set_klines_value(
                    self._d_klines, kline.name, 'l_macd_matched', True)
            else:
                self._set_klines_value(
                    self._d_klines, kline.name, 'l_macd_matched', False)
            content = log_str.format(
                trade_time, s, k_date_str_short, e5, e20, e60, close, macd)
            logger.info(content)
            self._set_klines_value(
                self._d_klines, kline.name, 'l_matched', True)
            if self.ts.open_condition is None:
                self.ts.open_condition = BottomOpenCondition()
            self._set_open_condition(
                kline, self.ts.open_condition.daily_condition  # type: ignore
            )
        else:
            self._set_klines_value(
                self._d_klines, kline.name, 'l_matched', False)
        return self._d_klines.loc[kline.name, 'l_matched']  # type: ignore

    def _match_3h_condition(self, is_in=True) -> bool:
        logger = self.logger
        kline = self._get_lastd_last_3h_kline(is_in)
        if tools.has_set_k_attr(kline, 'l_matched'):
            return kline.l_matched
        _, _, _, macd, _, trade_time, _, k_date_str =\
            self._get_indicators(kline)
        log_str = '{} {} <摸底做多> 满足3小时 K线时间:{} MACD:{}'
        if macd > 0:
            content = log_str.format(
                trade_time, self.ts.symbol, k_date_str, macd)
            logger.info(content)
            self._set_klines_value(
                self._3h_klines, kline.name, 'l_matched', True)
            self._set_open_condition(
                kline, self.ts.open_condition.hourly_condition)  # type: ignore
        else:
            self._set_klines_value(
                self._3h_klines, kline.name, 'l_matched', False)
        return self._3h_klines.loc[kline.name, 'l_matched']  # type: ignore

    def _match_30m_condition(self, is_in=True) -> bool:
        logger = self.logger
        kline = self._get_lastd_last_30m_kline(is_in)
        if tools.has_set_k_attr(kline, 'l_matched'):
            return kline.l_matched
        e5, e20, e60, macd, close, trade_time, k_date_str_short, _ =\
            self._get_indicators(kline)
        log_str = ('{} {} <摸底做多> 满足30分钟条件 K线时间:{} ema5:{} ema20:{} '
                   'ema60:{} 收盘:{} MACD:{}')
        if close > e60 and e5 > e60:
            if self._is_within_distance(kline, self._is_dk_macd_matched(is_in)):
                self._set_klines_value(
                    self._30m_klines, kline.name, 'l_matched', True)
                content = log_str.format(
                    trade_time, self.ts.symbol, k_date_str_short, e5, e20, e60,
                    close, macd)
                logger.info(content)
                self._set_open_condition(
                    kline, self.ts.open_condition.minute_30_condition)  # type: ignore
            else:
                self._set_klines_value(
                    self._30m_klines, kline.name, 'l_matched', False)
        else:
            self._set_klines_value(
                self._30m_klines, kline.name, 'l_matched', False)
        return self._30m_klines.loc[kline.name, 'l_matched']  # type: ignore

    def _set_sold_prices(self, order: Order):
        s_c = self.ts.sold_condition
        s_c.stop_loss_price = self._calc_price(
            order.trade_price, self.config.f_info.short_config.stop_loss_scale,
            False)
        s_c.tp_started_point = self._calc_price(
            order.trade_price,
            self.config.f_info.short_config.profit_start_scale,
            True)
        self.logger.info(f'{self._get_trade_date_str()} {self.symbol} '
                         f'<做空>开仓价:{order.trade_price}'
                         f'止损设为:{s_c.stop_loss_price}'
                         f'止盈起始价为:{s_c.tp_started_point}')
