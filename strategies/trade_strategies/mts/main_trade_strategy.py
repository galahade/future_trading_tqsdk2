from abc import abstractmethod
from datetime import datetime, timedelta
from tqsdk2 import tafunc
from tqsdk2 import Order
from dao.odm.future_trade import MainIndicatorValues, MainTradeStatus
import dao.trade.trade_service as service
from strategies.trade_strategies.trade_strategies import TradeStrategy
from utils.common_tools import LoggerGetter
import strategies.tools as tools
import utils.tqsdk_tools as tq_tools


class MainTradeStrategy(TradeStrategy):
    logger = LoggerGetter()

    def fill_indicators_by_type(self, k_type: int):
        """根据K线类型填充指标 1:全部K线 2:日线 3:3小时线 4:30分钟线 5:5分钟线"""
        if k_type == 1:
            self.fill_indicators_by_type(2)
            self.fill_indicators_by_type(3)
            self.fill_indicators_by_type(4)
            self.fill_indicators_by_type(5)
        elif k_type == 2:
            tools.fill_main_indicators(self._d_klines)
        elif k_type == 3:
            tools.fill_main_indicators(self._3h_klines)
        elif k_type == 4:
            tools.fill_main_indicators(self._30m_klines)
        elif k_type == 5:
            tools.fill_main_indicators(self._5m_klines)

    def _can_open_pos(self) -> bool:
        """判断是否可以开仓"""
        logger = self.logger
        if not self.is_trading():
            if self._match_dk_condition():
                if self._match_3h_condition():
                    if self._match_30m_condition():
                        if self._match_5m_condition():
                            logger.info("<主策略>符合开仓条件, 请注意开仓提示".ljust(100, "-"))
                            return True
        return False

    def _try_stop_loss(self):
        """当满足止损条件时，进行止损操作"""
        logger = self.logger
        trade_date_str = self._get_trade_date_str()
        price = self._get_current_price()
        log_str = "{} {} {} {} 现价:{} 止损价:{} 手数:{}"
        if self._has_match_stop_loss():
            pos = self._get_carry_pos()
            content = log_str.format(
                trade_date_str,
                self.ts.symbol,
                self.ts.custom_symbol,
                self.ts.sold_condition.sl_reason,
                price,
                self.ts.sold_condition.stop_loss_price,
                pos,
            )
            logger.info(content)
            self.closeout(0, self.ts.sold_condition.sl_reason)

    def _get_trade_status(self, symbol: str) -> MainTradeStatus:
        """获取交易状态"""
        return service.get_main_trade_status(
            self.config.custom_symbol,
            symbol,
            self._get_direction(),
            self.config.quote.datetime,
        )

    def _get_last_kline_in_trade(self, klines):
        return klines.iloc[-2]

    def _get_indicators(self, kline) -> tuple:
        """获取常用指标"""
        ema9 = kline.ema9
        ema22 = kline.ema22
        ema60 = kline.ema60
        macd = kline["MACD.close"]
        close = kline.close
        open_price = kline.open
        trade_time = self._get_trade_date()
        kline_time_str_short = tq_tools.get_date_str_short(kline.datetime)
        kline_time_str = tq_tools.get_date_str(kline.datetime)
        return (
            ema9,
            ema22,
            ema60,
            macd,
            close,
            open_price,
            trade_time,
            kline_time_str_short,
            kline_time_str,
        )

    def is_within_2days(self) -> bool:
        """判断30分钟线上一次满足条件时是否在规定时间之内

        上一次满足的条件为：30分钟收盘价 < EMA60 < EAM22
        """
        logger = self.logger
        trade_time = self._get_trade_date_str()
        log_str = (
            "{} {} <做空> 当前日k线生成时间:{} 最近一次30分钟收盘价与EMA60"
            "交叉时间{} 交叉前一根30分钟K线ema60:{} close:{}"
        )
        daily_klines = self._d_klines
        c_dkline = daily_klines.iloc[-1]
        l_dkline = self._get_last_kline_in_trade(daily_klines)
        l30m_kline = daily_klines.iloc[-9]
        c_date = tq_tools._get_datetime_from_ns(c_dkline.datetime)
        temp_df = self._30m_klines.iloc[::-1]
        e60, close = 0, 0
        for i, temp_kline in temp_df.iterrows():
            _, _, e60, _, close, _, trade_time, _, _ = self._get_indicators(
                temp_kline
            )
            if close >= e60:
                # 30分钟收盘价和ema60还未交叉，不符合开仓条件
                if i == 199:
                    break
                else:
                    t30m_kline = self._30m_klines.iloc[i + 1]  # type: ignore
                    _, et22, et60, _, _, _, _, _, _ = self._get_indicators(
                        t30m_kline
                    )
                    if et22 > et60:
                        l30m_kline = t30m_kline
                        break
        temp_date = tq_tools._get_datetime_from_ns(l30m_kline.datetime)
        # 当30分钟线生成时间小于21点，其所在日线为当日，否则为下一日日线
        if temp_date.hour < 21:
            l_date = tafunc.time_to_ns_timestamp(
                datetime(temp_date.year, temp_date.month, temp_date.day)
            )
        else:
            l_date = tafunc.time_to_ns_timestamp(
                datetime(temp_date.year, temp_date.month, temp_date.day)
                + timedelta(days=1)
            )
        l_klines = daily_klines[daily_klines.datetime <= l_date]
        if not l_klines.empty:
            l_kline = l_klines.iloc[-1]
            logger.debug(
                log_str.format(
                    trade_time, self.ts.symbol, c_date, temp_date, e60, close
                )
            )
            logger.debug(
                f"当前日线id:{c_dkline.id},生成时间:{c_date},"
                f"交叉当时K线id:{l_kline.id},生成时间:"
                f"{tafunc.time_to_datetime(l_kline.datetime)}"
            )
            limite_day = 2
            _, el22, el60, _, cloes_l, _, _, _, _ = self._get_indicators(
                l_dkline
            )
            if (
                tools.diff_two_value(el22, el60)
                and cloes_l < el60
                or tools.diff_two_value(el22, el60) > 5
            ):
                limite_day = 3
            if c_dkline.id - l_kline.id <= limite_day:
                logger.debug(f"满足做空30分钟条件，两个日线间隔在{limite_day}日内。")
                return True
        return False

    def _match_3hk_c2_distance(self) -> bool:
        # logger = self.logger
        klines = self._3h_klines.iloc[::-1]
        # log_str = 'k2:{},e9:{},e60:{},date:{}/k1:{},e22:{},e60:{},date:{}'
        k1, k2 = 0, 0
        is_done_1 = False
        for _, kline in klines.iterrows():
            # logger.debug(f'kline:{kline}')
            e9 = kline.ema9
            e22 = kline.ema22
            e60 = kline.ema60
            if not is_done_1 and e22 <= e60:
                k1 = kline.id
                # date1 = get_date_str(kline.datetime)
                # ema22 = e22
                # ema60_1 = e60
                is_done_1 = True
                # logger.debug(log_debug_1.format(
                #    k1, e9, e22, e60, date1
                # ))
            if e9 <= e60:
                k2 = kline.id
                # date2 = get_date_str(kline.datetime)
                # ema9 = e9
                # ema60_2 = e60
                # logger.debug(log_debug_2.format(
                #    k2, e9, e22, e60, date2
                # ))
                break
        if 0 <= k1 - k2 <= 5:
            # logger.debug(log_str.format(
            # k2, ema9, ema60_2, date2, k1, ema22, ema60_1, date1))
            # logger.debug('两个交点距离小于等于5,符合条件')
            return True
        return False

    def _set_open_condition(
        self, kline, cond_num: int, indiatorValues: MainIndicatorValues
    ):
        """设置开仓条件"""
        (
            e9,
            e22,
            e60,
            macd,
            close,
            open_p,
            trade_time,
            _,
            _,
        ) = self._get_indicators(kline)
        indiatorValues.ema9 = e9
        indiatorValues.ema22 = e22
        indiatorValues.ema60 = e60
        indiatorValues.macd = macd
        indiatorValues.close = close
        indiatorValues.open = open_p
        indiatorValues.kline_time = trade_time
        indiatorValues.condition_id = cond_num

    def _set_sold_condition(self):
        s_c = self.ts.sold_condition
        s_c.take_profit_stage = 0

    def _store_open_pos_info(self, order: Order):
        service.open_main_pos(self.ts, order)

    @abstractmethod
    def _match_dk_condition(self, is_in=True) -> bool:
        """做多日线条件检测"""

    @abstractmethod
    def _match_3h_condition(self, is_in=True) -> bool:
        pass

    @abstractmethod
    def _match_30m_condition(self, is_in=True) -> bool:
        pass

    @abstractmethod
    def _match_5m_condition(self, is_in=True) -> bool:
        pass

    @abstractmethod
    def _has_match_stop_loss(self) -> bool:
        """返回是否已符合止损条件"""

    @abstractmethod
    def _try_improve_stop_loss(self) -> None:
        """当满足条件时提高止损价格"""

    @abstractmethod
    def _is_f5m_closeout(self) -> bool:
        """判断在交易日最后5分钟是否应该平仓"""

    @abstractmethod
    def _get_profit_condition(self) -> int:
        """返回止盈条件序号，并存储到数据库"""
