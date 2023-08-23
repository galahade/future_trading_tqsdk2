from strategies.main_joint_symbol_strategies.mjs_strategy import MJStrategy
from strategies.trade_strategies.bts.bts_long import BottomLongTradeStrategy
from strategies.trade_strategies.bts.bts_short import BottomShortTradeStrategy
from strategies.trade_strategies.mts.mts_long import MainLongTradeStrategy
from strategies.trade_strategies.mts.mts_short import MainShortTradeStrategy
from strategies.trade_strategies.trade_strategies import TradeStrategy


class MJMainStrategy(MJStrategy):
    '''主连主策略基类

    该类的子类包括两类：主连做多主策略和主连做空主策略
    '''

    def _get_name(self) -> str:
        return 'main'

    def execute_before_trade(self, is_in_trading: bool):
        pass


class MJBottomStrategy(MJStrategy):
    '''主连摸底策略基类

    该类的子类包括两类：主连做多摸底策略和主连做空摸底策略
    '''

    def _get_name(self) -> str:
        return 'bottom'


class MJMainLongStrategy(MJMainStrategy):

    def _create_trade_strategy(self, symbol: str) -> TradeStrategy:
        return MainLongTradeStrategy(self.config, symbol)

    def _get_direction(self) -> bool:
        return True


class MJMainShortStrategy(MJMainStrategy):

    def _create_trade_strategy(self, symbol: str) -> TradeStrategy:
        return MainShortTradeStrategy(self.config, symbol)

    def _get_direction(self) -> bool:
        return False


class MJBottomLongStrategy(MJBottomStrategy):

    def _create_trade_strategy(self, symbol: str) -> TradeStrategy:
        return BottomLongTradeStrategy(self.config, symbol)

    def _get_direction(self) -> bool:
        return True


class MJBottomShortStrategy(MJBottomStrategy):

    def _create_trade_strategy(self, symbol: str) -> TradeStrategy:
        return BottomShortTradeStrategy(self.config, symbol)

    def _get_direction(self) -> bool:
        return False
