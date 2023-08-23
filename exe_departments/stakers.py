from abc import ABC, abstractmethod
from typing import List
from venv import logger
from tqsdk import TqApi
from dao.odm.future_config import FutureConfigInfo
from exe_departments.traders import MainStrategyTrader, Trader
from utils.common import LoggerGetter
from utils.config_utils import (get_future_configs)
import dao.config_service as c_service


class Staker(ABC):
    logger = LoggerGetter()
    '''盯盘人，负责加载期货品种配置，并为每个品种生成一个交易人。当盯盘品种价格等参数发生改变时向交易人发送信号'''

    def __init__(self, api: TqApi, direction: int, strategy_ids: List[int]):
        self._api = api
        self.direction = direction
        self.strategy_ids = strategy_ids
        self.future_configs: list[FutureConfigInfo] = self._init_future_configs(
        )
        self._init_status()

    def start_work(self):
        '''执行盯盘操作

        每次程序运行该方法执行一次。除非被中断，否则不会停止。 
        '''
        logger = self.logger
        logger.info(f'交易初始资金为{self._api.get_account().balance}')
        # self._api.wait_update()
        logger.info("天勤服务器端已连接成功")
        self._prepare_task()
        logger.info("交易准备工作完成，开始盯盘".center(100, "*"))
        self._handle_trade()

    def _handle_trade(self):
        '''交易相关操作，包括盘前提示，交易，盘后操作

        当交易日结束后该函数将退出执行，然后重新生成trader并再次执行该函数。'''
        logger = self.logger
        for trader in self.traders:
            trader.execute_before_trade()
        logger.info(
            '盘前提示结束，开始进入交易'.center(100, '*')
        )
        while True:
            traders = filter(lambda t: t.is_active, self.traders)
            # 当所有交易员当日交易结束后，退出循环
            traders = list(traders)
            self._api.wait_update()
            for trader in traders:
                trader.execute_trade()

    def _init_status(self):
        '''初始化盯盘人的状态，使得盯盘人可以进行下一日交易'''
        self.traders: List[Trader] = self._init_traders(
            self.direction, self.strategy_ids)

    def _prepare_task(self):
        self.logger.info('当前配置的品种为:')
        for trader in self.traders:
            self.logger.info(f'{trader._config.f_info.symbol}')
        self.logger.info('当前参与交易品种为:')
        for trader in filter(lambda t: t.is_active, self.traders):
            self.logger.info(f'{trader._config.f_info.symbol}')
            s_traders = trader.strategy_traders
            for strader in filter(lambda t: t.long_mjs is not None, s_traders):
                if isinstance(strader, MainStrategyTrader):
                    self.logger.info('主策略做多合约列表：')
                    self.logger.info(f'当前合约：{strader.long_mjs.mjs_status.current_symbol}')
                    self.logger.info(f'下一合约：{strader.long_mjs.mjs_status.next_symbol}')
            for strader in filter(lambda t: t.short_mjs is not None, s_traders):
                if isinstance(strader, MainStrategyTrader):
                    self.logger.info('主策略做空合约列表：')
                    self.logger.info(f'当前合约：{strader.long_mjs.mjs_status.current_symbol}')
                    self.logger.info(f'下一合约：{strader.long_mjs.mjs_status.next_symbol}')

    @abstractmethod
    def _init_future_configs(self) -> List[FutureConfigInfo]:
        '''加载期货配置信息。

        首先在系统文件系统加载初始期货配置信息，实盘和回测的配置文件路径不同，
        当数据库中有期货配置信息时，将数据库中的期货配置信息覆盖掉系统文件系统中的配置信息。
        否则，使用系统文件系统中的配置信息为数据库初始化期货配置信息。
        '''

    @abstractmethod
    def _init_traders(self, d: int, strategy_ids: List[int]) -> List[Trader]:
        '''根据期货配置信息为每个品种生成一个交易员

        Args:
            d: 交易方向, 交易员使用它来决定策略交易员的方向类型
            strategy_ids: 策略id列表, 交易员使用它来决定策略交易员的策略类型
        '''


class RealStaker(Staker):
    '''实盘交易盯盘人'''

    def _init_future_configs(self) -> List[FutureConfigInfo]:
        return c_service.get_future_configs(get_future_configs())

    def _init_traders(self, d, strategy_ids) -> List[Trader]:
        '''加载交易员'''
        traders = []
        for f_config in self.future_configs:
            traders.append(Trader(
                self._api, f_config, strategy_ids, d, False))
        return traders


class BTStaker(Staker):
    '''回测交易盯盘人'''

    def _init_future_configs(self) -> List[FutureConfigInfo]:
        return c_service.get_future_configs(get_future_configs(is_backtest=True))

    def _init_traders(self, d, strategy_ids) -> List[Trader]:
        '''加载交易员'''
        traders = []
        for config in self.future_configs:
            traders.append(Trader(
                self._api, config, strategy_ids, d, True))
        return traders

    def _prepare_task(self):
        '''交易前的准备工作, 实盘交易打印出参与交易品种的合约信息，回测交易打印出回测的起止时间'''
        super()._prepare_task()

    def _handle_trade(self):
        '''交易相关操作，包括盘前提示，交易，盘后操作

        当交易日结束后该函数将退出执行，然后重新生成trader并再次执行该函数。'''
        logger = self.logger
        for trader in self.traders:
            trader.execute_before_trade()
        logger.info(
            '盘前提示结束，开始进入交易'.center(100, '*')
        )
        while True:
            traders = filter(
                lambda t: t.is_active and not t.is_finished, self.traders)
            # 当所有交易员当日交易结束后，退出循环
            traders = list(traders)
            if len(traders) == 0:
                logger.debug("所有交易员当日交易结束，退出交易".center(100, '*'))
                break
            self._api.wait_update()
            for trader in traders:
                trader.execute_trade()

    def start_work(self):
        '''执行盯盘操作

        每次程序运行该方法执行一次。除非被中断，否则不会停止。 
        '''
        logger = self.logger
        logger.info(f'交易初始资金为{self._api.get_account().balance}')
        # self._api.wait_update()
        logger.info("天勤服务器端已连接成功")
        self._prepare_task()
        logger.info("交易准备工作完成，开始盯盘".center(100, "*"))
        while True:
            self._handle_trade()
            self._init_status()
