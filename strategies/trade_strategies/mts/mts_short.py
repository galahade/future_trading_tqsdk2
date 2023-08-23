from abc import abstractmethod
from tqsdk.objs import Order
import dao.trade.trade_service as service
from strategies.trade_strategies.mts.main_trade_strategy import MainTradeStrategy
from strategies.trade_strategies.trade_strategies import (ShortTradeStrategy)
import strategies.tools as tools
import utils.tqsdk_tools as tq_tools


class MainShortTradeStrategy(MainTradeStrategy, ShortTradeStrategy):

    def _try_take_profit(self) -> None:
        logger = self.logger
        symbol = self.ts.symbol
        kline = self._get_last_kline_in_trade(self._d_klines)
        dks = []
        (e9, e22, e60, macd, close, _,
         trade_time, _, _) = self._get_indicators(kline)
        diff22_60 = tools.diff_two_value(e22, e60)
        log_str = ('{} {} <做空> 全部止赢 现价:{} 手数:{} diff22_60:{} '
                   'close:{} macd:{} 之前符合条件K线日期{} macd{} '
                   'close:{} open:{}')
        self._try_improve_stop_loss()
        if self._get_profit_condition(kline):
            price = self._get_current_price()
            if close > e9 and macd > 0:
                dks.append(self._d_klines.iloc[-3])
                dks.append(self._d_klines.iloc[-4])
                for t_dk in dks:
                    t_macd = t_dk['MACD.close']
                    if not tools.is_nline(t_dk) and t_macd > 0:
                        order = self.closeout(1, '趋势止盈')
                        content = log_str.format(
                            trade_time, symbol, price, order.volume_orign,
                            diff22_60, close, macd,
                            tq_tools.get_date_str_short(t_dk.datetime),
                            t_macd, t_dk.close, t_dk.open
                        )
                        logger.debug(content)
                        return
                self.ts.sold_condition.has_stop_tp = True
                service.update_trade_status(self.ts, trade_time)  # type: ignore

    def _match_dk_condition(self, is_in=True) -> bool:
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._d_klines)
        if tools.has_set_k_attr(kline, 's_condition'):
            return kline.s_condition
        s = self.ts.symbol
        (e9, e22, e60, macd, close, _, trade_time,
            k_date_str_short, _) = self._get_indicators(kline)
        log_str = ('{} {} <做空> 满足日线 K线时间:{} ema9:{} ema22:{} '
                   'ema60:{} 收盘:{} MACD:{}')
        content = log_str.format(
            trade_time, s, k_date_str_short,
            e9, e22, e60, close, macd)
        # 日线条件
        if e22 > e60 and macd < 0 and e22 > close:
            # logger.debug(f'kline column:{kline}')
            is_matched = not self._no_matched_open_cond()
            if is_matched:
                self._set_klines_value(
                    self._d_klines, kline.name, 's_condition', 1)
                logger.info(content)
                self._set_open_condition(
                    kline, 1, self.ts.open_condition.daily_condition)  # type: ignore
            else:
                self._set_klines_value(
                    self._d_klines, kline.name, 's_condition', 0)
        else:
            self._set_klines_value(
                self._d_klines, kline.name, 's_condition', 0)
        return self._d_klines.loc[kline.name, 's_condition']  # type: ignore

    def _no_matched_open_cond(self) -> bool:
        # logger = self.logger
        # t_time = self._ts.get_current_date_str()
        # log_str = ('{} Last is N:{},Last2 is N:{},'
        #            'Last decline more then 2%:{},'
        #            'Last2 decline more than 2%:{}')
        # log_str2 = ('{} diff9_60:{},ema9:{},ema60:{},close:{}')
        l_kline = self._get_last_kline_in_trade(self._d_klines)
        # l2_kline = self._daily_klines.iloc[-3]
        # l3_kline = self._daily_klines.iloc[-4]
        e9, e22, e60, _, close, _, _, _, _ = self._get_indicators(l_kline)
        diff9_60 = tools.diff_two_value(e9, e60)
        diff22_60 = tools.diff_two_value(e22, e60)
        if diff9_60 < 2 or diff22_60 < 2:
            if e60 < close:
                # logger.debug(log_str2.format(
                #     t_time, diff9_60, e9, e60, close))
                return True
        # if diff9_60 < 3:
        #     l_n = is_nline(l_kline)
        #     l2_n = is_nline(l2_kline)
        #     l_d2 = is_decline_2p(l_kline, l2_kline)
        #     l2_d2 = is_decline_2p(l2_kline, l3_kline)
        #     if (l_n and l2_n) or (l_d2 or l2_d2):
        #         logger.debug(log_str.format(t_time, l_n, l2_n, l_d2, l2_d2))
        #         return True
        return False

    def _match_3h_condition(self, is_in=True) -> bool:
        '''做空3小时线检测
        '''
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._3h_klines)
        if tools.has_set_k_attr(kline, 's_condition'):
            return kline.s_condition
        e9, e22, e60, macd, close, open_p, trade_time, _, k_date_str =\
            self._get_indicators(kline)
        diffc_60 = tools.diff_two_value(close, e60)
        diff9_60 = tools.diff_two_value(e9, e60)
        diff22_60 = tools.diff_two_value(e22, e60)
        log_str = ('{} {} <做空> 满足3小时 K线时间:{} '
                   'ema9:{} ema22:{} ema60:{} 收盘:{} 开盘:{}'
                   'diffc_60:{} diff9_60:{} diff22_60{} MACD:{}')
        if (e22 > e60 and
            (e22 > e9 or (e22 < e9 and close < e60 and open_p > e60)) and
           diff9_60 < 3 and diff22_60 < 3 and diffc_60 < 3 and macd < 0):
            self._set_klines_value(
                self._3h_klines, kline.name, 's_condition', 1)
            content = log_str.format(
                trade_time, self.ts.symbol, k_date_str, e9, e22,
                e60, close, open_p, diffc_60, diff9_60, diff22_60, macd)
            logger.info(content)
            self._set_open_condition(
                kline, 1, self.ts.open_condition.hourly_condition)  # type: ignore
        else:
            self._set_klines_value(
                self._3h_klines, kline.name, 's_condition', 0)
        return self._3h_klines.loc[kline.name, 's_condition']  # type: ignore

    def _match_30m_condition(self, is_in=True) -> bool:
        '''做空30分钟线检测
        '''
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._30m_klines)
        if tools.has_set_k_attr(kline, 's_condition'):
            return kline.s_condition
        e9, e22, e60, macd, close, _, trade_time, _, k_date_str =\
            self._get_indicators(kline)
        diff22_60 = tools.diff_two_value(e22, e60)
        diff9_60 = tools.diff_two_value(e9, e60)
        log_str = ('{} {} <做空> 满足30分钟 K线时间:{} ema9:{} '
                   'ema22:{} ema60:{} 收盘:{} diff22_60:{} deff9_60:{} MACD:{}')
        if ((e60 > e22 > e9 or e22 > e60 > e9) and diff9_60 < 2
           and diff22_60 < 1 and macd < 0 and e60 > close
           and self.is_within_2days()):
            self._set_klines_value(
                self._30m_klines, kline.name, 's_condition', 1)
            content = log_str.format(
                trade_time, self.ts.symbol, k_date_str,
                e9, e22, e60, close, diff22_60, diff9_60, macd)
            logger.info(content)
            self._set_open_condition(
                kline, 1, self.ts.open_condition.minute_30_condition  # type: ignore
            )
        else:
            self._set_klines_value(
                self._30m_klines, kline.name, 's_condition', 0)
        return self._30m_klines.loc[kline.name, 's_condition']  # type: ignore

    def _match_5m_condition(self, is_in=True) -> bool:
        return True

    def _has_match_stop_loss(self) -> bool:
        matched = False
        price = self._get_current_price()
        if self.ts.trade_status == 1:
            sold_cond = self.ts.sold_condition
            if price >= sold_cond.stop_loss_price:
                matched = True
        return matched

    def _set_sold_prices(self, order: Order):
        s_c = self.ts.sold_condition
        s_c.stop_loss_price = self._calc_price(
            order.trade_price, self.config.f_info.short_config.stop_loss_scale,  # type: ignore
            True)
        s_c.tp_started_point = self._calc_price(
            order.trade_price,
            self.config.f_info.short_config.profit_start_scale,  # type: ignore
            False)
        self.logger.info(f'{self._get_trade_date_str()} {self.symbol}'
                         f'<做空>开仓价:{order.trade_price}'
                         f'止损设为:{s_c.stop_loss_price}'
                         f'止盈起始价为:{s_c.tp_started_point}')

    def _try_improve_stop_loss(self) -> None:
        logger = self.logger
        price = self._get_current_price()
        trade_price = self.ts.open_pos_info.trade_price
        trade_config = self.config.f_info.short_config
        sc = self.ts.sold_condition
        trade_time = tq_tools.get_date_str(self._get_trade_date())
        log_str = '{} {} <做空> 现价{} 达到1:{} 盈亏比,将止损价提高至{}'
        promote_price = self._calc_price(
            trade_price, trade_config.promote_scale, False)
        if sc.has_increase_slp:
            return
        if (sc.take_profit_stage == 0 and price <= promote_price):
            sc.stop_loss_price = self._calc_price(
                trade_price, trade_config.promote_target, False)
            sc.take_profit_stage = 1
            sc.sl_reason = '跟踪止盈'
            sc.has_increase_slp = True
            service.update_trade_status(self.ts, self._get_trade_date())
            logger.debug(log_str.format(
                trade_time, self.symbol, price,
                trade_config.promote_scale, sc.stop_loss_price))

    def _is_f5m_closeout(self) -> bool:
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._d_klines)
        log_str = ('{} {} <做空> 满足最后5分钟止盈,当前价:{} '
                   '日线EMA9:{} 日线EMA22:{} MACD:{}')
        e9, e22, _, macd, _, _, trade_time, _, _ =\
            self._get_indicators(kline)
        price = self._get_current_price()
        trade_time = tq_tools.get_date_str(trade_time)
        if self._is_last_5m():
            if (macd > 0 and price > e9):
                logger.debug(log_str.format(
                    trade_time, self.symbol, price, e9, e22, macd))
                return True
        return False

    def _get_profit_condition(self, dk) -> bool:
        '''返回是否满足止盈条件，并设置相关止盈参数'''
        if self.is_trading():
            e9, e22, e60, _, close, _, _, _, _ =\
                self._get_indicators(dk)
            sc = self.ts.sold_condition
            if (e60 > e22 > e9 and not sc.has_stop_tp):
                return True
            elif sc.has_stop_tp:
                if close < e9:
                    sc.has_stop_tp = False
                    service.update_trade_status(
                        self.ts, self._get_trade_date())
        return False
