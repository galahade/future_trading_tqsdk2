from abc import abstractmethod
from typing import List, Optional
from tqsdk2 import TqApi
from dao.odm.future_config import FutureConfigInfo
from strategies.cyclical_strategies import CyclicalStrategy
from strategies.entity import StrategyConfig
import strategies.tools as tools
from strategies.main_joint_symbol_strategies.smjs_strategies import (
    MJBottomLongStrategy,
    MJBottomShortStrategy,
    MJBottomStrategy,
    MJMainLongStrategy,
    MJMainShortStrategy,
    MJMainStrategy,
    MJStrategy,
)
from utils.common import LoggerGetter
from utils.common_tools import get_china_date_from_str
import logging


class StrategyTrader:
    logger = LoggerGetter()

    def __init__(self, s_config: StrategyConfig):
        self._config = s_config
        self.long_mjs: Optional[MJStrategy]
        self.short_mjs: Optional[MJStrategy]
        self._init_MJ_strategy()
        self.cycle_strategy = CyclicalStrategy(self._config)

    def _init_MJ_strategy(self):
        """根据交易方向类型创建主连策略

        交易方向类型决定了策略交易者所拥有的主连方向策略：
        1. 多头策略交易者拥有多头主连策略
        0. 空头策略交易者拥有空头主连策略
        2. 多空策略交易者拥有多头和空头主连策略
        """
        if self._config.direction in [1, 2]:
            self.long_mjs = self._get_mjs_by_direction(1)
        if self._config.direction in [0, 2]:
            self.short_mjs = self._get_mjs_by_direction(0)

    @staticmethod
    def get_strader_by_sid(config: StrategyConfig, sid: int):
        """工厂方法，根据 sid 创建相应的策略交易者

        Args:
            sid (int): 策略类型：1 代表主策略，2 代表摸底策略

        Raises:
            ValueError: 目前支持的 sid 只有 1 和 2，其他值会抛出异常,为不支持的策略类型

        Returns:
            StrategyTrader: 返回该类的子类实例，如 MainStrategyTrader
        """
        logger = logging.getLogger(__name__)
        try:
            if sid == 1:
                return MainStrategyTrader(config)
            if sid == 2:
                return BottomStrategyTrader(config)
        except Exception as e:
            logger.error(e, stack_info=True)
            raise e
        raise ValueError("sid must be 1 or 2")

    @abstractmethod
    def _get_mjs_by_direction(self, direction: int) -> MJStrategy:
        """根据交易方向获取该类型交易人对应的主连策略

        Args:
            direction (int): 交易方向，1 代表多头策略，0 代表空头策略，2 代表多空策略
        """

    def _switch_symbol(self):
        """尝试换月"""
        if self.long_mjs is not None:
            self.cycle_strategy.switch_symbol(self.long_mjs)
        if self.short_mjs is not None:
            self.cycle_strategy.switch_symbol(self.short_mjs)

    def execute_before_trade(self):
        self._switch_symbol()
        is_in_trading = tools.is_trading_time(
            self._config.api, self._config.f_info.symbol
        )
        if self.long_mjs is not None:
            self.long_mjs.execute_before_trade(is_in_trading)
        if self.short_mjs is not None:
            self.short_mjs.execute_before_trade(is_in_trading)

    def execute_after_trade(self):
        if self.long_mjs is not None:
            self.long_mjs.execute_after_trade()
        if self.short_mjs is not None:
            self.short_mjs.execute_after_trade()

    def execute_trade(self):
        if self.long_mjs is not None:
            self.long_mjs.execute_trade()
        if self.short_mjs is not None:
            self.short_mjs.execute_trade()


class MainStrategyTrader(StrategyTrader):
    """主力合约交易员"""

    def _get_mjs_by_direction(self, direction: int) -> MJMainStrategy:
        """根据交易方向获取该类型交易人对应的主连策略

        Args:
            direction (int): 交易方向，1 代表多头策略，0 代表空头策略，2 代表多空策略
        """
        if direction == 1:
            return MJMainLongStrategy(self._config)
        if direction == 0:
            return MJMainShortStrategy(self._config)
        raise ValueError("direction must be 1 or 0")


class BottomStrategyTrader(StrategyTrader):
    """摸底策略交易员"""

    def _get_mjs_by_direction(self, direction: int) -> MJBottomStrategy:
        """根据交易方向获取该类型交易人对应的主连策略

        Args:
            direction (int): 交易方向，1 代表多头策略，0 代表空头策略，2 代表多空策略
        """
        if direction == 1:
            return MJBottomLongStrategy(self._config)
        if direction == 0:
            return MJBottomShortStrategy(self._config)
        raise ValueError("direction must be 1 or 0")


class Trader:
    """分为激活的交易员和观察交易员。激活的交易员参与实盘交易，观察交易员进行盘前交易提示。

    每个期货品种对应一个交易人，交易人可以使用多种交易策略.
    记录交易品种相关信息，包括：主连合约，主力合约，quote，个级别k线等，接受盯盘人发出的信号，并根据信号调用相关策略，
    同时记录交易策略运行结果。当符合开仓/平仓条件后调用开仓/平仓工具进行交易
    """

    logger = LoggerGetter()

    def __init__(
        self,
        api: TqApi,
        future_info: FutureConfigInfo,
        strategy_ids: List[int],
        direction: int = 2,
        is_bt: bool = False,
    ):
        self.is_active = future_info.is_active
        self._config = StrategyConfig(api, future_info, direction, is_bt)
        self.strategy_traders: List[StrategyTrader] = self._init_s_traders(
            strategy_ids
        )
        self.is_finished = False
        self._has_run_after_execute = False
        self._mj_d_klines = api.get_kline_serial(
            future_info.symbol, self._config.getDailyK_Duration()
        )

    def _init_s_traders(self, strategy_ids: List[int]) -> List[StrategyTrader]:
        """初始化策略交易人, 每种交易策略对应一个策略交易人"""
        s_traders = []
        for sid in strategy_ids:
            s_traders.append(
                StrategyTrader.get_strader_by_sid(self._config, sid)
            )
        return s_traders

    def _is_daily_trade_finished(self) -> bool:
        return tools.is_after_execute_time(
            self._config.api, self._config.f_info.symbol
        )

    def _is_trading_time(self) -> bool:
        symbol = self._config.f_info.symbol
        if len(self.strategy_traders):
            s_trader = self.strategy_traders[0]
            if self.strategy_traders[0].long_mjs is not None:
                symbol = s_trader.long_mjs.current_trade_strategy.ts.symbol
            else:
                symbol = s_trader.short_mjs.current_trade_strategy.ts.symbol

        return tools.is_trading_time(self._config.api, symbol)

    def execute_trade(self):
        """根据该品种配置和当前交易时间，执行交易操作"""
        logger = self.logger
        log_str = "{} {} <交易人> 完成当日交易，开始执行盘后操作"
        quote_time = get_china_date_from_str(self._config.quote.datetime)
        if self._is_daily_trade_finished() and not self._has_run_after_execute:
            logger.info(log_str.format(quote_time, self._config.f_info.symbol))
            self.execute_after_trade()
            self._has_run_after_execute = True
        elif self.is_active and self._is_trading_time():
            for s_trader in self.strategy_traders:
                s_trader.execute_trade()

    def execute_before_trade(self):
        """交易前的准备工作,

        包括：各种策略的换月，实盘交易中提示开仓等
        """
        for s_trader in self.strategy_traders:
            s_trader.execute_before_trade()

    def execute_after_trade(self):
        """交易前的准备工作,

        包括：各种策略的换月，实盘交易中提示开仓等
        """
        for s_trader in self.strategy_traders:
            s_trader.execute_after_trade()


class TestTrader(Trader):
    def _is_daily_trade_finished(self) -> bool:
        return self._config.api.is_changing(
            self._mj_d_klines.iloc[-1], "datetime"
        )

    def execute_trade(self):
        """根据该品种配置和当前交易时间，执行交易操作"""
        logger = self.logger
        log_str = "{} {} <交易人:{}> 完成当日交易，准备产生新的交易人"
        quote_time = get_china_date_from_str(self._config.quote.datetime)
        if self._is_daily_trade_finished():
            logger.info(
                log_str.format(quote_time, self._config.f_info.symbol, id(self))
            )
            self.is_finished = True
        elif (
            self.is_active
            and not self.is_finished
            and tools.is_trading_time(
                self._config.api, self._config.get_mj_symbol()
            )
        ):
            for s_trader in self.strategy_traders:
                s_trader.execute_trade()
