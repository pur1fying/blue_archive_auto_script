import logging
import sys


logger = logging.getLogger("logger_name")
formatt = logging.Formatter("%(asctime)20s | %(levelname)10s | %(message)s | ")
handler1 = logging.StreamHandler(stream=sys.stdout)
# handler2 = logging.FileHandler()
handler1.setFormatter(formatt)
logger.setLevel(logging.INFO)
logger.addHandler(handler1)


def o_p(message, level=4):
    message = message.upper()
    if level == 1:
        logger.info(message)
    if level == 2:
        logger.warning(message)
    if level == 3:
        logger.error(message)
    if level == 4:
        logger.critical(message)


o_p("log module functioning correct", 1)
