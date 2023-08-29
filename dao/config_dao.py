from dao.odm.future_config import FutureConfigInfo, LongConfig, ShortConfig
from dao.odm.trade_config import Account, BacktestDays, RohonAccount, TradeConfigInfo
from utils.common_tools import get_china_tz_now
from utils.config_utils import FutureConfig, SystemConfig


def get_sc_odm():
    '''返回数据库中的系统配置信息'''
    return TradeConfigInfo.objects().first()  # type: ignore


def create_sc_odm(config: SystemConfig) -> TradeConfigInfo:
    '''根据配置文件内容创建系统配置信息并保存到数据库中'''
    sc_odm = TradeConfigInfo()
    t_config = config.trade_config
    tq_config = config.tq_config
    rohon_config = config.rohon_config
    sc_odm.direction = t_config.direction  # type: ignore
    sc_odm.account_type = t_config.account_type
    sc_odm.is_backtest = t_config.is_backtest  # type: ignore
    sc_odm.strategy_ids = t_config.strategies  # type: ignore
    bd = BacktestDays()
    bd.start_date = t_config.start_date
    bd.end_date = t_config.end_date
    sc_odm.backtest_days = bd
    sc_odm.date_time = get_china_tz_now()
    tq_account = Account()
    tq_account.user_name = tq_config.user  # type: ignore
    tq_account.password = tq_config.password  # type: ignore
    rohon_account = RohonAccount()
    rohon_account.app_id = rohon_config.app_id  # type: ignore
    rohon_account.auth_code = rohon_config.auth_code  # type: ignore
    rohon_account.broker_id = rohon_config.broker_id  # type: ignore
    rohon_account.url = rohon_config.url  # type: ignore
    rohon_account.user_name = rohon_config.user_name  # type: ignore
    rohon_account.password = rohon_config.password  # type: ignore
    sc_odm.tq_account = tq_account
    sc_odm.rohon_account = rohon_account
    sc_odm.save()
    return sc_odm


def get_fc_odms() -> list[FutureConfigInfo]:
    return FutureConfigInfo.objects().order_by('symbol')  # type: ignore


def create_fc_odm(configs: list[FutureConfig]) -> list[FutureConfigInfo]:
    fc_odms = []
    for config in configs:
        fc_odm = FutureConfigInfo()
        fc_odm.symbol = config.symbol  # type: ignore
        fc_odm.is_active = bool(config.is_active)  # type: ignore
        fc_odm.name = config.name  # type: ignore
        fc_odm.open_pos_scale = config.open_pos_scale
        fc_odm.switch_days = config.switch_days  # type: ignore
        fc_odm.main_symbols = config.main_symbols  # type: ignore
        fc_odm.multiple = config.multiple  # type: ignore
        long_config = LongConfig()
        ltc = config.long_trade_config
        long_config.base_scale = ltc.base_scale  # type: ignore
        long_config.profit_start_scale_1 = ltc.profit_start_scale_1  # type: ignore
        long_config.profit_start_scale_2 = ltc.profit_start_scale_2  # type: ignore
        long_config.promote_scale_1 = ltc.promote_scale_1  # type: ignore
        long_config.promote_scale_2 = ltc.promote_scale_2  # type: ignore
        long_config.promote_target_1 = ltc.promote_target_1  # type: ignore
        long_config.promote_target_2 = ltc.promote_target_2  # type: ignore
        long_config.stop_loss_scale = ltc.stop_loss_scale  # type: ignore
        short_config = ShortConfig()
        stc = config.short_trade_config
        short_config.base_scale = stc.base_scale  # type: ignore
        short_config.profit_start_scale = stc.profit_start_scale  # type: ignore
        short_config.promote_scale = stc.promote_scale  # type: ignore
        short_config.promote_target = stc.promote_target  # type: ignore
        short_config.stop_loss_scale = stc.stop_loss_scale  # type: ignore
        fc_odm.long_config = long_config
        fc_odm.short_config = short_config
        fc_odm.save()
        fc_odms.append(fc_odm)
    return fc_odms
