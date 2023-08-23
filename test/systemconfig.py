# from utils.common_tools import get_china_tz_time_from_str
# from utils.config_utils import get_system_config
# from dao.config_service import get_db_system_config
# from headquarters.headquarters import DBA


# class TestClass:
    # def test_get_system_config(self):
    #     config = get_system_config()
    #     assert config.tq_config.user == 'galahade'
    #     assert config.trade_config.direction == 2
    #     assert len(config.trade_config.strategies) == 2
    #     assert config.trade_config.strategies[0] == 1

    # def test_systemconfig_db(self):
    #     '''测试 get_db_system_config 方法是否能够正确读取系统配置信息'''
    #     config = get_system_config()
    #     DBA(config)
    #     db_config = get_db_system_config(config)
    #     assert db_config.direction == 2
    #     assert db_config.is_backtest is False
    #     assert len(db_config.strategies) == 2
    #     assert db_config.strategies[0] == 1
    #     assert db_config.backtest_days.start_date == (
    #         get_china_tz_time_from_str('2018-01-01 00:00:00'))
    #     assert db_config.backtest_days.end_date == (
    #         get_china_tz_time_from_str('2022-12-31 00:00:00'))
    #     assert db_config.tq_account.user_name == 'galahade'
    #     assert db_config.account_type == 0
