#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__date__ = '2023/5/5'

from tqsdk2 import TqApi, TqAuth, TqRohon

account = TqRohon(td_url="tcp://124.160.66.119:41253", broker_id="RohonDemo", app_id="MQT_MQT_1.0", auth_code="HtZfFGH0GP6xj50H", user_name="zc01", password="888888")
api = TqApi(account=account, auth=TqAuth("galahade", "211212"), debug="trade.log")
