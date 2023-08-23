from typing import List
from mongoengine import (
    Document, EmbeddedDocument, StringField, FloatField,
    BooleanField,  EmbeddedDocumentField, ListField, IntField)


class LongConfig(EmbeddedDocument):
    # 止盈止损基础比例
    base_scale: float = FloatField()  # type: ignore
    # 止损倍数
    stop_loss_scale: float = FloatField()  # type: ignore
    # 开始止盈倍数
    profit_start_scale_1: float = FloatField()  # type: ignore
    # 开始止盈2倍数
    profit_start_scale_2: float = FloatField()  # type: ignore
    # 提高止损需达到的倍数
    promote_scale_1: float = FloatField()  # type: ignore
    # 提高止损需达到的倍数2
    promote_scale_2: float = FloatField()  # type: ignore
    # 将止损提高的倍数
    promote_target_1: float = FloatField()  # type: ignore
    # 将止损提高的倍数2
    promote_target_2: float = FloatField()  # type: ignore


class ShortConfig(EmbeddedDocument):
    # 止盈止损基础比例
    base_scale: float = FloatField(required=True)  # type: ignore
    # 止损倍数
    stop_loss_scale: float = FloatField()  # type: ignore
    # 开始止盈倍数
    profit_start_scale: float = FloatField()  # type: ignore
    # 提高止损需达到的倍数
    promote_scale: float = FloatField()  # type: ignore
    # 将止损提高的倍数
    promote_target: float = FloatField()  # type: ignore


class FutureConfigInfo(Document):
    # 期货合约加交易所的表示方法
    symbol: str = StringField(unique=True, required=True)  # type: ignore
    # 是否对该品种进行交易
    is_active: bool = BooleanField(required=True)  # type: ignore
    # 合约中文名称
    name: str = StringField(required=True)  # type: ignore
    multiple: int = IntField(required=True)  # type: ignore
    # 开仓金额占粽资金的比例
    open_pos_scale: float = FloatField()  # type: ignore
    # 换月时间距离交割日的天数
    switch_days: List[int] = ListField()  # type: ignore
    # 该品种的主力合约列表
    main_symbols: List[str] = ListField()  # type: ignore
    long_config: LongConfig = EmbeddedDocumentField(
        LongConfig)  # type: ignore
    short_config: ShortConfig = EmbeddedDocumentField(
        ShortConfig)  # type: ignore
