import logging
import sys
import threading
import os
from typing import Union
from datetime import datetime, timedelta, timezone


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

def detach(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args[:-1], kwargs=kwargs).start()
    return wrapper

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
        
        # 创建日志目录
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 创建文件处理器
        self.file_handler = None
        self._setup_file_handler()
    
    def _setup_file_handler(self):
        """
        设置文件处理器，用于将日志输出到本地文件
        """
        # 获取当前日期作为文件名
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{current_date}.txt")
        
        # 如果已有文件处理器，先移除
        if self.file_handler and self.file_handler in self.logger.handlers:
            self.logger.removeHandler(self.file_handler)
        
        # 创建新的文件处理器
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter("%(levelname)8s |%(asctime)20s | %(message)s ")
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def __out__(self, message: str, level: int = 1, raw_print=False) -> None:
        """
        Output log
        :param message: log message
        :param level: log level
        :return: None
        """
        # 检查日期是否变更，如果变更则更新文件处理器
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{current_date}.txt")
        if not os.path.exists(log_file) or (self.file_handler and self.file_handler.baseFilename != log_file):
            self._setup_file_handler()
            
        # If raw_print is True, output log to logger box
        if raw_print:
            self.logs += message
            self.logger_signal.emit(message)
            # 将原始消息写入日志文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message.replace('<br>', '\n').replace('&nbsp;', ' ') + '\n')
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
            message_html = message.replace('\n', '<br>').replace(' ', '&nbsp;')
            adding = (f'''
                    <div style="font-family: Consolas, monospace;color:{statusColor[level - 1]};">
                        {statusHtml[level - 1]} | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {message_html}
                    </div>
                        ''')
            self.logs += adding
            self.logger_signal.emit(adding)
            
            # 将纯文本消息写入日志文件
            log_level_names = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
            log_message = f"{log_level_names[level-1]:8s} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {message}"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        else:
            print(f'{statusHtml[level - 1]} | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {message}')
            
            # 将纯文本消息写入日志文件
            log_level_names = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
            log_message = f"{log_level_names[level-1]:8s} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {message}"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')

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


def build_possible_string_dict_and_length(st_list):
    string_letter_dict = []
    string_len = []
    for st in st_list:
        string_letter_dict.append({})
        string_len.append(len(st))
        for j in range(0, len(st)):
            string_letter_dict[-1].setdefault(st[j], 0)
            string_letter_dict[-1][st[j]] += 1
    return string_letter_dict, string_len


def most_similar_string(s, possible_string_letter_dict, possible_string_length):
    """
        s : "pineapple"
        possible_string_letter_dict :
        [
            {
                "a": 1,
                "e": 1,
                "l": 1,
                "p": 2,
            }
        ]
        possible_string_length : [5]  apple
        acc = 1 + (1 - |2-1|) + 1 + 2 = 4 / 5 = 0.8
    """
    s_letter_dict = {}
    for letter in s:
        s_letter_dict.setdefault(letter, 0)
        s_letter_dict[letter] += 1

    acc = []
    for i in range(0, len(possible_string_letter_dict)):
        cnt = 0
        t = possible_string_letter_dict[i].keys()
        for letter in t:
            if letter not in s_letter_dict:
                continue
            possible_string_letter_appear_cnt = possible_string_letter_dict[i][letter]
            cnt += max(0, (possible_string_letter_appear_cnt - abs(
                s_letter_dict[letter] - possible_string_letter_appear_cnt)))
        acc.append(cnt / possible_string_length[i])

    max_acc = max(acc)
    return max_acc, acc.index(max_acc)


def get_serial_pair(serial):
    """
    Args:
        serial (str):

    Returns:
        str, str: `127.0.0.1:5555+{X}` and `emulator-5554+{X}`, 0 <= X <= 32
    """
    if serial.startswith('127.0.0.1:'):
        try:
            port = int(serial[10:])
            if 5555 <= port <= 5555 + 32:
                return f'127.0.0.1:{port}', f'emulator-{port - 1}'
        except (ValueError, IndexError):
            pass
    if serial.startswith('emulator-'):
        try:
            port = int(serial[9:])
            if 5554 <= port <= 5554 + 32:
                return f'127.0.0.1:{port + 1}', f'emulator-{port}'
        except (ValueError, IndexError):
            pass

    return None, None


def merge_nearby_coordinates(coords, abs_x=10, abs_y=10):
    coords.sort()
    groups = []
    for coord in coords:
        found_group = False
        for group in groups:
            if is_nearby_group(coord, group, abs_x, abs_y):
                group.append(coord)
                found_group = True
                break
        if not found_group:
            groups.append([coord])
    return groups


def is_nearby_group(coord, group, abs_x=10, abs_y=10):
    for p in group:
        if abs(p[0] - coord[0]) <= abs_x and abs(p[1] - coord[1]) <= abs_y:
            return True
    return False

def get_nearest_hour(target_hour):
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    if target_hour >= current_hour:
        diff = target_hour - current_hour
        if diff > 12:
            hour_delta = diff - 24
        else:
            hour_delta = diff
    else:   # target_hour < current_hour
        diff = current_hour - target_hour
        if diff > 12:
            hour_delta = 24 - diff
        else:
            hour_delta = -diff

    nearest_time = (now + timedelta(hours=hour_delta)).replace(minute=0, second=0, microsecond=0)
    return nearest_time

