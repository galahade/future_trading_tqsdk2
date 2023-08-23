from abc import abstractmethod
import dao.trade.trade_service as service
from dao.odm.future_trade import MainJointSymbolStatus
from strategies.entity import StrategyConfig
from strategies.trade_strategies.trade_strategies import (Strategy,
                                                          TradeStrategy)
from utils.common_tools import get_next_symbol
from utils.tqsdk_tools import get_date_str


class MJStrategy(Strategy):
    '''主连合约策略基类

    该类的子类包括两类：主连主策略和主连摸底策略
    '''

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.mjs_status = self._get_MJSymbol_status()
        self.config.setCustomSymbol(self.mjs_status.custom_symbol) # type: ignore
        self.current_trade_strategy: TradeStrategy =\
            self._create_trade_strategy(
                self.mjs_status.current_symbol)  # type: ignore
        self.next_trade_strategy: TradeStrategy =\
            self._create_trade_strategy(
                self.mjs_status.next_symbol)  # type: ignore
    
    def _update_trade_strategy(self):
        '''更新策略的合约状态表'''
        self.current_trade_strategy = self._create_trade_strategy(
            self.mjs_status.current_symbol)  # type: ignore
        self.next_trade_strategy = self._create_trade_strategy(
            self.mjs_status.next_symbol)  # type: ignore

    def swith_symbol(self):
        '''盘前换月

        换月流程： 
            1. 记录需要换月交易的信息
            2. 更新主连合约状态表中的当前合约和下一个合约的信息
            3. 更新各策略的合约状态表
        '''
        current_symbol = self.config.quote.underlying_symbol
        next_symbol = get_next_symbol(
            self.config.quote.underlying_symbol,
            self.config.f_info.main_symbols)  # type: ignore
        self.mjs_status.current_symbol = current_symbol
        self.mjs_status.next_symbol = next_symbol
        current_status = self.current_trade_strategy.ts
        next_status = self.next_trade_strategy.ts
        self.logger.info(f'主连合约{self.mjs_status.main_joint_symbol}换月：'
                         f'上一主力合约：{current_status.symbol} '
                         f'下一主力合约：{next_status.symbol}'
                         f'交易系统主力合约：{self.mjs_status.current_symbol}'
                         f'即将成为主力的合约：{self.mjs_status.next_symbol}')
        service.switch_symbol(self.mjs_status, current_status, next_status,
                              self.config.quote.datetime)
        # self.next_trade_strategy = self._create_trade_strategy(status.symbol)

    def _get_MJSymbol_status(self) -> MainJointSymbolStatus:
        return service.get_MJStatus(
            self.config.f_info.symbol, self.config.quote.underlying_symbol,  # type: ignore
            get_next_symbol(
                self.config.quote.underlying_symbol,
                self.config.f_info.main_symbols), self._get_direction(),  # type: ignore
            self.config.quote.datetime, self._get_name())

    def execute_before_trade(self, is_in_trading: bool):
        self._update_trade_strategy()
        self.current_trade_strategy.execute_before_trade(is_in_trading)
        self.next_trade_strategy.execute_before_trade(is_in_trading)

    def execute_trade(self):
        '''当K线发生变化时，先为K线填充数据，然后执行交易策略'''
        if self._is_changing(1):
            self.execute_after_trade()
        if self._is_changing(2):
            self.fill_indicators_by_type(2)
        if self._is_changing(3):
            self.fill_indicators_by_type(3)
        if self._is_changing(4):
            self.fill_indicators_by_type(4)
        if self._is_changing(5):
            self.fill_indicators_by_type(5)
        if self.config.api.is_changing(self.config.quote, 'datetime'):
            self.current_trade_strategy.execute_trade()
            self.next_trade_strategy.execute_trade()

    def execute_after_trade(self):
        logger = self.logger
        log_str = '{} {} 交易时间结束，开始执行收盘后操作'
        self.current_trade_strategy.execute_after_trade()
        self.next_trade_strategy.execute_after_trade()
        logger.info(log_str.format(
            get_date_str(self.config.quote.datetime), self.config.f_info.symbol))

    def fill_indicators_by_type(self, indicator_type: int):
        self.current_trade_strategy.fill_indicators_by_type(indicator_type)
        self.next_trade_strategy.fill_indicators_by_type(indicator_type)

    def _is_changing(self, k_type: int) -> bool:
        '''k_type: 1: 交易日结束 2: 日线, 3: 3小时线, 4: 30分钟线, 5: 5分钟线'''
        return self.current_trade_strategy.is_changing(k_type)

    @abstractmethod
    def _create_trade_strategy(self, symbol: str) -> TradeStrategy:
        pass

    @abstractmethod
    def _get_name(self) -> str:
        pass

    @abstractmethod
    def _get_direction(self) -> bool:
        '''返回多空方向

        True: 多 False: 空
        '''
