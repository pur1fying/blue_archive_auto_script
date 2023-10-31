import logging
import sys
import threading
from datetime import datetime

from gui.components.logger_box import LoggerBox
from debug.debugger import debugger_view

logger = logging.getLogger("logger_name")
formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
handler1 = logging.StreamHandler(stream=sys.stdout)
handler1.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler1)
logs = ''


def d(message, level=4, logger_box=None):
    global logs
    while len(logging.root.handlers) > 0:
        logging.root.handlers.pop()
    status = ['&nbsp;&nbsp;&nbsp;&nbsp;INFO', '&nbsp;WARNING', '&nbsp;&nbsp;&nbsp;ERROR', 'CRITICAL']
    statusColor = ['#2d8cf0', '#f90', '#ed3f14', '#3e0480']
    statusHtml = [
        f'<b style="color:{color};">{status}</b>'
        for color, status in zip(statusColor, status)]
    if logger_box is not None:
        # logger_box.lineEdit.scrollContentsBy(0, 100)
        adding = (f'<div style="font-family: Consolas, monospace;color:{statusColor[level - 1]};">'
                  f'{statusHtml[level - 1]} | {datetime.now()} | {message} '
                  f'</div>')
        debugger_view.content += adding
        logs += adding
        # threading.Thread(target=logger_box.emit, args=(adding,)).start()
        logger_box.emit(adding)


def line(logger_box=None):
    if logger_box is not None:
        # logger_box.lineEdit.scrollContentsBy(0, 100)
        # logger_box.lineEdit.scroll
        logger_box.emit(
            '<div style="font-family: Consolas, monospace;color:#2d8cf0;">--------------'
            '-------------------------------------------------------------'
            '-------------------</div>')
