from utils import excel_utils
import sys
import logging
from utils.common import get_init_db_args

log_level = "warning"
logger = logging.getLogger(__name__)


def main():
    try:
        logger = logging.getLogger(__name__)
        logger.debug("开始将摸底数据导出")
        excel_utils.generate_bovt_sheet_book()
    except Exception as e:
        logger.exception(e)
        return str(e)


if __name__ == "__main__":
    sys.exit(main())
