from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
    queryset_manager,
)


class IndicatorValues(EmbeddedDocument):
    '''指标值'''
    meta = {'abstract': True}

    ema60 = FloatField()
    macd = FloatField()
    close = FloatField()
    kline_time: datetime = DateTimeField()  # type: ignore

    def clear(self):
        self.ema60 = 0.0
        self.macd = 0.0
        self.close = 0.0
        self.kline_time = None  # type: ignore


class BottomIndicatorValues(IndicatorValues):
    '''指标值'''
    ema5 = FloatField()
    ema20 = FloatField()

    def clear(self):
        super().clear()
        self.ema5 = 0.0
        self.ema20 = 0.0


class MainIndicatorValues(IndicatorValues):
    '''主策略的指标值'''
    ema9 = FloatField()
    ema22 = FloatField()
    open = FloatField()
    condition_id = IntField()

    def clear(self):
        super().clear()
        self.ema9 = 0.0
        self.ema22 = 0.0
        self.open = 0.0
        self.condition_id = 0


class OpenCondition(EmbeddedDocument):
    '''开仓满足的条件，包括：日线条件，3小时条件， 30分钟条件 的类型'''
    meta = {'allow_inheritance': True}
    daily_condition: IndicatorValues = EmbeddedDocumentField(
        IndicatorValues)  # type: ignore
    hourly_condition: IndicatorValues = EmbeddedDocumentField(
        IndicatorValues)  # type: ignore
    minute_30_condition: IndicatorValues = EmbeddedDocumentField(
        IndicatorValues)  # type: ignore

    def clear(self):
        self.daily_condition = None  # type: ignore
        self.hourly_condition = None  # type: ignore
        self.minute_30_condition = None  # type: ignore


class BottomOpenCondition(OpenCondition):
    daily_condition: BottomIndicatorValues = EmbeddedDocumentField(
        BottomIndicatorValues)  # type: ignore
    hourly_condition: BottomIndicatorValues = EmbeddedDocumentField(
        BottomIndicatorValues)  # type: ignore
    minute_30_condition: BottomIndicatorValues = EmbeddedDocumentField(
        BottomIndicatorValues)  # type: ignore


class MainOpenCondition(OpenCondition):
    '''主策略开仓满足的条件，包括：日线条件，3小时条件， 30分钟条件 5分钟线 等类型'''
    # 开仓条件
    daily_condition: MainIndicatorValues | None = EmbeddedDocumentField(
        MainIndicatorValues)  # type: ignore
    hourly_condition: MainIndicatorValues | None = EmbeddedDocumentField(
        MainIndicatorValues)  # type: ignore
    minute_30_condition: MainIndicatorValues | None = EmbeddedDocumentField(
        MainIndicatorValues)  # type: ignore
    minute_5_condition: MainIndicatorValues | None = EmbeddedDocumentField(
        MainIndicatorValues)  # type: ignore

    def clear(self):
        super().clear()
        self.minute_5_condition = None


class CloseCondition(EmbeddedDocument):
    '''存储平仓用到的条件'''
    meta = {'allow_inheritance': True}
    # 止盈阶段
    take_profit_stage: int = IntField(default=0)  # type: ignore
    # 该交易适用的止盈条件
    take_profit_cond: int = IntField(default=0)  # type: ignore
    # 止损价格
    stop_loss_price: float = FloatField(default=0.0)  # type: ignore
    # 是否已经提高止损价
    has_increase_slp: bool = BooleanField(default=False)  # type: ignore
    # 止损原因
    sl_reason: str = StringField(default='止损')  # type: ignore
    # 止盈监控开始价格
    tp_started_point: float = FloatField(default=0.0)  # type: ignore
    # 是否进入止盈阶段
    has_enter_tp: bool = BooleanField(default=False)  # type: ignore
    # 是否停止跟踪止盈
    has_stop_tp: bool = BooleanField(default=False)  # type: ignore

    def clear(self):
        self.take_profit_stage = 0
        self.take_profit_cond = 0
        self.stop_loss_price = 0.0
        self.has_increase_slp = False
        self.sl_reason = '止损'
        self.tp_started_point = 0.0
        self.has_enter_tp = False
        self.has_stop_tp = False


class BottomSoldCondition(CloseCondition):
    '''摸底策略的平仓条件'''


class MainSoldCondition(CloseCondition):
    '''存储平仓用到的条件'''


class TradePosBase(Document):
    '''开平仓信息的基类'''
    meta = {'abstract': True}
    # 期货合约
    symbol = StringField(required=True)
    # 交易方向：0: 做空，1: 做多
    direction = IntField(required=True, min_value=0, max_value=1)
    # 开仓价格
    trade_price: float = FloatField()  # type: ignore
    # 开仓数量
    volume = IntField()
    # 交易时间
    trade_time = DateTimeField()
    # 系统订单id
    order_id = StringField()
    last_modified = DateTimeField()


class CloseVolume(TradePosBase):
    meta = {'abstract': True}
    '''存储期货合约的平仓信息'''
    # 平仓类型 0: 止损, 1: 止盈, 2: 换月, 3: 人工平仓
    close_type = IntField()
    close_message = StringField()


class MainCloseVolume(CloseVolume):
    '''存储期货合约主策略平仓信息'''


class MainOpenVolume(TradePosBase):
    '''存储某个期货合约的开仓信息，包括：
    期货合约，交易方向，开仓价格，开仓时间，开仓订单id，开仓条件，是否平仓，平仓信息id，最后更新时间
    '''
    # 开仓条件
    open_condition = EmbeddedDocumentField(MainOpenCondition)
    # 止盈止损条件
    close_condition: CloseCondition = EmbeddedDocumentField(
        CloseCondition)  # type: ignore
    # 是否平仓
    is_close = BooleanField(required=True, default=False)
    # 平仓信息
    close_pos_infos = ListField(ReferenceField(MainCloseVolume))


class BottomOpenVolumeTip(Document):
    '''摸底策略开仓盘前提示信息'''
    id = StringField(primary_key=True)
    custom_symbol = StringField(required=True)
    # 期货合约
    symbol: str = StringField(required=True)  # type: ignore
    # 是否需要在下一交易日开仓
    need_trade: bool = BooleanField(required=True, default=False)
    # 最近一根日k线时间
    dkline_time: datetime = DateTimeField()  # type: ignore
    # 交易方向：0: 做空，1: 做多
    direction = IntField(required=True, min_value=0, max_value=1)
    # 上一交易日收盘价格
    last_price = FloatField()
    # 开仓数量
    volume = IntField()
    last_modified = DateTimeField()
    # 开仓条件
    open_condition = EmbeddedDocumentField(BottomOpenCondition)

    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.order_by('-dkline_time')

    @queryset_manager
    def get_last_tips(doc_cls, queryset):
        result = queryset.order_by('-dkline_time').first()
        if result is not None:
            return queryset.filter(dkline_time=result.dkline_time)
        return None


class BottomCloseVolume(CloseVolume):
    '''存储期货合约主策略平仓信息'''


class BottomOpenVolume(TradePosBase):
    # 盘前提示记录
    tip = ReferenceField(BottomOpenVolumeTip)
    # 是否平仓
    is_close = BooleanField(required=True, default=False)
    # 平仓信息
    close_pos_infos = ListField(ReferenceField(BottomCloseVolume))


class TradeStatus(Document):
    '''具体合约需要保存的交易状态基类'''
    meta = {
        'abstract': True,
        'indexes': [
            {
                'fields': ['symbol', 'direction'],
                'unique': True
            }
        ]}
    # 主连合约+交易策略+交易方向
    custom_symbol: str = StringField(required=True)  # type: ignore
    symbol: str = StringField(required=True)  # type: ignore
    # 交易方向：0: 做空，1: 做多
    direction: int = IntField(
        required=True, min_value=0, max_value=1)  # type: ignore
    # 交易状态：0: 未开始，1: 交易中，2: 已平仓
    trade_status: int = IntField(default=0)  # type: ignore
    # 持仓数量, 已开仓数量 - 已平仓数量
    carrying_volume: int = IntField(default=0)  # type: ignore
    # 开始交易时间
    start_time: datetime = DateTimeField()  # type: ignore
    # 结束交易时间
    end_time: datetime = DateTimeField()  # type: ignore
    last_modified: datetime = DateTimeField()  # type: ignore
    open_condition: OpenCondition = EmbeddedDocumentField(
        OpenCondition)  # type: ignore
    sold_condition: CloseCondition = EmbeddedDocumentField(
        CloseCondition)  # type: ignore
    open_pos_info: TradePosBase = ReferenceField(
        TradePosBase)  # type: ignore

    def closeout(self, end_time: datetime):
        '''平仓'''
        self.trade_status = 2
        self.carrying_volume = 0
        self.end_time = end_time
        self.open_pos_info = None  # type: ignore
        self.last_modified = end_time
        self._clear_conditions()

    def _clear_conditions(self):
        '''清除开仓和平仓条件'''
        self.open_condition.clear()
        self.sold_condition.clear()


class MainTradeStatus(TradeStatus):
    # 开仓信息
    open_condition = EmbeddedDocumentField(MainOpenCondition)  # type: ignore
    sold_condition = EmbeddedDocumentField(MainSoldCondition)  # type: ignore
    open_pos_info = ReferenceField(MainOpenVolume)  # type: ignore


class BottomTradeStatus(TradeStatus):
    # 开仓信息
    open_condition = EmbeddedDocumentField(BottomOpenCondition)  # type: ignore
    sold_condition = EmbeddedDocumentField(BottomSoldCondition)  # type: ignore
    open_pos_info = ReferenceField(BottomOpenVolume)  # type: ignore


class MainJointSymbolStatus(Document):
    '''主连合约状态的基类

    主连合约的多空方向都有一个主连合约状态，故一个双向交易的主连合约，每种策略都有两个主连合约状态
    '''
    # 主连合约+交易策略+交易方向
    custom_symbol = StringField(required=True, unique=True)
    # 主连合约
    main_joint_symbol = StringField(required=True)
    # 当前跟踪合约，有可能是当前主力合约，也有可能是上一个主力合约
    current_symbol = StringField(required=True)
    # 当前合约之后的主力合约，有可能是下一个主力合约，也有可能是当前主力合约
    next_symbol = StringField(required=True)
    # 交易方向: 0: 做空，1: 做多
    direction = IntField(required=True)
    last_modified = DateTimeField()


class SwitchSymbolTradeRecord(Document):
    '''切换合约时的交易记录
    当盘前需要换月平仓时生成该记录，用于盘中对该品种进行平仓交易
    并将平仓的结果记录在该记录中'''
    meta = {
        'indexes': [
            {
                'fields': ['custom_symbol', 'next_symbol'],
                'unique': True
            }
        ]}
    id: str = StringField(primary_key=True)
    custom_symbol: str = StringField(required=True)
    # 期货合约
    current_symbol: str = StringField(required=True)  # type: ignore
    next_symbol: str = StringField(required=True)  # type: ignore
    # 交易时间
    quote_time: datetime = DateTimeField()  # type: ignore
    # 交易方向：0: 做空，1: 做多
    direction: int = IntField(required=True, min_value=0, max_value=1)
    # 平仓完成状态：0: 未完成，1: 已完成
    current_close_status: bool = BooleanField(default=False)
    # 下一个合约是否需要开仓
    next_need_open: bool = BooleanField(default=False)
    # 下一个合约的开仓状态
    next_open_status: bool = BooleanField(default=False)
    # 换月前的交易记录
    current_open_volume_info: TradePosBase = ReferenceField(
        TradePosBase)  # type: ignore
    # 换月平仓的交易记录
    close_volume_info: TradePosBase = ReferenceField(
        TradePosBase)  # type: ignore
    # 换月开仓的交易记录
    next_open_volume_info: TradePosBase = ReferenceField(
        TradePosBase)  # type: ignore
    last_modified: datetime = DateTimeField()

    @queryset_manager
    def objects(doc_cls, queryset):
        return queryset.order_by('-quote_time')
