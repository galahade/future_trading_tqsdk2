from datetime import datetime
from dao.odm.future_trade import (
    CloseVolume, SwitchSymbolTradeRecord, TradeStatus,
    MainJointSymbolStatus,  MainTradeStatus, BottomTradeStatus)
from utils.common_tools import get_custom_symbol
import dao.trade.main_trade_dao as mdao
import dao.trade.bottom_trade_dao as bdao

def updateSwitchSymbolTradeRecord(sstr: SwitchSymbolTradeRecord):
    '''更新换月交易记录'''
    sstr.save(cascade=True)

def createSwitchSymbolTradeRecord(
        current_status: TradeStatus,
        next_status: TradeStatus, quote_time: datetime):
    '''创建换月交易记录'''
    sstr = SwitchSymbolTradeRecord()
    sstr.custom_symbol = current_status.custom_symbol
    sstr.current_symbol = current_status.symbol
    sstr.next_symbol = next_status.symbol
    sstr.quote_time = quote_time
    sstr.direction = current_status.direction
    sstr.current_open_volume_info = current_status.open_pos_info
    if next_status.trade_status != 1:
        sstr.next_need_open = True
    sstr.last_modified = quote_time


def getSwitchSymbolTradeRecord(custom_symbol: str, symbol: str
                               ) -> SwitchSymbolTradeRecord:
    '''获取换月交易记录
    '''
    sstr = SwitchSymbolTradeRecord.objects(
        custom_symbol=custom_symbol, current_symbol=symbol,
        current_close_status=False).first()  # type: ignore 
    

def updateTradeStatus(ts: TradeStatus):
    '''更新交易状态信息到数据库中'''
    ts.save(cascade=True)


def deleteTradeStatus(ts: TradeStatus):
    ts.delete()


def getMainJointSymbolStatus(custom_symbol: str) -> MainJointSymbolStatus:
    '''根据主连合约获取策略交易状态，如果不存在则在数据库中创建
    '''
    return MainJointSymbolStatus.objects(custom_symbol=custom_symbol).first()  # type: ignore


def createMainJointSymbolStatus(
        mj_symbol: str, current_symbol: str, next_symbol: str, direction: int,
        s_name: str, dt: datetime) -> MainJointSymbolStatus:
    '''根据传入参数创建主连合约状态信息并保存到数据库中,
    参数 direction: 0:多头, 1:空头. '''
    mjss = MainJointSymbolStatus()
    mjss.custom_symbol = get_custom_symbol(mj_symbol, bool(direction), s_name)
    mjss.main_joint_symbol = mj_symbol
    mjss.current_symbol = current_symbol
    mjss.next_symbol = next_symbol
    mjss.direction = direction
    mjss.last_modified = dt
    mjss.save()
    return mjss


def save_close_volume(ts: TradeStatus, cpd: dict, cv: CloseVolume):
    '''主策略和摸底策略共用方法，用来保存'''
    opi = ts.open_pos_info
    cv.symbol = opi.symbol
    cv.direction = opi.direction
    cv.trade_price = cpd['trade_price']
    cv.volume = cpd['volume']
    cv.trade_time = cpd['trade_time']
    cv.order_id = cpd['order_id']
    cv.last_modified = cpd['trade_time']
    cv.close_type = cpd['close_type']
    cv.close_message = cpd['close_message']
    cv.save()
    opi.close_pos_infos.append(cv)  # type: ignore
    ts.carrying_volume = ts.carrying_volume - cv.volume
    if ts.carrying_volume == 0:
        ts.trade_status = 2
        ts.end_time = cv.trade_time
        opi.is_close = True
        opi.last_modified = cv.trade_time
    ts.save(cascade=True)


def save_open_volume(ts: TradeStatus, opd: dict, ov):
    '''主策略和摸底策略共用方法，用来保存'''
    ov.symbol = ts.symbol
    ov.direction = ts.direction
    ov.trade_price = opd['trade_price']
    ov.volume = opd['volume']
    ov.trade_time = opd['trade_time']
    ov.order_id = opd['order_id']
    ov.last_modified = opd['trade_time']
    ov.save()
    ts.trade_status = 1
    ts.carrying_volume = ov.volume
    ts.start_time = ov.trade_time
    ts.open_pos_info = ov
    ts.save(cascade=True)


def switch_symbol(
        mj_status: MainJointSymbolStatus,
        current_status: TradeStatus,
        next_status: TradeStatus,
        new_status: TradeStatus,
        trade_status_list: [TradeStatus]):
    '''重置期货合约交易状态信息, 用于下一个交易合约使用'''
    mj_status.save()
    current_status.delete()
    next_status.save()
    new_status.save()
    for ts in trade_status_list:
        if ts != next_status and ts != new_status:
            ts.delete()


def closeout(sts: TradeStatus, symbol: str, t_time: datetime
             ) -> TradeStatus:
    '''平仓'''
    sts.closeout(t_time)
    sts.save()
    return sts
