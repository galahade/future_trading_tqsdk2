from datetime import datetime
from math import ceil
from abc import ABC, abstractmethod
from pandas import DataFrame
from tqsdk.objs import Order
from tqsdk import tafunc
import dao.trade.trade_service as service
from dao.odm.future_trade import (TradeStatus)
from strategies.entity import StrategyConfig
from utils.common_tools import LoggerGetter, get_china_date_from_str  # type: ignore
import utils.tqsdk_tools as tq_tools
import strategies.tools as tools


class Strategy(ABC):
    '''策略基类'''
    logger = LoggerGetter()

    def __init__(self, config: StrategyConfig):
        self.config = config

    @abstractmethod
    def execute_before_trade(self, is_in_trading: bool):
        pass

    @abstractmethod
    def execute_trade(self):
        pass

    @abstractmethod
    def execute_after_trade(self):
        pass


class TradeStrategy(Strategy):
    '''交易策略基类'''

    def __init__(self, config: StrategyConfig, symbol: str):
        super().__init__(config)
        self.api = config.api
        self.symbol = symbol
        self.ts = self._get_trade_status(symbol)
        self.quote = self.api.get_quote(symbol)
        self._d_klines = self.fetch_daily_klines()
        self._3h_klines = self.api.get_kline_serial(
            symbol, self.config.get3hK_Duration()
        )
        self._30m_klines = self.api.get_kline_serial(
            symbol, self.config.get30mK_Duration()
        )
        self._5m_klines = config.api.get_kline_serial(
            symbol, self.config.get5mK_Duration()
        )
        self.fill_indicators_by_type(1)

    def execute_before_trade(self, is_in_trading: bool):
        '''在交易前执行，提供开盘提示等功能

        默认不提供该功能，只在摸底策略中提供盘前提示功能
        '''
        pass

    def execute_trade(self):
        '''在交易期间，循环执行该方法尝试交易'''
        self._trade_switch_symbol()
        if self.is_trading():
            self._try_close_pos()
        elif not self.is_trading():
            self._try_open_pos()

    def execute_after_trade(self):
        '''在收盘后执行

        当结束交易时，重新获取日线数据
        '''
        # 由于在staker中，每次交易结束后都会重新生成新的交易人，故此处不需要再次获取
        # self.fetch_daily_klines()

    def closeout(self, c_type: int, c_message: str) -> Order:
        '''全部平仓, 可以安全调用，不会重复平仓

        c_type: 0: 止损, 1: 止盈, 2: 换月, 3: 人工平仓 
        '''
        return self.close_pos(self.ts.carrying_volume, c_type, c_message)  # type: ignore

    def open_pos(self, pos: int, o_message='') -> Order:
        '''进行开仓相关操作，并记录开仓信息，输出日志'''
        order = self._trade_pos(pos, 'OPEN')
        self._set_open_pos_info(order)
        self._store_open_pos_info(order)
        log_str = '{} {} {} 开仓 价格：{} 数量：{}'
        self.logger.info(log_str.format(
            tq_tools.get_date_str(self._get_trade_date()),
            self.ts.symbol, self.ts.custom_symbol, order.trade_price,
            order.volume_orign))
        if not self.config.is_backtest:
            tools.sendTradePosMsg(
                self.ts.custom_symbol, self.ts.symbol, bool(
                    self._get_direction()),
                pos, order.trade_price, tq_tools.get_date_str(
                    order.insert_date_time))
        return order

    def close_pos(self, pos: int, c_type: int, c_message: str) -> Order:
        '''根据数量进行平仓，并记录平仓信息，输出日志'''
        order = None
        if self.ts.trade_status == 1:
            order = self._trade_pos(pos, 'CLOSE')
            order.close_volume = service.close_ops(self.ts, c_type, c_message, order)
        return order  # type: ignore

    def is_changing(self, k_type: int) -> bool:
        '''判断是否有某个周期的K线正在发生改变

        k_type: 1: 交易日结束 2: 日线, 3: 3小时线, 4: 30分钟线, 5: 5分钟线
        '''
        if k_type == 2:
            return self.config.api.is_changing(
                self._d_klines.iloc[-1], "datetime")
        elif k_type == 3:
            return self.config.api.is_changing(
                self._3h_klines.iloc[-1], "datetime")
        elif k_type == 4:
            return self.config.api.is_changing(
                self._30m_klines.iloc[-1], "datetime")
        elif k_type == 5:
            return self.config.api.is_changing(
                self._5m_klines.iloc[-1], "datetime")
        elif k_type == 1:
            return self.config.api.is_changing(
                self._d_klines.iloc[-1], "datetime")
        return False

    def fetch_daily_klines(self) -> DataFrame:
        '''获得日线序列, 由于天勤量化实盘中实时获取日线序列会导致错误，故需要特殊处理

        在实盘交易中，由于获取的是日线的拷贝数据。故当日线发生变化时，需要重新获取日线数据。
        '''
        if self.config.is_backtest:
            self._d_klines = self.api.get_kline_serial(
                self.ts.symbol, self.config.getDailyK_Duration(),
                self.config.getKlineLength())
        else:
            self._d_klines = self.api.get_kline_serial(
                self.ts.symbol, self.config.getDailyK_Duration(),
                self.config.getKlineLength()).copy()
        return self._d_klines

    def _trade_switch_symbol(self):
        record = service.get_switch_symbol_trade_record(self.ts)
        if record is not None:
            ovi = record.current_open_volume_info
            order_c = self.close_pos(ovi.volume, 2, '换月平仓')
            record.close_volume_info = order_c.close_volume
            if record.next_need_open:
            # TO-DO: 当需要换月开仓时，需要确定它的止盈止损条件，
            # 但目前还无法确定，所以暂时不开仓，等待条件确定后在实现开仓逻辑 
                record.next_open_status = True
            service.update_switch_symbol_trade_record(record)

    def _trade_pos(self, pos: int, offset: str) -> Order:
        '''和期货交易所进行期货交易
        先尝试市价下单，如果不支持则将当前价格作为限价尝试下单'''
        try:
            order = self.api.insert_order(
                symbol=self.ts.symbol,
                direction=self._get_open_direction(),
                offset=offset,
                volume=pos
            )
        except Exception as e:
            order = self.api.insert_order(
                symbol=self.ts.symbol,
                direction=self._get_open_direction(),
                offset=offset,
                volume=pos,
                limit_price=self._get_current_price()
            )
        while True:
            self.api.wait_update()
            if order.status == "FINISHED":
                break
        service.store_tq_order(order)
        return order

    def _calc_price(self, o_price: float, scale: float, is_up: bool) -> float:
        """根据给定价格和调整比例和调整方向计算最新价格

        Args:
            o_price (float): 原始价格
            scale (float): 基础调整比例 
            is_up (bool): 是否是上浮

        Returns:
            float: 调整后的价格
        """
        if is_up:
            return round(o_price * (1 + self._get_base_scale() * scale), 2)
        else:
            return round(o_price * (1 - self._get_base_scale() * scale), 2)

    def _is_last_5m(self) -> bool:
        '''判断是否是最后5分钟'''
        t_time = tafunc.time_to_datetime(self.quote.datetime)
        time_num = int(t_time.time().strftime("%H%M%S"))
        return 150000 > time_num > 145500

    def _has_dk_changed(self):
        '''当日线生成新K线时返回True'''
        return self.api.is_changing(self._d_klines[-1], 'datetime')

    def _has_3hk_changed(self):
        '''当3小时线生成新K线时返回True'''
        return self.api.is_changing(self._3h_klines[-1], 'datetime')

    def _has_30mk_changed(self):
        '''当30分钟线生成新K线时返回True'''
        return self.api.is_changing(self._30m_klines[-1], 'datetime')

    def _get_trade_date(self) -> datetime:
        '''从天勤的报价对象中获取交易的当前时间'''
        return get_china_date_from_str(self.quote.datetime)

    def _get_trade_date_str(self) -> str:
        '''从天勤的报价对象中获取交易的当前时间'''
        return self._get_trade_date().strftime("%Y-%m-%d %H:%M:%S")

    def _calc_open_pos(self, price) -> int:
        '''计算开仓手数

        根据账户余额与该品种开仓比例计算出交易该品种可用余额，
        可用余额除以开仓价格向上取整，获得可开仓手术'''
        f_info = self.config.f_info
        available = (
            self.api.get_account().balance *
            f_info.open_pos_scale / f_info.multiple)
        self.logger.debug(f'{available}-{price}-{self.api.get_account().balance}-{f_info.open_pos_scale}-{f_info.multiple}')
        pos = ceil(available / price)
        return pos

    def _try_close_pos(self):
        '''交易的主要方法，负责判断是否满足平仓条件：当合约有持仓时，尝试止盈或止损
        满足条件后平仓。'''
        if self.is_trading():
            self._try_stop_loss()
            self._try_take_profit()

    def _try_open_pos(self):
        '''交易的主要方法，负责判断是否满足开仓条件：当合约无持仓，且满足条件后开仓。'''
        if not self.is_trading():
            if self._can_open_pos():
                try:
                    pos = self._calc_open_pos(self._get_current_price())
                    self.open_pos(pos)
                except Exception as e:
                    self.logger.debug(f'quote:{self.quote}')
                    raise e

    def _set_klines_value(self, klines, k_name, k_key, k_value):
        klines.loc[k_name, k_key] = k_value

    def _get_carry_pos(self) -> int:
        '''获取持仓手数'''
        return self.ts.carrying_volume  # type: ignore

    def is_trading(self) -> bool:
        '''判断是否已经有交易存在'''
        return self.ts.trade_status == 1

    def _get_current_price(self) -> float:
        '''获取当前交易所交易价格'''
        return self.quote.last_price

    def _set_open_pos_info(self, order: Order):
        '''设置开仓信息'''
        self._set_sold_condition()
        self._set_sold_prices(order)

    @abstractmethod
    def _store_open_pos_info(self, order: Order):
        '''存储开仓信息'''

    @abstractmethod
    def _get_trade_status(self, symbol: str) -> TradeStatus:
        '''获取交易状态'''

    @abstractmethod
    def _get_open_direction(self) -> str:
        '''获取当前交易策略的开仓方向'''

    @abstractmethod
    def _get_close_direction(self) -> str:
        '''获取当前交易策略的平仓方向'''

    @abstractmethod
    def _can_open_pos(self) -> bool:
        '''判断是否可以开仓'''

    @abstractmethod
    def _try_stop_loss(self):
        '''当满足止损条件时，进行止损操作'''

    @abstractmethod
    def _try_take_profit(self) -> None:
        '''当满足止盈条件时，进行止盈操作'''

    @abstractmethod
    def _get_direction(self) -> int:
        '''获取当前交易策略的方向'''

    @abstractmethod
    def _set_sold_condition(self):
        '''设置平仓条件'''

    @abstractmethod
    def _set_sold_prices(self, order: Order):
        '''设置平仓价格'''

    @abstractmethod
    def _get_base_scale(self) -> float:
        '''获取当前交易策略的基础开仓比例

        开仓比例为开仓资金占总资金的比例
        '''

    @abstractmethod
    def _need_stop_loss(self, c_price: float) -> bool:
        '''是否需要止损'''

    @abstractmethod
    def fill_indicators_by_type(self, k_type: int):
        '''根据K线类型填充指标 1:全部K线 2:日线 3:3小时线 4:30分钟线 5:5分钟线
        '''


class LongTradeStrategy(TradeStrategy):

    def _get_open_direction(self) -> str:
        return 'BUY'

    def _get_close_direction(self) -> str:
        return 'SELL'

    def _get_direction(self) -> int:
        return 1

    def _get_base_scale(self) -> float:
        return self.config.f_info.long_config.base_scale

    def _need_stop_loss(self, c_price: float) -> bool:
        return c_price <= self.ts.sold_condition.stop_loss_price


class ShortTradeStrategy(TradeStrategy):

    def _get_open_direction(self) -> str:
        return 'SELL'

    def _get_close_direction(self) -> str:
        return 'BUY'

    def _get_direction(self) -> int:
        return 0

    def _get_base_scale(self) -> float:
        return self.config.f_info.short_config.base_scale

    def _need_stop_loss(self, c_price: float) -> bool:
        return c_price >= self.ts.sold_condition.stop_loss_price
