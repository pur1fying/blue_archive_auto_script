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
            self.tr("暂无任务"): "暂无任务",
            self.tr("日常小游戏"): "日常小游戏",
            self.tr("咖啡厅邀请"): "咖啡厅邀请",

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
            self.tr("战术综合测试"): "战术综合测试",

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
            self.tr("自动清好友白名单"): "自动清好友白名单",
            self.tr("设置在定期好友清理中需要保留的好友码"): "设置在定期好友清理中需要保留的好友码",
            self.tr("帮助你自动打战术综合测试"): "帮助你自动打战术综合测试",

            # normal shop
            self.tr('初级经验书'): '初级经验书',
            self.tr('中级经验书'): '中级经验书',
            self.tr('高级经验书'): '高级经验书',
            self.tr('特级经验书'): '特级经验书',
            self.tr('初级经验珠'): '初级经验珠',
            self.tr('中级经验珠'): '中级经验珠',
            self.tr('高级经验珠'): '高级经验珠',
            self.tr('特级经验珠'): '特级经验珠',
            self.tr('随机初级神秘古物'): '随机初级神秘古物',
            self.tr('随机中级神秘古物'): '随机中级神秘古物',

            # tactical challenge shop
            self.tr('宫子神明文字x5'): '宫子神明文字x5',
            self.tr('静子神明文字x5'): '静子神明文字x5',
            self.tr('真白神明文字x5'): '真白神明文字x5',
            self.tr('纱绫神明文字x5'): '纱绫神明文字x5',
            self.tr('风香神明文字x5'): '风香神明文字x5',
            self.tr('歌原神明文字x5'): '歌原神明文字x5',
            self.tr('初级经验书x5'): '初级经验书x5',
            self.tr('中级经验书x10'): '中级经验书x10',
            self.tr('高级经验书x3'): '高级经验书x3',
            self.tr('特级经验书x1'): '特级经验书x1',
            self.tr('信用点x5k'): '信用点x5k',
            self.tr('信用点x75k'): '信用点x75k',
            self.tr('信用点x125k'): '信用点x125k',

            # server combobox
            self.tr('官服'): '官服',
            self.tr('B服'): 'B服',
            self.tr('国际服'): '国际服',
            self.tr('国际服青少年'): '国际服青少年',
            self.tr('韩国ONE'): '韩国ONE',
            self.tr('日服'): '日服',
            self.tr('Steam国际服'): 'Steam国际服',

            # patstyles combobox
            self.tr('拖动礼物'): '拖动礼物',

            # emulator combobox
            self.tr('MuMu模拟器'): 'MuMu模拟器',
            self.tr('MuMu模拟器全球版'): 'MuMu模拟器全球版',
            self.tr('蓝叠模拟器'): '蓝叠模拟器',
            self.tr('蓝叠国际版'): '蓝叠国际版',

            # then combobox
            self.tr('无动作'): '无动作', # Do Nothing
            self.tr('退出 Baas'): '退出 Baas', # Exit Baas
            self.tr('退出 模拟器'): '退出 模拟器', # Exit Emulator
            self.tr('退出 Baas 和 模拟器'): '退出 Baas 和 模拟器', # Exit Baas and Emulator
            self.tr('关机'): '关机', # Shutdown

            # attributes
            self.tr('贯穿'): '贯穿', # piercing
            self.tr('爆发'): '爆发', # explosive
            self.tr('神秘'): '神秘', # mystic
            self.tr('振动'): '振动', # sonic

            # scheduler_selector_combobox
            self.tr('开'): '开',
            self.tr('关'): '关',
            self.tr('默认'): '默认',
        }
