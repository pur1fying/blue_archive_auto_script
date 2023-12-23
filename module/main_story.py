import time

import cv2
import numpy as np

from core import color, stage, image

x = {
    'story': (107, 9, 162, 36),
    'menu': (107, 9, 162, 36),
    'choose-plot': (107, 9, 162, 36),
    'clearance': (861, 188, 983, 205),
    'current-clearance': (855, 188, 1010, 205),
    'first-lock': (1102, 225, 1131, 257),
    'plot-info': (577, 145, 640, 174),
    'plot-fight': (901, 211, 925, 236),
    'plot-attack': (107, 9, 162, 36),  # 部队出击
    'fight-parse': (1223, 32, 1243, 59),  # 战斗中暂停按钮
    'fight-confirm': (1144, 649, 1194, 674),  # 战斗结果
    'auto': (1181, 664, 1236, 689),  # 自动战斗
    'three-times': (1190, 616, 1240, 633)  # 三倍加速

}

story_position = {
    1: (350, 345), 2: (950, 345)
}


def start(self):
    if self.server == 'CN':
        # 回到首页
        home.go_home(self)
        # 点击业务区
        self.double_click(1195, 576)
        # 等待业务区页面加载
        image.compare_image(self, 'home_bus', mis_fu=self.click, mis_argv=(1195, 576))

        # 点击故事
        self.click(1093, 273)
        image.compare_image(self, 'main_story_story')

        # 点击主线故事
        self.click(248, 355)
        image.compare_image(self, 'main_story_menu')

        # 选择故事
        select_story(self)

        # 开始剧情
        start_admission(self)

        # 回到首页
        home.go_home(self)
    elif self.server == "Global":
        self.logger.info("Global server not support")


def skip_polt(self):
    """
    跳过剧情
    @param self:
    @return:
    """
    while True:
        # 等待菜单出现
        image.compare_image(self, 'cm_skip-menu')
        # 点击菜单
        self.click(1204, 40, False)
        # 点击>>
        self.click(1210, 120, False, 1, 1)
        # 等待跳过加载
        if image.compare_image(self, 'cm_confirm', 3):
            # 点击跳过
            self.click(770, 521, False)
            return


def start_admission(self):
    # 检查是否通关
    if image.compare_image(self, 'main_story_clearance', 0, 10):
        return
    # 检查是否通关
    if image.compare_image(self, 'main_story_current-clearance', 0, 10):
        return
    # 查看第一个是否锁住了
    if image.compare_image(self, 'main_story_first-lock', 10, 20):
        # 锁住了点第二个任务
        self.click(1114, 339, False)
    else:
        self.click(1114, 237, False)
    # 等待剧情信息加载
    image.compare_image(self, 'main_story_plot-info')

    is_fight = image.compare_image(self, 'main_story_plot-fight', 0, 10)

    # 进入剧情
    self.click(641, 516, False)
    # 跳过剧情
    skip_polt(self)

    if is_fight:
        # 等待部队出击页面加载
        image.compare_image(self, 'main_story_plot-attack')
        time.sleep(3)
        # 点击出击
        self.click(1158, 655, False)
        auto_fight(self)
        # 跳过剧情
        skip_polt(self)

    # 关闭获得奖励
    stage.close_prize_info(self)
    time.sleep(2)
    # 再次递归
    return start_admission(self)


def change_acc_auto(self):
    img1 = self.get_screenshot_array()
    if self.server == 'CN':
        y = 625
    elif self.server == 'Global':
        y = 575
    acc_r_ave = int(img1[y][1196][0]) // 3 + int(img1[y][1215][0]) // 3 + int(img1[y][1230][0]) // 3
    if 250 <= acc_r_ave <= 260:
        self.logger.info("CHANGE acceleration phase from 2 to 3")
        self.click(1215, y)
    elif 0 <= acc_r_ave <= 60:
        self.logger.info("ACCELERATION phase 3")
    elif 140 <= acc_r_ave <= 180:
        self.logger.info("CHANGE acceleration phase from 1 to 3")
        self.click(1215, y, wait=False,count=2)
    else:
        self.logger.warning("CAN'T DETECT acceleration BUTTON")
    if self.server == 'CN':
        y = 677
    elif self.server == 'Global':
        y = 627
    auto_r_ave = int(img1[y][1171][0]) // 2 + int(img1[y][1246][0]) // 2
    if 190 <= auto_r_ave <= 230:
        self.logger.info("CHANGE MANUAL to auto")
        self.click(1215, y,wait=False)
    elif 0 <= auto_r_ave <= 60:
        self.logger.info("AUTO")
    else:
        self.logger.warning("can't identify auto button")


def auto_fight(self):
    t_start = time.time()
    while time.time() <= t_start + 20:
        img = self.get_screenshot_array()
        if self.server == 'CN':
            if not color.judge_rgb_range(img, 831, 692, 44, 64, 197, 217, 240, 255):
                time.sleep(self.screenshot_interval)
            else:
                break
        elif self.server == 'Global':
            if not (color.judge_rgb_range(img, 831, 643, 0, 40, 150, 190, 240, 255) or color.judge_rgb_range(img, 831, 692, 0, 64, 150, 217, 240, 255)):
                time.sleep(self.screenshot_interval)
            else:
                break
    change_acc_auto(self)


def select_story(self):
    """
    选择故事
    @param self:
    @return:
    """
    story = self.tc['config']['story']
    quotient = (story - 1) // 2
    self.click(1246, 335, False, quotient, 0.5)
    zb = 1 if story % 2 == 1 else 2
    image.compare_image(self, 'main_story_choose-plot', mis_fu=self.click, mis_argv=(*story_position[zb], False))
