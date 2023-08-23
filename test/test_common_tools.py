from datetime import datetime
from utils.common_tools import (
    get_china_date_from_str, get_custom_symbol, get_next_symbol, tz_utc_8
)
from strategies.tools import is_trading_time
from tqsdk import TqApi, TqAuth, TqSim


class TestClass:

    def test_get_next_symbol(self):
        next_symbol = get_next_symbol('DCE.a2307', [1, 3, 5, 7, 9, 11])
        assert next_symbol == 'DCE.a2309'
        next_symbol = get_next_symbol('DCE.a2309', [1, 5, 9])
        assert next_symbol == 'DCE.a2401'
        next_symbol = get_next_symbol('SHFE.ag2308', [6, 8, 12])
        assert next_symbol == 'SHFE.ag2312'
        next_symbol = get_next_symbol('SHFE.hc2310', [1, 5, 10])
        assert next_symbol == 'SHFE.hc2401'

    def test_get_datetime_from_str(self):
        date = get_china_date_from_str('2021-01-01 00:00:00.000000')
        assert date == datetime(2021, 1, 1, 0, 0, 0, 0, tzinfo=tz_utc_8)

    def test_get_custom_symbol(self):
        cs = get_custom_symbol('KQ.m@DCE.a', bool(0), 'main')
        assert cs == 'DCE_a_main_short'

    def test_is_trading_time(self):
        # api = TqApi(auth=TqAuth('galahade', '211212'))
        api = TqApi(auth=TqAuth("galahade", "211212"))
        quote = api.get_quote("KQ.m@DCE.i")
        # klines = api.get_kline_serial("SHFE.rb2309", 60)
        # result = is_trading_time(api, 'KQ.m@DCE.a')
        # assert result is False
