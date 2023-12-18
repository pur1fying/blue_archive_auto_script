from common import config
from modules.baas import restart


def start(self):
    if self.server == 'CN':
        # 重启游戏
        self.log_title("开始反和谐")
        pkg = self.bc['baas']['base']['package']
        self.logger.info("开始推送反和谐文件到模拟器中...")
        # 推送文件
        self.d.push(config.get_froze_path('assets/LocalizeConfig.txt'), '/sdcard/Android/data/{0}/files/'.format(pkg))
        self.logger.info("反和谐已完成，开始重启游戏")
        restart.start(self)
    elif self.server == "Global":
        self.logger.info("Global server not support")
