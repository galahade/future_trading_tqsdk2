from mongoengine import connect
import dao.trade.trade_service as t_service
import dao.config_service as c_service
from dao.odm.future_trade_excel import Trade_Tips_Book
from utils.common_tools import tz_utc_8
import logging


def get_logger():
    return logging.getLogger(__name__)


def generate_bovt_sheet_book(mongo_user=None, mongo_pasw=None,
                             dbname='future_trade', mongo_host='localhost',
                             mongo_port=27017):
    # logger = get_logger()
    if mongo_user is None:
        mongo_url = (f'mongodb://{mongo_host}:{mongo_port}/{dbname}')
    else:
        mongo_url = (f'mongodb://{mongo_user}:{mongo_pasw}'
                     f'@{mongo_host}:{mongo_port}/{dbname}')
    connect(host=mongo_url, tz_aware=True, tzinfo=tz_utc_8)

    future_configs = c_service.get_future_configs([])
    bovts = t_service.get_last_bottom_tips()
    if bovts is not None:
        trade_book = Trade_Tips_Book(dbname, future_configs, bovts)
        trade_book.finish()
