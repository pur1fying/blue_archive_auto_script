import os
import sys

import cv2

from module.arena import x as arena_x
from module.cafe_reward import x as cafe_reward_x
from module.clear_special_task_power import x as clear_special_task_power_x
from module.create import x as create_x
from module.group import x as group_x
from module.mail import x as mail_x
from module.main_story import x as main_story_x
from module.momo_talk import x as momo_talk_x
from module.normal_task import x as normal_task_x
from module.rewarded_task import x as rewarded_task_x
from module.lesson import x as lesson_x
from module.common_shop import x as shop_x
from module.buy_ap import x as buy_ap_x
from module.collect_daily_power import x as collect_daily_power_x

iad = {

}
ibd = {

}


def init_image_data(self):
    try:
        global iad, ibd
        base_path = ''
        self.logger.info("Start initializing image data")
        if self.server == 'CN':
            ibd = {
                'work_task': collect_daily_power_x,
                'main_page': {
                    'student': (328, 654, 346, 663),
                    'cafe': (88, 651, 96, 657),  # 咖啡厅
                    'cafe-black': (88, 651, 96, 657),  # 咖啡厅(用来判断无法截图)
                    'menu': (611, 248, 670, 278),  # 右上角点击菜单
                    'bus': (107, 9, 162, 36),  # 业务区
                    'home-feature': (1203, 24, 1240, 60),  # 右上角菜单(作为主页标志)
                    'quick-home': (1215, 5, 1255, 42),  # 快速回到首页,右上
                    'login-feature': (1105, 601, 1142, 640),  # 登录界面
                    'news': (250, 85, 328, 117),  # 公告
                    'relationship-rank-up': (754, 595, 776, 647),
                    'full-notice': (563, 277, 613, 312)
                },
                'arena': arena_x,
                'cafe': cafe_reward_x,
                'group': group_x,
                'create': create_x,
                'lesson': lesson_x,
                'shop': shop_x,
                'special_task': clear_special_task_power_x,
                'rewarded_task': rewarded_task_x,
                'mail': mail_x,
                'momo_talk': momo_talk_x,
                'normal_task': normal_task_x,
                'main_story': main_story_x,
                'buy_ap': buy_ap_x,
                'plot':{
                    'menu':(1172,21, 1231,56),
                    'skip-plot-button':(1193,103, 1235,132),
                    'skip-plot-notice':(606,124, 672,160)
                }
            }
            filepath = 'src/images/CN'
        elif self.server == 'Global':
            ibd = {
                'normal_task': {
                    'SUB-mission-info': (543, 141, 736, 176),
                    'Main-mission-info': (543, 121, 743, 159),
                    'select-area': (97, 9, 255, 37),
                    'fight-complete-confirm': (1120, 646, 1222, 681),
                    'reward-acquired-confirm': (712, 643, 836, 675),
                    'task-operating-mission-info': (548, 81, 732, 116),
                    'task-info': (548, 124, 732, 153),
                    'help': (597, 111, 675, 150),
                    'mission-wait-to-begin-feature': (103, 6, 213, 42),
                    'mission-operating-feature': (10, 10, 121, 40),
                    'end-phase-notice': (595, 372, 669, 402),
                    'formation-teleport-notice': (542, 317, 625, 351),
                    'add-ally-notice': (730, 284, 846, 314),
                    'quit-mission-info':(536,142,740,182),
                    'mission-conclude-confirm':(959,641,1102,687),
                    'fight-skip': (1111, 531, 1136, 556),
                    'auto-over': (1072, 589, 1094, 611),
                }
            }
            filepath = 'src/images/Global'
        assets_dir = os.path.join(base_path, filepath)
        for dp, dns, fns in os.walk(assets_dir):
            for fn in fns:
                if not fn.endswith('.png'):
                    continue
                filepath = os.path.join(dp, fn)
                key = os.path.relpath(filepath, assets_dir)
                key = os.path.splitext(key)[0].replace(os.sep, '_')
                iad[key] = cv2.imread(filepath)

        self.logger.info("Image data successfully initialized total assets : {0}".format(len(iad)))
        return True
    except Exception as e:
        self.logger.error("Failed to initialize image data {0}".format(e))
        return False
