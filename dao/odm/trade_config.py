from datetime import datetime
from typing import List
from mongoengine import (
    EmbeddedDocument, StringField, IntField, BooleanField, FloatField,
    ListField, DateTimeField, Document, EmbeddedDocumentField)


class Account(EmbeddedDocument):
    meta = {'allow_inheritance': True}
    user_name = StringField(required=True)
    password = StringField(required=True)


class RohonAccount(Account):
    app_id = StringField()
    auth_code = StringField()
    broker_id = StringField()
    url = StringField()


class BacktestDays(EmbeddedDocument):
    start_date: datetime = DateTimeField()  # type: ignore
    end_date: datetime = DateTimeField()  # type: ignore


class TradeConfigInfo(Document):
    direction: int = IntField(required=True, default=2)  # type: ignore
    is_backtest: bool = BooleanField(
        required=True, default=False)  # type: ignore
    # 0:模拟 1:天勤实盘 2: 融航实盘
    account_type: int = IntField(required=True, default=0)  # type: ignore
    account_balance: float = FloatField(default=100000.00)  # type: ignore
    strategy_ids: List[int] = ListField(
        IntField(), default=[1, 2])  # type: ignore
    backtest_days: BacktestDays = EmbeddedDocumentField(
        BacktestDays)  # type: ignore
    tq_account: Account = EmbeddedDocumentField(Account)  # type: ignore
    rohon_account: RohonAccount = EmbeddedDocumentField(
        RohonAccount)  # type: ignore
    date_time: datetime = DateTimeField()  # type: ignore
