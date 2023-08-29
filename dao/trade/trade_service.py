import logging
from datetime import datetime, timedelta
from typing import List, Optional

from mongoengine.queryset.visitor import Q
from tqsdk2 import Order

import dao.trade.bottom_trade_dao as bdao
import dao.trade.main_trade_dao as mdao
import dao.trade.tq_dao as tqdao
import dao.trade.trade_dao as dao
import utils.common_tools as ctools
from dao.odm.future_trade import (
    BottomOpenVolume,
    BottomOpenVolumeTip,
    BottomTradeStatus,
    MainJointSymbolStatus,
    MainOpenVolume,
    MainTradeStatus,
    SwitchSymbolTradeRecord,
    TradeStatus,
)
from dao.odm.tq_odm import TqOrder
from utils.tqsdk_tools import get_chinadt_from_ns

logger = logging.getLogger(__name__)


def get_MJStatus(
    mj_symbol: str,
    current_symbol: str,
    next_symbol: str,
    direction: int,
    quote_date: str,
    strategy_name: str,
) -> MainJointSymbolStatus:
    """根据主连合约获取策略交易状态，如果不存在则在数据库中创建"""
    mjss = _get_MJStatus(mj_symbol, direction, strategy_name)
    if mjss is None:
        mjss = dao.createMainJointSymbolStatus(
            mj_symbol,
            current_symbol,
            next_symbol,
            direction,
            strategy_name,
            ctools.get_china_date_from_str(quote_date),
        )
    return mjss


def _get_MJStatus(
    mj_symbol: str, direction: int, strategy_name: str
) -> MainJointSymbolStatus | None:
    """换月时获取主连合约状态信息"""
    custom_symbol = ctools.get_custom_symbol(
        mj_symbol, bool(direction), strategy_name
    )
    mjss = dao.getMainJointSymbolStatus(custom_symbol)
    return mjss


def get_main_trade_status(
    custom_symbol: str, symbol: str, direction: int, quote_date: str
) -> MainTradeStatus:
    ts = mdao.getTradeStatus(symbol, direction)
    if ts is None:
        dt = ctools.get_china_date_from_str(quote_date)
        ts = mdao.createTradeStatus(custom_symbol, symbol, direction, dt)
    return ts


def get_bottom_trade_status(
    custom_symbol: str, symbol: str, direction: int, quote_date: str
) -> BottomTradeStatus:
    ts = bdao.getTradeStatus(symbol, direction)
    if ts is None:
        dt = ctools.get_china_date_from_str(quote_date)
        ts = bdao.createTradeStatus(custom_symbol, symbol, direction, dt)
    return ts


def del_trade_status(ts: TradeStatus):
    dao.deleteTradeStatus(ts)


def get_main_ov(symbol: str, direction: int) -> MainOpenVolume:
    """根据主连合约代码,合约代码,交易方向 返回数据库中该合约的开仓信息"""
    return mdao.getOpenVolume(symbol, direction)


def get_bottom_ov(symbol: str, direction: int) -> BottomOpenVolume:
    """根据主连合约代码,合约代码,交易方向 返回数据库中该合约的开仓信息"""
    return bdao.getOpenVolume(symbol, direction)


def open_main_pos(status: TradeStatus, order: Order):
    """将开仓信息保存至数据库，并更新合约交易状态信息"""
    o_dict = _get_odict_from_order(order)
    return mdao.openPosAndUpdateStatus(status, o_dict)  # type: ignore


def open_bottom_pos(
    status: TradeStatus, order: Order, bovt: BottomOpenVolumeTip
):
    """将开仓信息保存至数据库，并更新合约交易状态信息"""
    o_dict = _get_odict_from_order(order)
    return bdao.openPosAndUpdateStatus(status, o_dict, bovt)  # type: ignore


def close_ops(status: TradeStatus, c_type: int, c_message: str, order: Order):
    """平仓，将合约交易状态信息重置为初始状态"""
    c_dict = _get_cdict_from_order(order, c_type, c_message)
    if isinstance(status, MainTradeStatus):
        return mdao.closePosAndUpdateStatus(status, c_dict)
    elif isinstance(status, BottomTradeStatus):
        return bdao.closePosAndUpdateStatus(status, c_dict)


def update_switch_symbol_trade_record(record: SwitchSymbolTradeRecord):
    """更新换月交易记录"""
    dao.updateSwitchSymbolTradeRecord(record)


def get_switch_symbol_trade_record(
    status: TradeStatus,
) -> SwitchSymbolTradeRecord:
    """获取换月交易记录"""
    try:
        return dao.getSwitchSymbolTradeRecord(
            status.custom_symbol, status.symbol
        )
    except Exception as e:
        logger.warning("获取换月交易记录失败", e)
        return None


def switch_symbol(
    mj_status: MainJointSymbolStatus,
    current_status: TradeStatus,
    next_status: TradeStatus,
    quote_date: str,
):
    """
    如果合约在交易中，将该合约交易信息记录到换月交易信息表中。
    更新主连合约状态表。
    删除当前合约状态信息记录
    """
    last_modified = datetime.now()
    mj_status.last_modified = last_modified
    # 为防止在数据库中的下一个交易状态与根据系统计算出的不一致，这里重新获取
    # 如果不一致，则在最后将前一个交易状态清除。
    if isinstance(current_status, MainTradeStatus):
        next_status = get_main_trade_status(
            mj_status.custom_symbol,
            mj_status.current_symbol,
            current_status.direction,
            quote_date,
        )
    elif isinstance(current_status, BottomTradeStatus):
        next_status = get_bottom_trade_status(
            mj_status.custom_symbol,
            mj_status.current_symbol,
            current_status.direction,
            quote_date,
        )
    if current_status.trade_status == 1:
        dao.createSwitchSymbolTradeRecord(
            current_status,
            next_status,
            ctools.get_china_date_from_str(quote_date),
        )
    next_status.last_modified = last_modified
    new_status = None
    if isinstance(current_status, MainTradeStatus):
        new_status = get_main_trade_status(
            mj_status.custom_symbol,
            mj_status.next_symbol,
            current_status.direction,
            quote_date,
        )
        mdao.switch_symbol(mj_status, current_status, next_status, new_status)
    elif isinstance(current_status, BottomTradeStatus):
        new_status = get_bottom_trade_status(
            mj_status.custom_symbol,
            mj_status.next_symbol,
            current_status.direction,
            quote_date,
        )
        bdao.switch_symbol(mj_status, current_status, next_status, new_status)


def _get_cdict_from_order(order: Order, c_type: int, c_message: str) -> dict:
    """从order对象中获取交易信息"""
    return {
        "trade_price": order.trade_price,
        "volume": order.volume_orign,
        "trade_time": get_chinadt_from_ns(order.insert_date_time),
        "order_id": order.order_id,
        "close_type": c_type,
        "close_message": c_message,
    }


def _get_odict_from_order(order: Order) -> dict:
    """从order对象中获取交易信息"""
    return {
        "trade_price": order.trade_price,
        "volume": order.volume_orign,
        "trade_time": get_chinadt_from_ns(order.insert_date_time),
        "order_id": order.order_id,
    }


def store_b_open_volume_tip(
    status: BottomTradeStatus, pos: int
) -> BottomOpenVolumeTip:
    """将开仓信息保存至数据库，并更新合约交易状态信息"""
    return bdao.createOpenVolumeTip(status, pos)


def update_trade_status(status: TradeStatus, update_time: datetime):
    """更新合约交易状态信息"""
    status.last_modified = update_time
    dao.updateTradeStatus(status)


def get_last_bottom_tips() -> Optional[List[BottomOpenVolumeTip]]:
    """获取最近的开仓提示信息"""
    return BottomOpenVolumeTip.get_last_tips()  # type: ignore


def get_last_bottom_tips_by_symbol(
    symbol: str, direction: int
) -> Optional[BottomOpenVolumeTip]:
    queryset = None
    try:
        queryset = get_last_bottom_tips()
    except Exception:
        pass
    if queryset is not None:
        return queryset.filter(Q(symbol=symbol) & Q(direction=direction)).first()  # type: ignore
    return None


def get_last7d_count(bovt: BottomOpenVolumeTip) -> int:
    """获取最近7天的开仓提示数量"""
    return BottomOpenVolumeTip.objects(
        Q(symbol=bovt.symbol)
        & Q(direction=bovt.direction)
        & Q(dkline_time__gte=bovt.dkline_time - timedelta(days=7))
    ).count()  # type: ignore


def store_tq_order(order: Order) -> TqOrder:
    return tqdao.createTqOrder(order)
