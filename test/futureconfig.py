# from dao.config_service import get_db_future_configs
# from utils.config_utils import get_future_configs, get_system_config
# from headquarters.headquarters import DBA


# class TestClass:
    # def test_get_future_config(self):
    #     '''测试 get_future_configs 方法是否能够正确读取期货配置信息'''
    #     configs = get_future_configs()

    #     assert len(configs) > 0
    #     assert any(c.symbol == 'KQ.m@DCE.a' for c in configs)
    #     for c in configs:
    #         if c.symbol == 'KQ.m@DCE.a':
    #             assert c.long_trade_config.base_scale == 0.03
    #             assert c.long_trade_config.stop_loss_scale == 1
    #             assert c.long_trade_config.profit_start_scale_1 == 3
    #             assert c.long_trade_config.profit_start_scale_2 == 1.5
    #             assert c.long_trade_config.promote_scale_1 == 6
    #             assert c.long_trade_config.promote_scale_2 == 3
    #             assert c.long_trade_config.promote_target_1 == 3
    #             assert c.long_trade_config.promote_target_2 == 1
    #             assert c.short_trade_config.base_scale == 0.03
    #             assert c.short_trade_config.stop_loss_scale == 1
    #             assert c.short_trade_config.profit_start_scale == 8
    #             assert c.short_trade_config.promote_scale == 3
    #             assert c.short_trade_config.promote_target == 1

    # def test_get_future_config_in_bt(self):
    #     '''测试 get_future_configs 方法是否能够正确读取期货配置信息'''
    #     configs = get_future_configs('conf/trade_config_backtest.yaml')

    #     assert len(configs) == 32
    #     assert any(c.symbol == 'KQ.m@DCE.c' for c in configs)
    #     for c in configs:
    #         if c.symbol == 'KQ.m@DCE.c':
    #             assert c.long_trade_config.base_scale == 0.03
    #             assert c.long_trade_config.stop_loss_scale == 1
    #             assert c.long_trade_config.profit_start_scale_1 == 3
    #             assert c.long_trade_config.profit_start_scale_2 == 1.5
    #             assert c.long_trade_config.promote_scale_1 == 6
    #             assert c.long_trade_config.promote_scale_2 == 3
    #             assert c.long_trade_config.promote_target_1 == 3
    #             assert c.long_trade_config.promote_target_2 == 1
    #             assert c.short_trade_config.base_scale == 0.02
    #             assert c.short_trade_config.stop_loss_scale == 1
    #             assert c.short_trade_config.profit_start_scale == 8
    #             assert c.short_trade_config.promote_scale == 3
    #             assert c.short_trade_config.promote_target == 1

    # def test_get_future_config_db(self):
    #     '''测试 get_future_configs 方法是否能够正确读取期货配置信息'''
    #     sys_config = get_system_config()
    #     DBA(sys_config)
    #     future_configs = get_future_configs()
    #     db_configs = get_db_future_configs(future_configs)
    #     assert any(c.symbol == 'KQ.m@DCE.a' for c in db_configs)
    #     for c in db_configs:
    #         if c.symbol == 'KQ.m@DCE.a':
    #             assert c.name == '豆一'
    #             assert c.is_active
    #             assert len(c.switch_days) == 2
    #             assert c.switch_days[0] == 20
    #             assert c.switch_days[1] == 45
    #             assert len(c.main_symbols) == 3
    #             assert c.main_symbols[0] == 1
    #             assert c.main_symbols[1] == 5
    #             assert c.main_symbols[2] == 9
    #             assert c.long_config.base_scale == 0.03
    #             assert c.long_config.stop_loss_scale == 1
    #             assert c.long_config.profit_start_scale_1 == 3
    #             assert c.long_config.profit_start_scale_2 == 1.5
    #             assert c.long_config.promote_scale_1 == 6
    #             assert c.long_config.promote_scale_2 == 3
    #             assert c.long_config.promote_target_1 == 3
    #             assert c.long_config.promote_target_2 == 1
    #             assert c.short_config.base_scale == 0.03
    #             assert c.short_config.stop_loss_scale == 1
    #             assert c.short_config.profit_start_scale == 8
    #             assert c.short_config.promote_scale == 3
    #             assert c.short_config.promote_target == 1