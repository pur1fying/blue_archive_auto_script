import logging
import sys

logger = logging.getLogger("logger_name")
formatter = logging.Formatter("%(asctime)20s | %(levelname)10s | %(message)s | ")
handler = logging.StreamHandler(stream=sys.stdout)
# handler2 = logging.FileHandler()
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def o_p(message, level=4):
    while len(logging.root.handlers) > 0:
        logging.root.handlers.pop()
    message = message.upper()
    if level == 1:
        logger.info(message)
    elif level == 2:
        logger.warning(message)
    elif level == 3:
        logger.error(message)
    elif level == 4:
        logger.critical(message)


o_p("log module functioning correct", 1)
