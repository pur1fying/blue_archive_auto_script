from common import ocr, image
from modules.baas import home, fhx, restart


def to_options(self):
    """
    进入选项
    """


def check_english(self):
    home.go_home(self)
    to_options(self)


def check(self):
    """
    检查环境
    @param self:
    """
    if self.server == "CN":
        check_ss(self)
        check_resolution(self)
        check_clarity(self)
        check_fhx(self)
    elif self.server == "Global":
        check_english(self)


def check_ss(self):
    self.log_title("️开始截图测试")
    app = self.d.app_current()
    if app['package'] != self.bc['baas']['base']['package']:
        restart.only_start(self)
    if image.compare_image(self, 'home_cafe-black', 2):
        self.exit(
            "模拟器设置有误! 如果是mumu模拟器，打开模拟器设置 -> 其他 -> 其他设置 -> 取消勾选(应用运行 -> 后台挂机时保持活跃运行) ")


def check_resolution(self):
    """
    检查分辨率
    @param self:
    @return:
    """
    self.log_title("️开始检查分辨率")
    ss = self.d.screenshot()
    if (ss.size[0] == 1280 and ss.size[1] == 720) or (ss.size[1] == 1280 and ss.size[0] == 720):
        return
    self.exit("分辨率必须为 1280 * 720,当前分辨率为:{0} * {1}".format(ss.size[0], ss.size[1]))


def check_clarity(self):
    """
    开始检查清晰度
    @param self:
    @return:
    """
    self.log_title("️开始检查清晰度")
    home.go_home(self)
    # 点击桃信
    self.double_click(170, 144)
    # 等待桃信页面加载
    ocr.screenshot_check_text(self, '成员', (226, 167, 277, 189), before_wait=1)
    self.latest_img_array = self.get_screenshot_array()
    for i in range(1, 5):
        if image.compare_image(self, 'momo_talk_peach{0}'.format(i), 0, screenshot=self.latest_img_array,
                               need_log=False):
            if i == 1:
                return home.go_home(self)
            self.logger.error("游戏分辨率太低! 打开BA->选项->图像-> 分辨率:最高 后期处理:ON 抗锯齿:ON")
            home.go_home(self)
            # 点击右上角
            self.click(1223, 40)
            ocr.screenshot_check_text(self, '菜单', (611, 248, 670, 278))
            # 选项
            self.click(535, 340)
            ocr.screenshot_check_text(self, '选项', (605, 130, 677, 167))
            # 点击图像
            self.click(289, 277)
            ocr.screenshot_check_text(self, '分辨率', (421, 213, 486, 237))
            # 点击最高
            self.click(432, 280)
            return check_clarity(self)
    home.go_home(self)


def check_fhx(self):
    self.log_title("开始检查反和谐")
    home.go_home(self)
    if ocr.screenshot_check_text(self, '等级', (31, 28, 71, 48), 1):
        self.logger.error("检测到未开启反和谐")
        fhx.start(self)
        return check_fhx(self)
