from datetime import datetime
from mongoengine import (DateTimeField, EmbeddedDocument,
                         EmbeddedDocumentListField,
                         Document, StringField, IntField, FloatField, BooleanField)


class TqTrade(EmbeddedDocument):
    # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
    order_id: str = StringField()
    # 成交单ID
    trade_id: str = StringField()
    # 交易所单号
    exchange_trade_id: str = StringField()
    # 交易所
    exchange_id: str = StringField()
    # 交易所内的合约代码
    instrument_id: str = StringField()
    # 下单方向, BUY=买, SELL=卖
    direction: str = StringField()
    # 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
    offset: str = StringField()
    # 成交手数
    volume: int = IntField()
    # 成交价
    price: float = FloatField()
    # 下单时间
    trade_date_time: datetime = DateTimeField()


class TqOrder(Document):
    # 委托单ID, 对于一个用户的所有委托单，这个ID都是不重复的
    order_id: str = StringField()
    # 交易所单号
    exchange_order_id: str = StringField()
    # 交易所
    exchange_id: str = StringField()
    # 交易所内的合约代码
    instrument_id: str = StringField()
    # 下单方向, BUY=买, SELL=卖
    direction: str = StringField()
    # 开平标志, OPEN=开仓, CLOSE=平仓, CLOSETODAY=平今
    offset: str = StringField()
    # 总报单手数
    volume_orign: int = IntField()
    # 未成交手数
    volume_left: int = IntField()
    # 委托价格, 仅当 price_type = LIMIT 时有效
    limit_price: float = FloatField()
    # 价格类型, ANY=市价, LIMIT=限价
    price_type: str = StringField()
    # 手数条件, ANY=任何数量, MIN=最小数量, ALL=全部数量
    volume_condition: str = StringField()
    # 时间条件, IOC=立即完成，否则撤销, GFS=本节有效, GFD=当日有效, GTC=撤销前有效, GFA=集合竞价有效
    time_condition: str = StringField()
    # 下单时间
    insert_date_time: datetime = DateTimeField()
    #: 委托单状态信息
    last_msg: str = StringField()
    #: 委托单状态, ALIVE=有效, FINISHED=已完
    status: str = StringField()
    #: 委托单是否确定是错单（即下单失败，一定不会有成交）(注意，返回 False 不代表确定不是错单，有可能交易所回来的信息还在路上或者丢掉了)
    is_error: bool = BooleanField()
    #: 平均成交价
    trade_price: float = FloatField()
    # 成交单详细记录
    trade_list: list[TqTrade] = EmbeddedDocumentListField(TqTrade)
