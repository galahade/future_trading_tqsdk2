from tqsdk2 import Order

import dao.trade.trade_service as service
import strategies.tools as tools
import utils.tqsdk_tools as tq_tools
from strategies.trade_strategies.mts.main_trade_strategy import (
    MainTradeStrategy,
)
from strategies.trade_strategies.trade_strategies import LongTradeStrategy


class MainLongTradeStrategy(MainTradeStrategy, LongTradeStrategy):
    def _try_take_profit(self) -> None:
        logger = self.logger
        s = self.ts.symbol
        kline = self._get_last_kline_in_trade(self._d_klines)
        sc = self.ts.sold_condition
        log_str = "{} {} <做多> 止赢{} 现价:{} 手数:{} 剩余仓位:{} 止赢起始价:{}"
        sp_log = "止盈条件{}-售出{}"
        trade_time = tq_tools.get_date_str(kline.datetime)
        price = self._get_current_price()
        if self._get_profit_condition() in [1, 2, 3]:
            self._try_improve_stop_loss()
            if self._is_f5m_closeout():
                sold_pos = self._get_carry_pos()
                self.closeout(1, sp_log.format(sc.take_profit_cond, "100%"))
                content = log_str.format(
                    trade_time,
                    s,
                    sc.take_profit_cond,
                    price,
                    sold_pos,
                    0,
                    sc.tp_started_point,
                )
                logger.info(content)
        elif self._get_profit_condition() in [4]:
            if sc.take_profit_stage == 1:
                sc.take_profit_stage = 2
                carry_pos = self._get_carry_pos()
                sold_pos = carry_pos // 2 if carry_pos > 1 else carry_pos
                self.close_pos(
                    sold_pos, 1, sp_log.format(sc.take_profit_cond, "50%")
                )
                content = log_str.format(
                    trade_time,
                    s,
                    sc.take_profit_cond,
                    price,
                    sold_pos,
                    self._get_carry_pos(),
                    sc.tp_started_point,
                )
                logger.info(content)
            elif sc.take_profit_stage == 2:
                if price >= self._calc_price(
                    self.ts.open_pos_info.trade_price, 3.0, True
                ):
                    self.closeout(
                        1, sp_log.format(sc.take_profit_cond, "剩余全部")
                    )
                    content = log_str.format(
                        trade_time,
                        s,
                        sc.take_profit_cond,
                        price,
                        sc.tp_started_point,
                    )
                    logger.info(content)

    def _match_dk_condition(self, is_in=True) -> bool:
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._d_klines)
        (
            e9,
            e22,
            e60,
            macd,
            close,
            open_p,
            trade_time,
            k_date_str_short,
            _,
        ) = self._get_indicators(kline)
        log_str = (
            "{} {} <做多> 满足日线{} K线时间:{} ema9:{} ema22:{} "
            "ema60:{} 收盘:{} diff9_60:{} diffc_60:{} diff22_60:{} "
            "MACD:{}"
        )
        cond_number = 0
        if tools.has_set_k_attr(kline, "l_condition"):
            return kline.l_condition
        diff9_60 = tools.diff_two_value(e9, e60)
        diffc_60 = tools.diff_two_value(close, e60)
        diff22_60 = tools.diff_two_value(e22, e60)
        if e22 < e60:
            # 日线条件1
            if (
                (diff9_60 < 1 or diff22_60 < 1)
                and close > e60
                and macd > 0
                and (e9 > e22 or macd > 0)
            ):
                cond_number = 1
        elif e22 > e60:
            # 日线条件2
            if diff22_60 < 1 and close > e60:
                cond_number = 2
            # 日线条件3
            elif (
                1 < diff9_60 < 3
                and e9 > e22
                and e22 > min(open_p, close) > e60
            ):
                cond_number = 3
            # 日线条件4
            elif (
                1 < diff22_60 < 3
                and diff9_60 < 2
                and e22 > close > e60
                and e22 > e9 > e60
            ):
                cond_number = 4
            # 日线条件5
            elif (
                diff22_60 > 3
                and diffc_60 < 3
                and e22 > close > e60
                and e22 > open_p > e60
            ):
                cond_number = 5
        self._set_klines_value(
            self._d_klines, kline.name, "l_condition", cond_number
        )
        if cond_number > 0:
            content = log_str.format(
                trade_time,
                self.ts.symbol,
                cond_number,
                k_date_str_short,
                e9,
                e22,
                e60,
                close,
                diff9_60,
                diffc_60,
                diff22_60,
                macd,
            )
            logger.info(content)
            self._set_open_condition(
                kline, cond_number, self.ts.open_condition.daily_condition
            )  # type: ignore
            self.ts.open_condition.daily_condition.condition_id = cond_number  # type: ignore
        return self._d_klines.loc[kline.name].l_condition  # type: ignore

    def _match_3h_condition(self, is_in=True) -> bool:
        """做多3小时线检测"""
        logger = self.logger
        dkline = self._get_last_kline_in_trade(self._d_klines)
        kline = self._get_last_kline_in_trade(self._3h_klines)
        if tools.has_set_k_attr(kline, "l_condition"):
            return kline.l_condition
        (
            e9,
            e22,
            e60,
            macd,
            close,
            open_p,
            trade_time,
            _,
            k_date_str,
        ) = self._get_indicators(kline)
        diffc_60 = tools.diff_two_value(close, e60)
        diffo_60 = tools.diff_two_value(open_p, e60)
        diff22_60 = tools.diff_two_value(e22, e60)
        diff9_60 = tools.diff_two_value(e9, e60)
        log_str = (
            "{} {} <做多> 满足3小时{} K线时间:{} "
            "ema9:{} ema22:{} ema60:{} 收盘:{} 开盘:{} "
            "diffc_60:{} diffo_60:{} diff22_60:{} MACD:{}"
        )
        cond_number = 0
        if diffc_60 < 3 or diffo_60 < 3:
            if dkline.l_condition in [1, 2]:
                if (
                    e22 < e60
                    and e9 < e60
                    and (
                        diff22_60 < 1
                        or (1 < diff22_60 < 2 and (macd > 0 or close > e60))
                    )
                ):
                    cond_number = 1
                elif close > e9 > e22 > e60:
                    if self._match_3hk_c2_distance():
                        cond_number = 2
                    elif diff9_60 < 1 and diff22_60 < 1 and macd > 0:
                        cond_number = 5
            elif dkline.l_condition in [3, 4]:
                if (
                    close > e60 > e22
                    and macd > 0
                    and diff22_60 < 1
                    and e9 < e60
                ):
                    cond_number = 3
                elif (
                    dkline.l_condition == 3 and diff9_60 < 1 and diff22_60 < 1
                ):
                    cond_number = 6
            elif dkline.l_condition == 5 and (e60 > e22 > e9):
                cond_number = 4
        self._set_klines_value(
            self._3h_klines, kline.name, "l_condition", cond_number
        )
        if cond_number > 0:
            content = log_str.format(
                trade_time,
                self.ts.symbol,
                cond_number,
                k_date_str,
                e9,
                e22,
                e60,
                close,
                open_p,
                diffc_60,
                diffo_60,
                diff22_60,
                macd,
            )
            logger.info(content)
            self._set_open_condition(
                kline, cond_number, self.ts.open_condition.hourly_condition
            )  # type: ignore
        return self._3h_klines.loc[kline.name].l_condition  # type: ignore

    def _match_30m_condition(self, is_in=True) -> bool:
        """做多30分钟线检测"""
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._30m_klines)
        if tools.has_set_k_attr(kline, "l_condition"):
            return kline.l_condition
        (
            e9,
            e22,
            e60,
            macd,
            close,
            _,
            trade_time,
            _,
            k_date_str,
        ) = self._get_indicators(kline)
        diffc_60 = tools.diff_two_value(close, e60)
        log_str = (
            "{} {} <做多> 满足30分钟条件 K线时间:{} ema9:{} ema22:{} "
            "ema60:{} 收盘:{} diffc_60:{} MACD:{}"
        )
        if close > e60 and macd > 0 and diffc_60 < 1.2:
            self._set_klines_value(
                self._30m_klines, kline.name, "l_condition", 1
            )
            content = log_str.format(
                trade_time,
                self.ts.symbol,
                k_date_str,
                e9,
                e22,
                e60,
                close,
                diffc_60,
                macd,
            )
            logger.info(content)
            self._set_open_condition(
                kline, 1, self.ts.open_condition.minute_30_condition
            )  # type: ignore
        else:
            self._set_klines_value(
                self._30m_klines, kline.name, "l_condition", 0
            )
        return self._30m_klines.loc[kline.name].l_condition  # type: ignore

    def _match_5m_condition(self, is_in=True) -> bool:
        """做多5分钟线检测"""
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._5m_klines)
        if tools.has_set_k_attr(kline, "l_condition"):
            return kline.l_condition
        (
            e9,
            e22,
            e60,
            macd,
            close,
            _,
            trade_time,
            _,
            k_date_str,
        ) = self._get_indicators(kline)
        diffc_60 = tools.diff_two_value(close, e60)
        log_str = (
            "{} {} <做多> 满足5分钟条件 K线时间:{} "
            "ema9:{} ema22:{} ema60:{} 收盘:{} diffc_60:{} MACD:{}"
        )
        if close > e60 and macd > 0 and diffc_60 < 1.2:
            self._set_klines_value(
                self._5m_klines, kline.name, "l_condition", 1
            )
            content = log_str.format(
                trade_time,
                self.ts.symbol,
                k_date_str,
                e9,
                e22,
                e60,
                close,
                diffc_60,
                macd,
            )
            logger.info(content)
            self._set_open_condition(
                kline, 1, self.ts.open_condition.minute_5_condition
            )  # type: ignore
            return True
        else:
            self._set_klines_value(
                self._5m_klines, kline.name, "l_condition", 0
            )
        return self._5m_klines.loc[kline.name, "l_condition"]  # type: ignore

    def _has_match_stop_loss(self) -> bool:
        price = self._get_current_price()
        if self.is_trading() == 1:
            sc = self.ts.sold_condition
            if price <= sc.stop_loss_price:
                return True
        return False

    def _set_sold_condition(self):
        super()._set_sold_condition()
        s_c = self.ts.sold_condition
        d_c_id = self.ts.open_condition.daily_condition.condition_id  # type: ignore
        h_c_id = self.ts.open_condition.hourly_condition.condition_id  # type: ignore
        if d_c_id in [1, 2]:
            s_c.take_profit_cond = 1
        elif d_c_id == 5:
            s_c.take_profit_cond = 2
        elif d_c_id == 3 and h_c_id == 6:
            s_c.take_profit_cond = 3
        elif d_c_id in [3, 4] and h_c_id == 3:
            s_c.take_profit_cond = 4

    def _set_sold_prices(self, order: Order):
        s_c = self.ts.sold_condition
        s_c.stop_loss_price = self._calc_price(
            order.trade_price,
            self.config.f_info.long_config.stop_loss_scale,
            False,
        )
        if s_c.take_profit_cond in [1, 2, 3]:
            s_c.tp_started_point = self._calc_price(
                order.trade_price,
                self.config.f_info.long_config.profit_start_scale_1,
                True,
            )
        elif s_c.take_profit_cond == 4:
            s_c.tp_started_point = self._calc_price(
                order.trade_price,
                self.config.f_info.long_config.profit_start_scale_2,
                True,
            )
        self.logger.info(
            f"{self._get_trade_date_str()} {self.symbol} "
            f"<做多>开仓价:{order.trade_price}"
            f"止损设为:{s_c.stop_loss_price}"
            f"止盈起始价为:{s_c.tp_started_point}"
        )

    def _try_improve_stop_loss(self) -> None:
        logger = self.logger
        price = self._get_current_price()
        trade_price = self.ts.open_pos_info.trade_price
        trade_config = self.config.f_info.long_config
        sc = self.ts.sold_condition
        trade_time = tq_tools.get_date_str(self._get_trade_date())
        log_str = "{} {} <做多> 现价{} 达到1:{} 盈亏比,将止损价提高至{}"
        promote_price = self._calc_price(
            trade_price, trade_config.promote_scale_1, True
        )
        if sc.has_increase_slp:
            return
        if sc.take_profit_stage in [1, 2, 3] and price >= promote_price:
            sc.stop_loss_price = self._calc_price(
                trade_price, trade_config.promote_target_1, True
            )
            sc.sl_reason = "跟踪止盈"
            sc.has_increase_slp = True
            service.update_trade_status(self.ts, self._get_trade_date())
            logger.debug(
                log_str.format(
                    trade_time,
                    self.symbol,
                    price,
                    trade_config.promote_scale_1,
                    sc.stop_loss_price,
                )
            )

    def _is_f5m_closeout(self) -> bool:
        logger = self.logger
        kline = self._get_last_kline_in_trade(self._d_klines)
        log_str = (
            "{} {} <做多> 满足最后5分钟止盈 止盈条件:{} 当前价:{} "
            "日线EMA9:{} 日线EMA22:{} EMA60:{}"
        )
        e9, e22, e60, _, _, _, trade_time, _, _ = self._get_indicators(kline)
        price = self._get_current_price()
        trade_time = tq_tools.get_date_str(trade_time)
        sc = self.ts.sold_condition
        if self._is_last_5m():
            if sc.take_profit_cond == 1 and price < e60 and e9 < e22:
                logger.debug(
                    log_str.format(
                        trade_time, self.symbol, 1, price, e9, e22, e60
                    )
                )
                return True
            elif sc.take_profit_cond in [2, 3] and price < e22 and e9 < e22:
                logger.debug(
                    log_str.format(
                        trade_time, self.symbol, 2, price, e9, e22, e60
                    )
                )
                return True
        return False

    def _get_profit_condition(self) -> int:
        """返回满足止盈条件的序号，并设置相关止盈参数

        0:不满足止盈条件
        1:止盈条件1
        2:止盈条件2
        3:止盈条件3
        4:止盈条件4
        """
        logger = self.logger
        if self.is_trading():
            log_str = "{} {} <做多> 现价:{} 达到止盈价{} 开始监控 " "止损价提高到:{}"
            price = self._get_current_price()
            sc = self.ts.sold_condition
            if sc.has_enter_tp:
                return sc.take_profit_cond
            if price >= sc.tp_started_point:
                sc.has_enter_tp = True
                if sc.take_profit_cond == 4:
                    sc.stop_loss_price = self.ts.open_pos_info.trade_price
                    sc.take_profit_stage = 1
                service.update_trade_status(self.ts, self._get_trade_date())
                logger.info(
                    log_str.format(
                        tq_tools.get_date_str(self._get_trade_date()),
                        self.symbol,
                        price,
                        sc.tp_started_point,
                        sc.stop_loss_price,
                    )
                )
                return sc.take_profit_cond
        return 0
