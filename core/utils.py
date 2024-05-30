import logging
import sys
import threading
from datetime import datetime
from typing import Union


def delay(wait=1):
    def decorator(func):
        timer = None  # type: Union[threading.Timer, None]

        def debounced(*args, **kwargs):
            nonlocal timer

            def call_it():
                func(*args, **kwargs)

            if timer and timer.is_alive():
                timer.cancel()

            timer = threading.Timer(wait, call_it)
            timer.start()

        return debounced

    return decorator


class Logger:
    """
    Logger class for logging
    """

    def __init__(self, logger_signal):
        """
        :param logger_signal: Logger Box signal
        """
        # Init logger box signal, logs and logger
        # logger box signal is used to output log to logger box
        self.logs = ""
        self.logger_signal = logger_signal
        self.logger = logging.getLogger("BAAS_Logger")
        formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
        handler1 = logging.StreamHandler(stream=sys.stdout)
        handler1.setFormatter(formatter)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler1)

    def __out__(self, message: str, level: int = 1, raw_print=False) -> None:
        """
        Output log
        :param message: log message
        :param level: log level
        :return: None
        """
        # If raw_print is True, output log to logger box
        if raw_print:
            self.logs += message
            self.logger_signal.emit(message)
            return

        while len(logging.root.handlers) > 0:
            logging.root.handlers.pop()
        # Status Text: INFO, WARNING, ERROR, CRITICAL
        status = ['&nbsp;&nbsp;&nbsp;&nbsp;INFO', '&nbsp;WARNING', '&nbsp;&nbsp;&nbsp;ERROR', 'CRITICAL']
        # Status Color: Blue, Orange, Red, Purple
        statusColor = ['#2d8cf0', '#f90', '#ed3f14', '#3e0480']
        # Status HTML: <b style="color:$color">status</b>
        statusHtml = [
            f'<b style="color:{_color};">{status}</b>'
            for _color, status in zip(statusColor, status)]
        # If logger box is not None, output log to logger box
        # else output log to console
        if self.logger_signal is not None:
            message = message.replace('\n', '<br>').replace(' ', '&nbsp;')
            adding = (f'''
                    <div style="font-family: Consolas, monospace;color:{statusColor[level - 1]};">
                        {statusHtml[level - 1]} | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {message}
                    </div>
                        ''')
            self.logs += adding
            self.logger_signal.emit(adding)
        else:
            print(f'{statusHtml[level - 1]} | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {message}')

    def info(self, message: str) -> None:
        """
        :param message: log message

        Output info log
        """
        self.__out__(message, 1)

    def warning(self, message: str) -> None:
        """
        :param message: log message

        Output warn log
        """
        self.__out__(message, 2)

    def error(self, message: Union[str, Exception]) -> None:
        """
        :param message: log message

        Output error log
        """
        self.__out__(message, 3)

    def critical(self, message: str) -> None:
        """
        :param message: log message

        Output critical log
        """
        self.__out__(message, 4)

    def line(self) -> None:
        """
        Output line
        """
        # While the line print do not need wrapping, we
        # use raw_print=True to output log to logger box
        self.__out__(
            '<div style="font-family: Consolas, monospace;color:#2d8cf0;">--------------'
            '-------------------------------------------------------------'
            '-------------------</div>', raw_print=True)

