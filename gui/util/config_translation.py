from PyQt5.QtCore import QObject


class ConfigTranslation(QObject):
    """ Contains translations of config strings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = {
            # display
            self.tr("每日特别委托"): "每日特别委托",
            self.tr("悬赏通缉"): "悬赏通缉",
            self.tr("竞技场"): "竞技场",
            self.tr("收集每日体力"): "收集每日体力",
            self.tr("收集小组体力"): "收集小组体力",
            self.tr("商店购买"): "商店购买",
            self.tr("日程"): "日程",
            self.tr("主线清除体力"): "主线清除体力",
            self.tr("自动MomoTalk"): "自动MomoTalk",
            self.tr("咖啡厅"): "咖啡厅",
            self.tr("查收邮箱"): "查收邮箱",
            self.tr("自动制造"): "自动制造",
            self.tr("收集奖励"): "收集奖励",

            # event
            self.tr("咖啡厅"): "咖啡厅",
            self.tr("日程"): "日程",
            self.tr("收集每日体力"): "收集每日体力",
            self.tr("收集小组体力"): "收集小组体力",
            self.tr("查收邮箱"): "查收邮箱",
            self.tr("商店购买"): "商店购买",
            self.tr("普通关清体力"): "普通关清体力",
            self.tr("困难关清体力"): "困难关清体力",
            self.tr("每日特别委托"): "每日特别委托",
            self.tr("悬赏通缉"): "悬赏通缉",
            self.tr("竞技场"): "竞技场",
            self.tr("自动制造"): "自动制造",
            self.tr("总力战"): "总力战",
            self.tr("自动MomoTalk"): "自动MomoTalk",
            self.tr("收集奖励"): "收集奖励",
            self.tr("学院交流会"): "学院交流会",
            self.tr("凌晨四点重启"): "凌晨四点重启",
            self.tr("活动扫荡"): "活动扫荡",

            # switch
            self.tr("新的配置"): "新的配置",
            self.tr("功能开关"): "功能开关",
            self.tr("咖啡厅"): "咖啡厅",
            self.tr("日程"): "日程",
            self.tr("商店购买"): "商店购买",
            self.tr("竞技场商店购买"): "竞技场商店购买",
            self.tr("主线清除体力"): "主线清除体力",
            self.tr("竞技场"): "竞技场",
            self.tr("自动制造"): "自动制造",
            self.tr("总力战"): "总力战",
            self.tr("扫荡及购买券设置"): "扫荡及购买券设置",

            # static
            self.tr("重要，此处为功能开关，控制各功能是否开启，启动前请检查是否开启。"): "重要，此处为功能开关，控制各功能是否开启，启动前请检查是否开启。",
            self.tr("帮助你收集咖啡厅体力和信用点"): "帮助你收集咖啡厅体力和信用点",
            self.tr("自动每日日程"): "自动每日日程",
            self.tr("商店里买东西"): "商店里买东西",
            self.tr("竞技场商店里买东西"): "竞技场商店里买东西",
            self.tr("主线关卡自动清除体力与每日困难"): "主线关卡自动清除体力与每日困难",
            self.tr("帮助你自动打竞技场"): "帮助你自动打竞技场",
            self.tr("帮助你自动制造"): "帮助你自动制造",
            self.tr("总力战期间自动打总力战"): "总力战期间自动打总力战",
            self.tr("各种扫荡及购买券次数设置"): "各种扫荡及购买券次数设置",

            # server combobox
            self.tr('官服'): '官服', 
            self.tr('B服'): 'B服', 
            self.tr('国际服'): '国际服',
            self.tr('日服'): '日服',

            # patstyles combobox
            self.tr('拖动礼物'): '拖动礼物'
            }

