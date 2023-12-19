from typing import Union

import cv2
from core import color
import logging
from datetime import datetime
import sys


def build_next_array(patten):  # 用于kmp算法获得next数组
    next_array = [0]
    prefix_len = 0
    i = 1
    while i < len(patten):
        if patten[prefix_len] == patten[i]:
            prefix_len += 1
            next_array.append(prefix_len)
            i += 1
        else:
            if prefix_len == 0:
                next_array.append(0)
                i += 1
            else:
                prefix_len = next_array[prefix_len - 1]
    return next_array


def kmp(patten, string):  # 用于统计关键字出现的次数
    next_array = build_next_array(patten)
    i = 0
    j = 0
    cnt = 0
    len1 = len(patten)
    len2 = len(string) - 1
    while i <= len2:
        if string[i] == patten[j]:
            i += 1
            j += 1
        elif j >= 1:
            j = next_array[j - 1]
        else:
            i += 1
        if j == len1:
            cnt += 1
            j = next_array[j - 1]
    return cnt


def img_crop(img, start_row, end_row, start_col, end_col):
    img = img[start_col:end_col, start_row:end_row]
    return img


def get_x_y(target_array, template_path: str):
    # print(target_array.dtype)
    if template_path.startswith("./src"):
        template_path = template_path.replace("./src", "src")
    elif template_path.startswith("../src"):
        template_path = template_path.replace("../src", "src")
    img1 = target_array
    img2 = cv2.imread(template_path)
    # sys.stdout = open('data.log', 'w+')
    height, width, channels = img2.shape

    #    print(img2.shape)
    #    for i in range(0, height):
    #        print([x for x in img2[i, :, 0]])

    result = cv2.matchTemplate(img1, img2, cv2.TM_SQDIFF_NORMED)
    upper_left = cv2.minMaxLoc(result)[2]
    #    print(img1.shape)
    #    print(upper_left[0], upper_left[1])
    # cv2.imshow("img2", img2)

    converted = img1[upper_left[1]:upper_left[1] + height, upper_left[0]:upper_left[0] + width, :]

    #     cv2.imshow("img1", converted)
    sub = cv2.subtract(img2, converted)
    # cv2.imshow("result", cv2.subtract(img2, converted))
    # for i in range(0, height):
    #    print([x for x in converted[i, :, 0]])
    # cv2.imshow("img1", img1)
    # cv2.waitKey(0)
    location = (int(upper_left[0] + width / 2), int(upper_left[1] + height / 2))
    return location, result[upper_left[1], [upper_left[0]]]


def check_sweep_availability(img):
    if color.judge_rgb_range(img, 211, 369, 192, 212, 192, 212, 192, 212) or color.judge_rgb_range(img, 211, 402, 192,
                                                                                                   212, 192, 212, 192,
                                                                                                   212) or color.judge_rgb_range(
        img, 211, 436, 192, 212, 192, 212, 192, 212):
        return "UNAVAILABLE"
    if color.judge_rgb_range(img, 211, 368, 225, 255, 200, 255, 20, 60) and color.judge_rgb_range(img, 211, 404, 225,
                                                                                                  255, 200, 255, 20,
                                                                                                  60) and color.judge_rgb_range(
        img, 211, 434, 225, 255, 200, 255, 20, 60):
        return "AVAILABLE"
    return "UNKNOWN"


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

    def __out__(self, message: str, level: int = 4) -> None:
        """
        Output log
        :param message: log message
        :param level: log level
        :return: None
        """
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
            adding = (f'''
                    <div style="font-family: Consolas, monospace;color:{statusColor[level - 1]};">
                        {statusHtml[level - 1]} | {datetime.now()} | {message}
                    </div>
                        ''')
            self.logs += adding
            self.logger_signal.emit(adding)
        else:
            print(f'{statusHtml[level - 1]} | {datetime.now()} | {message}')

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
        self.__out__(
            '<div style="font-family: Consolas, monospace;color:#2d8cf0;">--------------'
            '-------------------------------------------------------------'
            '-------------------</div>')

