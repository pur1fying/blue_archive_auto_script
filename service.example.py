from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from main import Main


def main():
    main = Main(ocr_needed=["en-us", "zh-cn"], jsonify=True)  # 日服也必须要 Global，否则会崩溃
    config = ConfigSet(config_dir="default_config")  # 修改为自己的配置目录名
    baas = Baas_thread(config, None, None, None, jsonify=True)
    # 得到Logger
    # logger=baas.logger

    # 初始化数据
    baas.init_all_data()
    baas.ocr = main.ocr  # type: ignore
    # # 应用启动
    baas.thread_starter()


main()
