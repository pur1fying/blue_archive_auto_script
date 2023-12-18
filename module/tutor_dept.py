from common import image, color, stage
from modules.baas import home

x = {
    'title': (108, 9, 161, 37),
    'entry': (1172, 172, 1210, 205),
}


def start(self):
    # 回到首页
    home.go_home(self)

    # 等待活动入口加载
    image.compare_image(self, 'tutor_dept_entry')

    # 点击活动页
    self.click(1191, 198, False)

    # 等待活动页加载
    image.compare_image(self, 'tutor_dept_title')

    # 一键领取
    while color.check_rgb_similar(self, (1066, 600, 1067, 601), (74, 236, 252)):
        self.click(1146, 599, False)
        stage.close_prize_info(self)

    # 回到首页
    home.go_home(self)
