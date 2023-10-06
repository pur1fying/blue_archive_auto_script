from qfluentwidgets import QConfig, ConfigItem


class ExtendConfig(QConfig):
    shopList = ConfigItem("Settings", "ShopList", [0] * 16)
    # res = [("5-53-3", 0),("3-3", 0),("3-3", 0)]
