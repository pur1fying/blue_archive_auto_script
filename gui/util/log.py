import logging
import sys
from datetime import datetime

from gui.components.logger_box import LoggerBox

logger = logging.getLogger("logger_name")
formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
handler1 = logging.StreamHandler(stream=sys.stdout)
handler1.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler1)


def d(message, level=4, logger_box: LoggerBox = None):
    while len(logging.root.handlers) > 0:
        logging.root.handlers.pop()
    # message = message.upper()
    # if level == 1:
    #     logger.info(message)
    # if level == 2:
    #     logger.warning(message)
    # if level == 3:
    #     logger.error(message)
    # if level == 4:
    #     logger.critical(message)
    status = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    statusColor = ['#2d8cf0', '#f90', '#ed3f14', '#3e0480']
    statusHtml = [f'<b style="color:{color}">{status}</b>' for color, status in zip(statusColor, status)]
    if logger_box is not None:
        logger_box.lineEdit.scrollContentsBy(0, 100)
        logger_box.lineEdit.append(f'{statusHtml[level - 1]} | {datetime.now()} | {message} |')


def line(logger_box: LoggerBox = None):
    if logger_box is not None:
        logger_box.lineEdit.scrollContentsBy(0, 100)
        logger_box.lineEdit.append('---------------------------------------------------------------------------'
                                   '-------------------')
