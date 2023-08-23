from typing import List
from dao.odm.future_config import FutureConfigInfo
from dao.odm.future_trade import BottomOpenVolumeTip
from utils.common_tools import get_zl_symbol
import xlwings as xw
import dao.trade.trade_service as t_service


class Trade_Tips_Sheet:

    def __init__(self, book: xw.Book, future_configs: list[FutureConfigInfo]):
        self.sheet = book.sheets.add()
        self.future_configs = future_configs
        sheet = self.sheet
        sheet.range('A1').value = 'NO'
        sheet.range('B1').value = '合约'
        sheet.range('C1').value = '方向'
        sheet.range('D1').value = '手数'
        sheet.range('E1').value = '收盘价'
        sheet.range('F1').value = '合约乘数'
        sheet.range('G1').value = '开仓比例'
        sheet.range('H1').value = '资金总额'
        sheet.range('I1').value = '时间'
        sheet.range('J1').value = '7日内提示次数'
        # sheet.range('K1').value = '手数'
        # sheet.range('L1').value = '浮动盈亏'
        # sheet.range('M1').value = '手续费'
        # sheet.range('N1').value = '账户权益'
        # sheet.range('O1').value = '回撤'
        # sheet.range('P1').value = '计算的盈亏'
        self.count = 2

    def record_line(self, bovt: BottomOpenVolumeTip):
        st = self.sheet
        st.range((self.count, 1)).value = self.count - 1
        st.range((self.count, 2)).value = bovt.symbol
        st.range((self.count, 3)).value = '多' if bovt.direction else '空'
        st.range((self.count, 4)).value = bovt.volume
        st.range((self.count, 5)).value = bovt.last_price
        st.range((self.count, 6)).value = self._get_multiplier(bovt)
        st.range((self.count, 7)).value = self._get_open_pos_scale(bovt)
        st.range((self.count, 8)).value = 0
        st.range((self.count, 9)).value = bovt.dkline_time
        st.range((self.count, 10)).value = t_service.get_last7d_count(bovt)
        # st.range((self.count, 11)).value = opi.trade_number
        # st.range((self.count, 12)).value = float_profit
        # st.range((self.count, 13)).value = commission
        # st.range((self.count, 14)).value = balance
        # st.range((self.count, 15)).value = self.failback
        # st.range((self.count, 16)).value = cfp
        st.autofit(axis="columns")
        self.count += 1

    def _get_multiplier(self, bovt: BottomOpenVolumeTip) -> int:
        zl_symbol = get_zl_symbol(bovt.symbol)
        for config in self.future_configs:
            if config.symbol == zl_symbol:
                return config.multiple
        return 0

    def _get_open_pos_scale(self, bovt: BottomOpenVolumeTip) -> float:
        '''获取开仓比例'''
        zl_symbol = get_zl_symbol(bovt.symbol)
        for config in self.future_configs:
            if config.symbol == zl_symbol:
                return config.open_pos_scale
        return 0.0

    def finish(self):
        st = self.sheet
        # st.range((self.count, 2)).value = '总盈亏'
        # st.range((self.count, 3)).value = self.total_profit
        # st.range((self.count, 4)).value = '最大回撤'
        # st.range((self.count, 5)).value = self.maxfailback


class Trade_Tips_Book:

    def __init__(self, db_name, future_configs: list[FutureConfigInfo], bovts: List[BottomOpenVolumeTip]):
        self.wb = xw.Book()
        self.name = f'{db_name}.xlsx'
        self.bovts = bovts
        self.sheet = Trade_Tips_Sheet(self.wb, future_configs)

    def finish(self):
        for bovt in self.bovts:
            self.sheet.record_line(bovt)
        self.sheet.finish()
        self.wb.save(self.name)
