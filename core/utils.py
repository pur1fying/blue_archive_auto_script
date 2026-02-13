import logging
import sys
import threading
import platform
from typing import Union
from datetime import datetime, timedelta, timezone

host_is_android = platform.system() == 'Android' or hasattr(sys, 'getandroidapilevel')

def host_platform_is_android():
    return host_is_android

if not host_platform_is_android():
    from rich.console import Console
    from rich.markup import escape
    console = Console()
else:
    console = None

def get_runtime_abi():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    context = PythonActivity.mActivity.getApplicationContext()
    native_lib_dir = context.getApplicationInfo().nativeLibraryDir
    abi_dir = os.path.basename(native_lib_dir)
    abi_map = {
        'arm64': 'arm64-v8a',
        'x86_64': 'x86_64',
        'armeabi-v7a': 'armeabi-v7a',
        'x86': 'x86',
    }
    return abi_map.get(abi_dir, abi_dir)


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
        :param logger_signal: Logger signal broadcasts log level and log message
        """
        # Init logger signal, logs and logger,
        # logger signal is used to output log to logger box or other output
        self.logs = ""
        self.logger_signal = logger_signal
        if not self.logger_signal and not host_platform_is_android():
            # if the logger signal is not configured, we use rich traceback then
            # to better display error messages in console
            from rich.traceback import install
            install(show_locals=True)
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
        :param level: log level(1: INFO, 2: WARNING, 3: ERROR, 4: CRITICAL)
        :return: None
        """
        # Keep original message for additional sinks (e.g. logcat)
        raw_message = message

        # If raw_print is True, output log to logger box
        if level < 1 or level > 4:
            raise ValueError("Invalid log level")

        if raw_print:
            self.logs += message
            if self.logger_signal:
                self.logger_signal.emit(level, message)
            # also send to logcat if on Android
            try:
                if host_platform_is_android():
                    from core.android.log import logcat
                    logcat(str(raw_message), level='INFO')
            except Exception:
                pass
            return

        while len(logging.root.handlers) > 0:
            logging.root.handlers.pop()

        levels_str = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        # If logger signal is not None, output log to logger signal
        # else output log to console
        levels_color = ["#2d8cf0", "#ff9900", "#ed3f14", "#3e0480"]
        if self.logger_signal is not None:
            self.logs += f"{levels_str[level - 1]} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {message}"
            self.logger_signal.emit(level, message)
        elif not host_platform_is_android():
            console.print(f'[{levels_color[level - 1]}]'
                          f'{levels_str[level - 1]} |'
                          f' {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |'
                          f' {escape(message)}[/]', soft_wrap=True)

        # If running on Android, also send a plain-text copy to logcat
        try:
            if host_platform_is_android():
                from core.android.log import logcat
                level_map = {1: 'INFO', 2: 'WARNING', 3: 'ERROR', 4: 'CRITICAL'}
                logcat(str(raw_message), level=level_map.get(level, 'INFO'))
        except Exception:
            # Do not let logcat failures affect normal logging
            pass

        # If running on Android, also send a plain-text copy to logcat
        try:
            if host_platform_is_android():
                from core.android.log import logcat
                level_map = {1: 'INFO', 2: 'WARNING', 3: 'ERROR', 4: 'CRITICAL'}
                logcat(str(raw_message), level=level_map.get(level, 'INFO'))
        except Exception:
            # Do not let logcat failures affect normal logging
            pass

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
        :param message: log message or Exception object

        Output error log
        """
        if isinstance(message, BaseException):
            exc_message = str(message)
            formatted_message = f"{type(message).__name__}: {exc_message}" if exc_message else type(message).__name__
            self.__out__(formatted_message, 3)
            return

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
    else:  # target_hour < current_hour
        diff = current_hour - target_hour
        if diff > 12:
            hour_delta = 24 - diff
        else:
            hour_delta = -diff

    nearest_time = (now + timedelta(hours=hour_delta)).replace(minute=0, second=0, microsecond=0)
    return nearest_time


def purchase_ticket_times_to_int(value, maxx=12):
    """
        Convert config like purchase_xxx_ticket_times to int
        Note : Origin value may be string.

        Args:
            value: Config value
            maxx: Max value
        Returns:
            int: Converted int value
    """
    if type(value) is int:
        pass
    if type(value) is str:
        try:
            value =  int(value)
        except ValueError:
            value = 0

    # purchase ticket time always over 0
    value = max(0, value)
    value = min(value, maxx)
    return value
