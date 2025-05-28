EVENT_DEFAULT_CONFIG = """
[
  {
    "enabled": true,
    "priority": -2,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "凌晨四点重启",
    "func_name": "restart",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": -1,
    "interval": 0,
    "daily_reset": [[6, 0, 0], [20, 0, 0]],
    "next_tick": 0,
    "event_name": "竞技场",
    "func_name": "arena",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 10800,
    "daily_reset": [[8, 0, 0], [20, 0, 0]],
    "next_tick": 0,
    "event_name": "咖啡厅",
    "func_name": "cafe_reward",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": false,
    "priority": 0,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "1号咖啡厅邀请",
    "func_name": "no1_cafe_invite",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": false,
    "priority": 0,
    "interval": 0,
    "daily_reset": [[8, 0, 0]],
    "next_tick": 0,
    "event_name": "2号咖啡厅邀请",
    "func_name": "no2_cafe_invite",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 1,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "日程",
    "func_name": "lesson",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 2,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "收集小组体力",
    "func_name": "group",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 3,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "查收邮箱",
    "func_name": "mail",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 4,
    "interval": 0,
    "daily_reset": [[10, 0, 1], [20, 0, 0]],
    "next_tick": 0,
    "event_name": "收集每日体力",
    "func_name": "collect_daily_power",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 5,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "商店购买",
    "func_name": "common_shop",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 6,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "竞技场商店购买",
    "func_name": "tactical_challenge_shop",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 7,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "悬赏通缉",
    "func_name": "rewarded_task",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 8,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "普通关清体力",
    "func_name": "normal_task",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 9,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "困难关清体力",
    "func_name": "hard_task",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 10,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "学院交流会",
    "func_name": "scrimmage",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 11,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "每日特别委托",
    "func_name": "clear_special_task_power",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 12,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "自动制造",
    "func_name": "create",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": false,
    "priority": 13,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "总力战",
    "func_name": "total_assault",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 14,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "活动扫荡",
    "func_name": "activity_sweep",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 15,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "收集奖励",
    "func_name": "collect_reward",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 16,
    "interval": 10800,
    "daily_reset": [],
    "next_tick": 0,
    "event_name": "自动MomoTalk",
    "func_name": "momo_talk",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 17,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "日常小游戏",
    "func_name": "dailyGameActivity",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": false,
    "priority": 18,
    "interval": 3600,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "清理好友",
    "func_name": "friend",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  },
  {
    "enabled": true,
    "priority": 19,
    "interval": 0,
    "daily_reset": [[20, 0, 0]],
    "next_tick": 0,
    "event_name": "综合战术测试",
    "func_name": "joint_firing_drill",
    "disabled_time_range": [],
    "pre_task": [],
    "post_task": []
  }
]
"""

DISPLAY_DEFAULT_CONFIG = """
{
  "running": "Empty",
  "queue": [
    "每日特别委托",
    "悬赏通缉",
    "竞技场",
    "收集每日体力",
    "收集小组体力",
    "商店购买",
    "日程",
    "主线清除体力",
    "自动MomoTalk",
    "咖啡厅",
    "查收邮箱",
    "自动制造",
    "收集奖励"
  ]
}
"""

DEFAULT_CONFIG = """
{
    "name": "新的配置",
    "purchase_arena_ticket_times": "0",
    "screenshot_interval": "0.3",
    "autostart": false,
    "then": "无动作",
    "program_address": "None",
    "open_emulator_stat": false,
    "emulator_wait_time": "180",
    "ArenaLevelDiff": 0,
    "ArenaComponentNumber": 1,
    "maxArenaRefreshTimes": 10,
    "createPriority_phase1": "",
    "createPriority_phase2": "",
    "createPriority_phase3": "",
    "create_phase_1_select_item_rule": "default",
    "create_phase_2_select_item_rule": "default",
    "create_phase_3_select_item_rule": "default",
    "create_phase": 1,
    "create_item_holding_quantity": {

    },
    "use_acceleration_ticket": false,
    "createTime": "3",
    "last_refresh_config_time": "0",
    "alreadyCreateTime": "0",
    "totalForceFightDifficulty": "NORMAL",
    "hardPriority": "1-1-1",
    "unfinished_hard_tasks": [],
    "mainlinePriority": "5-1-1",
    "unfinished_normal_tasks": [],
    "main_story_regions": "",
    "rewarded_task_times": "2,2,2",
    "purchase_rewarded_task_ticket_times": "0",
    "special_task_times": "1,1",
    "purchase_scrimmage_ticket_times": "0",
    "scrimmage_times": "2,2,2",
    "patStyle": "拖动礼物",
    "antiHarmony": true,
    "bannerVisibility": true,
    "push_after_error":false,
    "push_after_completion":false,
    "push_json":"",
    "push_serverchan":"",
    "cafe_reward_lowest_affection_first": true,
    "cafe_reward_invite1_criterion" : "starred",
    "favorStudent1": [
        "爱丽丝"
    ],
    "cafe_reward_invite1_starred_student_position" : 1,
    "cafe_reward_has_no2_cafe": false,
    "cafe_reward_collect_hour_reward": true,
    "cafe_reward_invite2_criterion" : "starred",
    "favorStudent2": [
        "爱丽丝(女仆)"
    ],
    "cafe_reward_invite2_starred_student_position" : 1,
    "cafe_reward_use_invitation_ticket": true,
    "cafe_reward_allow_duplicate_invite": false,
    "cafe_reward_allow_exchange_student": false,
    "cafe_reward_interaction_shot_delay": 1.0,
    "server": "官服",
    "control_method" : "uiautomator2",
    "screenshot_method" : "uiautomator2",
    "adbIP": "127.0.0.1",
    "adbPort": "5555",
    "lesson_times": [
        1,
        1,
        1,
        1,
        1,
        1
    ],
    "lesson_enableInviteFavorStudent": false,
    "lesson_favorStudent": ["Aris (Maid)", "Aris"],
    "lesson_relationship_first": false,
    "lesson_each_region_object_priority": [
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"],
        ["primary","normal","advanced","superior"]
    ],
    "purchase_lesson_ticket_times": "0",
    "explore_normal_task_list": [],
    "explore_hard_task_list": [],
    "emulatorIsMultiInstance": false,
    "emulatorMultiInstanceNumber": 0,
    "multiEmulatorName": "mumu",
    "manual_boss": false,
    "choose_team_method": "preset",
    "side_team_attribute": [["Unused","Unused","Unused","Unused"]],
    "preset_team_attribute": [
        ["Unused","Unused","Unused","Unused","Unused"],
        ["Unused","Unused","Unused","Unused","Unused"],
        ["Unused","Unused","Unused","Unused","Unused"],
        ["Unused","Unused","Unused","Unused","Unused"]
    ],
    "burst1": "1",
    "burst2": "2",
    "pierce1": "1",
    "pierce2": "2",
    "mystic1": "1",
    "mystic2": "2",
    "shock1": "2",
    "shock2": "3",
    "activity_sweep_task_number": 1,
    "activity_sweep_times": "0",
    "TacticalChallengeShopRefreshTime": "0",
    "TacticalChallengeShopList": [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
    ],
    "CommonShopRefreshTime": "0",
    "CommonShopList": [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0
    ],
    "clear_friend_white_list": [],
    "drill_difficulty_list": [1,1,1],
    "drill_fight_formation_list": [1,2,3],
    "drill_enable_sweep": true,
    "new_event_enable_state": "default",
    "ap": {
        "count": -1,
        "max": -1,
        "time": 0
    },
    "creditpoints": {
        "count": -1,
        "time": 0
    },
    "pyroxene": {
        "count": -1,
        "time": 0
    },
    "tactical_challenge_coin": {
        "count": -1,
        "time": 0
    },
    "bounty_coin": {
        "count": -1,
        "time": 0
    },
    "assetsVisibility": true
}
"""

SWITCH_DEFAULT_CONFIG = '''
[
    {
        "config": "cafeInvite",
        "name": "咖啡厅",
        "sort": 1,
        "tip": "帮助你收集咖啡厅体力和信用点",
        "type": "TextSettingCard"
    },
    {
        "config": "schedulePriority",
        "name": "日程",
        "sort": 2,
        "tip": "自动每日日程",
        "type": "TextSettingCard"
    },
    {
        "config": "shopPriority",
        "name": "商店购买",
        "sort": 6,
        "tip": "商店里买东西",
        "type": "CheckboxSettingCard"
    },
    {
        "config": "arenaShopPriority",
        "name": "竞技场商店购买",
        "sort": 7,
        "tip": "竞技场商店里买东西",
        "type": "CheckboxSettingCard"
    },
    {
        "config": "mainlinePriority",
        "name": "主线清除体力",
        "sort": 8,
        "tip": "主线关卡自动清除体力与每日困难",
        "type": "StageSettingCard"
    },
    {
        "config": "arenaPriority",
        "name": "竞技场",
        "sort": 11,
        "tip": "帮助你自动打竞技场",
        "type": "ComboSettingCard"
    },
    {
        "config": "createPriority",
        "name": "自动制造",
        "sort": 12,
        "tip": "帮助你自动制造",
        "type": "ComboSettingCard"
    },
    {
        "config": "totalForceFightPriority",
        "name": "总力战",
        "sort": 13,
        "tip": "总力战期间自动打总力战",
        "type": "BasicSettingCard"
    },
    {
        "config": "sweepCountConfig",
        "name": "扫荡及购买券设置",
        "sort": 14,
        "tip": "各种扫荡及购买券次数设置",
        "type": "BasicSettingCard"
    },
    {
        "config": "friendWhiteList",
        "name": "自动清好友白名单",
        "sort": 15,
        "tip": "设置在定期好友清理中需要保留的好友码",
        "type": "BasicSettingCard"
    },
    {
        "config": "drillConfig",
        "name": "战术综合测试",
        "sort": 16,
        "tip": "帮助你自动打战术综合测试",
        "type": "BasicSettingCard"
    }
]

'''
STATIC_DEFAULT_CONFIG = '''
{
    "main_story_final_episode_num": 6,
    "main_story_available_episodes": {
        "CN": [2, 3, 4, 5, 6],
        "Global": [1, 2, 3, 4, 5, 6, 7, 8],
        "JP": [1, 2, 3, 4, 5, 6, 7, 8]
    },
    "max_region": {
        "CN": 23,
        "Global": 27,
        "JP": 28
    },
    "explore_normal_task_region_range": [4, 28],
    "explore_hard_task_region_range": [1, 28],
    "screenshot_methods" : ["adb", "nemu", "uiautomator2", "scrcpy"],
    "control_methods" : ["adb", "nemu", "uiautomator2", "scrcpy"],
    "common_shop_price_list": {
        "CN": [
            ["初级经验书", 12500, "creditpoints"],["中级经验书", 125000, "creditpoints"],["高级经验书", 300000, "creditpoints"],["特级经验书",500000,"creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 20000, "creditpoints"],["中级经验珠", 80000, "creditpoints"],["高级经验珠", 192000, "creditpoints"],["特级经验珠", 258000, "creditpoints"],
            ["随机初级神秘古物", 8000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"]
        ],
        "Global": [
            ["初级经验书", 12500, "creditpoints"],["中级经验书", 125000, "creditpoints"],["高级经验书", 300000, "creditpoints"],["特级经验书", 500000, "creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 20000, "creditpoints"],["中级经验珠", 80000, "creditpoints"],["高级经验珠", 192000, "creditpoints"],["特级经验珠", 256000, "creditpoints"],
            ["一包强化珠α", 110000, "creditpoints"],["一包强化珠β", 240000, "creditpoints"],["一包强化珠γ", 384000, "creditpoints"],["一包强化珠δ", 496000, "creditpoints"],
            ["随机初级神秘古物", 8000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],
            ["随机初级神秘古物", 8000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"]
        ],
        "JP": [
            ["初级经验书", 12500, "creditpoints"],["中级经验书", 125000, "creditpoints"],["高级经验书", 300000, "creditpoints"],["特级经验书", 500000, "creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 20000, "creditpoints"],["中级经验珠", 80000, "creditpoints"],["高级经验珠", 192000, "creditpoints"],["特级经验珠", 256000, "creditpoints"],
            ["一包强化珠α", 110000, "creditpoints"],["一包强化珠β", 240000, "creditpoints"],["一包强化珠γ", 384000, "creditpoints"],["一包强化珠δ", 496000, "creditpoints"],
            ["随机初级神秘古物", 8000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],
             ["随机初级神秘古物", 8000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"]
        ]
    },
    "tactical_challenge_shop_price_list": {
        "CN": [
            ["静子神明文字x5",50],["真白神明文字x5",50],["纱绫神明文字x5",50],["风香神明文字x5",50],
            ["歌原神明文字x5",50],["30AP", 15],["60AP", 30], ["初级经验书x5", 5],
            ["中级经验书x10", 25],["高级经验书x3", 60],["特级经验书x1", 100],["信用点x5k", 4],
            ["信用点x5k", 20],["信用点x75k", 60],["信用点x125k", 10]
        ],
        "Global": [
             ["宫子神明文字x5",50],["静子神明文字x5",50],["真白神明文字x5",50],["纱绫神明文字x5",50],
             ["风香神明文字x5",50],["歌原神明文字x5",50],["30AP", 15],["60AP", 30],
             ["初级经验书x5", 5],["中级经验书x10", 25],["高级经验书x3", 60],["特级经验书x1", 100],
             ["信用点x5k", 4],["信用点x5k", 20],["信用点x75k", 60],["信用点x125k", 10]
        ],
        "JP": [
             ["宫子神明文字x5", 50],  ["静子神明文字x5",50],    ["真白神明文字x5",50],    ["纱绫神明文字x5",50],
             ["风香神明文字x5",50],   ["歌原神明文字x5",50],    ["30AP", 15],           ["60AP", 30],
             ["初级经验书x5", 5],     ["中级经验书x10", 25],    ["高级经验书x3", 60],    ["特级经验书x1", 100],
             ["信用点x5k", 4],       ["信用点x5k", 20],       ["信用点x75k", 60],      ["信用点x125k", 100]
        ]
    },
    "create_default_priority": {
      "CN": {
        "phase1": [
             "花",
             "桃桃朋友咖啡厅",
             "阿拜多斯讲堂主题",
             "游戏开发部主题",
             "果冻游戏中心",
             "情人节",
             "夏日",
             "万圣节",
             "温泉浴场",
             "新年",
             "色彩",
             "军事露营组合",
             "海滩组合",
             "大运动会主题",
             "灿烂",
             "武器部件",
             "铜",
             "光芒",
             "玲珑",
             "白金",
             "黄金",
             "白银",
             "金属",
             "隐然"
        ],
        "phase2": [
            "花",
            "牡丹",
            "牵牛花",
            "玫瑰",
            "郁金香",
            "樱花",
            "水仙花",
            "紫薇花",
            "蒲公英",
            "百合花",
            "金盏花",
            "桔梗花",
            "木莲花",
            "杜鹃花",
            "翡翠花",
            "灿烂",
            "光芒",
            "色彩",
            "桃桃朋友咖啡厅",
            "果冻游戏中心",
            "情人节",
            "夏日",
            "万圣节",
            "温泉浴场",
            "新年",
            "军事露营组合",
            "海滩组合",
            "大运动会主题",
            "红色",
            "黄色",
            "褐色",
            "橘黄色",
            "粉色",
            "灰色",
            "黑色",
            "浅绿色",
            "青绿色",
            "白色",
            "紫色",
            "百鬼夜行",
            "红冬",
            "崔尼蒂",
            "歌赫娜",
            "阿拜多斯",
            "千禧年",
            "山海经",
            "瓦尔基里",
            "阿里乌斯",
            "金属",
            "白银",
            "黄金",
            "白金",
            "铜",
            "武器部件",
            "玲珑"
        ],
        "phase3": [
            "钻石",
            "神秘",
            "花",
            "灿烂",
            "闪亮",
            "颜色",
            "富足",
            "银",
            "金",
            "白金",
            "铜",
            "武器部件",
            "百鬼夜行",
            "红冬",
            "崔尼蒂",
            "歌赫娜",
            "阿拜多斯",
            "千禧年",
            "山海经",
            "瓦尔基里",
            "阿里乌斯"
        ]
      },
      "Global": {
        "phase1": [
          "Flower",
          "Momo Friends Cafe Set",
          "Jellies Arcade Set",
          "Valentine's Set",
          "Summer Pool Party Set",
          "Jack-O-Lantern Cafe Set",
          "Hot Springs Resort Set",
          "New Year's House Set",
          "Military Campground Set",
          "Beachside Set",
          "Field Day Set",
          "Abydos Classroom Set",
          "Game Development Department Set",
          "Sunshine Resort Set",
          "Shopping Mall Set",
          "Gehenna Party Set",
          "Trinity Classroom Set",
          "DJ Party Venue Set",
          "Colorful",
          "Radiant",
          "Parts",
          "Copper",
          "Platinum",
          "Gold",
          "Silver",
          "Metal",
          "Shiny",
          "Brilliant",
          "Subtle"
        ],
        "phase2": [
          "Flower",
          "Peony",
          "Morning Glory",
          "Rose",
          "Tulip",
          "Cherry Blossom",
          "Daffodil",
          "Zinnia",
          "Dandelion",
          "Lily",
          "Marigold",
          "Bellflower",
          "Magnolia",
          "Azalea",
          "Jade Blossom",
          "Radiant",
          "Shiny",
          "Colorful",
          "Momo Friends Cafe Set",
          "Jellies Arcade Set",
          "Valentine's Set",
          "Summer Pool Party Set",
          "Jack-O-Lantern Cafe Set",
          "Hot Springs Resort Set",
          "New Year's House Set",
          "Military Campground Set",
          "Beachside Set",
          "Field Day Set",
          "Abydos Classroom Set",
          "Game Development Department Set",
          "Sunshine Resort Set",
          "Shopping Mall Set",
          "Gehenna Party Set",
          "Trinity Classroom Set",
          "DJ Party Venue Set",
          "Red",
          "Yellow",
          "Brown",
          "Orange",
          "Pink",
          "Gray",
          "Black",
          "Yellow-Green",
          "Turquoise",
          "White",
          "Purple",
          "Hyakkiyako",
          "Red Winter",
          "Trinity",
          "Gehenna",
          "Abydos",
          "Millennium",
          "Shanhaijing",
          "Valkyrie",
          "Arius",
          "Metal",
          "Silver",
          "Gold",
          "Platinum",
          "Copper",
          "Weapon Parts",
          "Brilliant"
        ],
        "phase3": [
          "Diamond",
          "Mystic",
          "Flower",
          "Radiant",
          "Shiny",
          "Colorful",
          "Abundance",
          "Silver",
          "Gold",
          "Platinum",
          "Copper",
          "Weapon Parts",
          "Hyakkiyako",
          "Red Winter",
          "Trinity",
          "Gehenna",
          "Abydos",
          "Millennium",
          "Shanhaijing",
          "Valkyrie",
          "Arius"
        ]
      },
      "Global_zh-tw": {
        "phase1": [
            "花",
            "Momo好友咖啡廳組合",
            "果凍遊戲中心組合",
            "情人節組合",
            "避暑勝地泳池派對組合",
            "萬聖節南瓜咖啡廳組合",
            "傳統溫泉浴場組合",
            "正月居家組合",
            "軍事露營區組合",
            "海灘組合",
            "大運動會主題",
            "阿拜多斯教室組合",
            "遊戲開發部組合",
            "陽光渡假勝地組合",
            "購物中心組合",
            "格黑娜派對組合",
            "三一教室組合",
            "DJ派對會場組合",
            "顏色",
            "燦爛",
            "武器零件",
            "銅",
            "白金",
            "金",
            "銀",
            "金屬",
            "閃亮",
            "璀璨",
            "隱約"
        ],
        "phase2": [
            "花",
            "牡丹",
            "牽牛花",
            "玫瑰",
            "鬱金香",
            "櫻花",
            "水仙花",
            "百日菊",
            "蒲公英",
            "百合",
            "金盞花",
            "桔梗",
            "玉蘭花",
            "杜鵑花",
            "翡翠花",
            "燦爛",
            "閃亮",
            "顏色",
            "Momo好友咖啡廳組合",
            "果凍遊戲中心組合",
            "情人節組合",
            "避暑勝地泳池派對組合",
            "萬聖節南瓜咖啡廳組合",
            "傳統溫泉浴場組合",
            "正月居家組合",
            "軍事露營區組合",
            "海灘組合",
            "大運動會主題",
            "阿拜多斯教室組合",
            "遊戲開發部組合",
            "陽光渡假勝地組合",
            "購物中心組合",
            "格黑娜派對組合",
            "三一教室組合",
            "DJ派對會場組合",
            "紅",
            "黃",
            "褐色",
            "橘色",
            "粉紅",
            "灰色",
            "黑色",
            "淺綠色",
            "翠綠色",
            "白色",
            "紫色",
            "百鬼夜行",
            "赤冬",
            "三一",
            "格黑娜",
            "阿拜多斯",
            "千年",
            "山海經",
            "女武神",
            "奧利斯",
            "金屬",
            "銀",
            "金",
            "白金",
            "銅",
            "武器零件",
            "璀璨"
        ],
        "phase3": [
            "鑽石",
            "神秘",
            "花",
            "燦爛",
            "閃亮",
            "顏色",
            "很富足",
            "銀",
            "金",
            "白金",
            "銅",
            "武器零件",
            "百鬼夜行",
            "赤冬",
            "三一",
            "格黑娜",
            "阿拜多斯",
            "千年",
            "山海經",
            "女武神",
            "奧利斯"
        ]
      },
      "Global_ko-kr": {
        "phase1": [
            "꽃",
            "모모프렌즈 카페 세트",
            "젤리즈 오락실 세트",
            "발렌타인 세트",
            "여름 리조트 풀파티 세트",
            "할로윈 펌킨 카페 세트",
            "전통 온천장 세트",
            "새해 하우스 세트",
            "밀리터리 캠핑장 세트",
            "비치사이드 세트",
            "대운동회 세트",
            "아비도스 교실 세트",
            "게임개발부 세트",
            "선샤인 리조트 세트",
            "쇼핑몰 세트",
            "게헨나 파티 세트",
            "트리니티 교실 세트",
            "DJ 파티장 세트",
            "색깔",
            "찬란함",
            "무기 부품",
            "구리",
            "백금",
            "금",
            "은",
            "금속",
            "반짝임",
            "영롱함",
            "은은함"
        ],
        "phase2": [
            "꽃",
            "모란",
            "나팔꽃",
            "장미",
            "튤립",
            "벚꽃",
            "수선화",
            "백일홍",
            "민들레",
            "백합",
            "황금초",
            "도라지꽃",
            "목련",
            "진달래",
            "비취꽃",
            "찬란함",
            "반짝임",
            "색깔",
            "모모프렌즈 카페 세트",
            "젤리즈 오락실 세트",
            "발렌타인 세트",
            "여름 리조트 풀파티 세트",
            "할로윈 펌킨 카페 세트",
            "전통 온천장 세트",
            "새해 하우스 세트",
            "밀리터리 캠핑장 세트",
            "비치사이드 세트",
            "대운동회 세트",
            "아비도스 교실 세트",
            "게임개발부 세트",
            "선샤인 리조트 세트",
            "쇼핑몰 세트",
            "게헨나 파티 세트",
            "트리니티 교실 세트",
            "DJ 파티장 세트",
            "빨강",
            "노랑",
            "갈색",
            "주황",
            "분홍",
            "회색",
            "검정",
            "연두색",
            "청록색",
            "흰색",
            "보라",
            "백귀야행",
            "붉은겨울",
            "트리니티",
            "게헨나",
            "아비도스",
            "밀레니엄",
            "산해경",
            "발키리",
            "아리우스",
            "금속",
            "은",
            "금",
            "백금",
            "구리",
            "무기 부품",
            "영롱함"
        ],
        "phase3": [
            "다이아몬드",
            "신비",
            "꽃",
            "찬란함",
            "반짝임",
            "색깔",
            "풍족함",
            "은",
            "금",
            "백금",
            "구리",
            "무기 부품",
            "백귀야행",
            "붉은겨울",
            "트리니티",
            "게헨나",
            "아비도스",
            "밀레니엄",
            "산해경",
            "발키리",
            "아리우스"
        ]
      },
      "JP": {
        "phase1": [
          "花弁",
          "モモフレンズのカフェシリーズ",
          "ゼリーズゲーセンシリーズ",
          "バレンタインシリーズ",
          "サマーリゾートシリーズ",
          "ハロウィーンカフェシリーズ",
          "伝統的な温泉郷シリーズ",
          "お正月シリーズ",
          "ミリタリーアウトドア",
          "ビーチサイドシリーズ",
          "大運動会シリーズ",
          "アビドス教室シリーズ",
          "ゲーム開発部シリーズ",
          "サンシャインリゾートシリーズ",
          "デパートシリーズ",
          "ゲヘナパーティーシリーズ",
          "トリニティ教室シリーズ",
          "DJパーティー会場シリーズ",
          "百鬼夜行シリーズ",
          "色彩",
          "煌めき",
          "パーツ",
          "輝き",
          "铜",
          "金属",
          "銀",
          "金",
          "プラチナ",
          "明かり",
          "瞬き"
        ],
        "phase2": [
          "花弁",
          "牡丹",
          "アサガオ",
          "薔薇",
          "チューリップ",
          "桜",
          "スイセン",
          "百日紅",
          "タンポポ",
          "ユリ",
          "キンセンカ",
          "桔梗",
          "モクレン",
          "ツツジ",
          "翡翠花",
          "煌めき",
          "輝き",
          "色彩",
          "モモフレンズのカフェシリーズ",
          "ゼリーズゲーセンシリーズ",
          "バレンタインシリーズ",
          "サマーリゾートシリーズ",
          "ハロウィーンカフェシリーズ",
          "伝統的な温泉郷シリーズ",
          "お正月シリーズ",
          "ミリタリーアウトドア",
          "ビーチサイドシリーズ",
          "大運動会シリーズ",
          "アビドス教室シリーズ",
          "ゲーム開発部シリーズ",
          "サンシャインリゾートシリーズ",
          "デパートシリーズ",
          "ゲヘナパーティーシリーズ",
          "トリニティ教室シリーズ",
          "DJパーティー会場シリーズ",
          "百鬼夜行シリーズ",
          "レッド",
          "イエロー",
          "ブラウン",
          "アンバー",
          "ピンク",
          "グレー",
          "ブラック",
          "グリーン",
          "ブルー",
          "ホワイト",
          "パープル",
          "百鬼夜行",
          "レッドウィンター",
          "トリニティ",
          "ゲヘナ",
          "アビドス",
          "ミレニアム",
          "山海経",
          "ヴァルキューレ",
          "アリウス",
          "金属",
          "銀",
          "金",
          "プラチナ",
          "銅",
          "パーツ",
          "明かり"
        ],
        "phase3": [
            "ダイヤモンド",
            "神秘",
            "花弁",
            "煌めき",
            "輝き",
            "色彩",
            "豊かさ",
            "銀",
            "金",
            "プラチナ",
            "銅",
            "パーツ",
            "百鬼夜行",
            "レッドウィンター",
            "トリニティ",
            "ゲヘナ",
            "アビドス",
            "ミレニアム",
            "山海経",
            "ヴァルキューレ",
            "アリウス"
        ]
      }
    },
    "create_each_phase_weight" : [0, 10, 40, 40],
    "create_filter_type_list": [
        "Equipment",
        "Furniture",
        "Decoration",
        "Interior",
        "Eleph",
        "Coin",
        "Material",
        "Gift"
    ],
    "create_item_order": {
      "CN": {
        "basic": {
          "Special": [
            "Keystone-Piece",
            "Keystone"
          ],
          "Equipment": [],
          "Furniture": [],
          "Decoration": [],
          "Interior": [],
          "Eleph": [],
          "Coin": [],
          "Material": [
            "Nebra-Sky-Disk-Piece",
            "Broken-Nebra-Sky-Disk",
            "Damaged-Nebra-Sky-Disk",
            "Intact-Nebra-Sky-Disk",
            "Phasitos-Disc-Piece",
            "Broken-Phaistos-Disc",
            "Damaged-Phaistos-Disc",
            "Intact-Phaistos-Disc",
            "Wolfsegg-Iron-ore",
            "Wolfsegg-steel",
            "Low-Purity-Wolfsegg-steel",
            "High-Purity-Wolfsegg-steel",
            "Nimrud-Lens-Piece",
            "Broken-Nimrud-Lens",
            "Damaged-Nimrud-Lens",
            "Intact-Nimrud-Lens",
            "Mandrake-Seed",
            "Mandrake-Sprout",
            "Mandrake-Juice",
            "Mandrake-Extract",
            "Rohonc-Codex-Page",
            "Broken-Rohonc-Codex",
            "Annotated-Rohonc-Codex",
            "Intact-Rohonc-Codex",
            "Aether-Dust",
            "Aether-Piece",
            "Aether-Shared",
            "Aether-Essence",
            "Antikythera-Mechanism-Piece",
            "Broken-Antikythera-Mechanism",
            "Damaged-Antikythera-Mechanism",
            "Intact-Antikythera-Mechanism",
            "Voynich-Manuscript-Page",
            "Damaged-Voynich-Manuscript",
            "Annotated-Voynich-Manuscript",
            "Intact-Voynich-Manuscript",
            "Crystal-Haniwa-Fragment",
            "Broken-Crystal-Haniwa",
            "Repaired-Crystal-Haniwa",
            "Intact-Crystal-Haniwa",
            "Totem-Pole-Piece",
            "Broken-Totem-Pole",
            "Repaired-Totem-Pole",
            "Intact-Totem-Pole",
            "Ancient-Battery-Piece",
            "Broken-Ancient-Battery",
            "Damaged-Ancient-Battery",
            "Intact-Ancient-Battery",
            "Disco-Colgante-Piece",
            "Broken-Disco-Colgante",
            "Repaired-Disco-Colgante",
            "Intact-Disco-Colgante",
            "Winnipesaukee-Stone-Piece",
            "Broken-Winnipesaukee-Stone",
            "Damage-Winnipesaukee-Stone",
            "Intact-Winnipesaukee-Stone",
            "Beginner-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Normal-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Advanced-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Superior-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Beginner-Tactical-Training-Blu-ray-(Red Winter)",
            "Normal-Tactical-Training-Blu-ray-(Red Winter)",
            "Advanced-Tactical-Training-Blu-ray-(Red Winter)",
            "Superior-Tactical-Training-Blu-ray-(Red Winter)",
            "Beginner-Tactical-Training-Blu-ray-(Trinity)",
            "Normal-Tactical-Training-Blu-ray-(Trinity)",
            "Advanced-Tactical-Training-Blu-ray-(Trinity)",
            "Superior-Tactical-Training-Blu-ray-(Trinity)",
            "Beginner-Tactical-Training-Blu-ray-(Gehenna)",
            "Normal-Tactical-Training-Blu-ray-(Gehenna)",
            "Advanced-Tactical-Training-Blu-ray-(Gehenna)",
            "Superior-Tactical-Training-Blu-ray-(Gehenna)",
            "Beginner-Tactical-Training-Blu-ray-(Abydos)",
            "Normal-Tactical-Training-Blu-ray-(Abydos)",
            "Advanced-Tactical-Training-Blu-ray-(Abydos)",
            "Superior-Tactical-Training-Blu-ray-(Abydos)",
            "Beginner-Tactical-Training-Blu-ray-(Millennium)",
            "Normal-Tactical-Training-Blu-ray-(Millennium)",
            "Advanced-Tactical-Training-Blu-ray-(Millennium)",
            "Superior-Tactical-Training-Blu-ray-(Millennium)",
            "Beginner-Tactical-Training-Blu-ray-(Arius)",
            "Normal-Tactical-Training-Blu-ray-(Arius)",
            "Advanced-Tactical-Training-Blu-ray-(Arius)",
            "Superior-Tactical-Training-Blu-ray-(Arius)",
            "Beginner-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Normal-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Advanced-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Superior-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Beginner-Tactical-Training-Blu-ray-(Valkyrie)",
            "Normal-Tactical-Training-Blu-ray-(Valkyrie)",
            "Advanced-Tactical-Training-Blu-ray-(Valkyrie)",
            "Superior-Tactical-Training-Blu-ray-(Valkyrie)",
            "Beginner-Tech-Notes-(Hyakkiyako)",
            "Normal-Tech-Notes-(Hyakkiyako)",
            "Advanced-Tech-Notes-(Hyakkiyako)",
            "Superior-Tech-Notes-(Hyakkiyako)",
            "Beginner-Tech-Notes-(Red Winter)",
            "Normal-Tech-Notes-(Red Winter)",
            "Advanced-Tech-Notes-(Red Winter)",
            "Superior-Tech-Notes-(Red Winter)",
            "Beginner-Tech-Notes-(Trinity)",
            "Normal-Tech-Notes-(Trinity)",
            "Advanced-Tech-Notes-(Trinity)",
            "Superior-Tech-Notes-(Trinity)",
            "Beginner-Tech-Notes-(Gehenna)",
            "Normal-Tech-Notes-(Gehenna)",
            "Advanced-Tech-Notes-(Gehenna)",
            "Superior-Tech-Notes-(Gehenna)",
            "Beginner-Tech-Notes-(Abydos)",
            "Normal-Tech-Notes-(Abydos)",
            "Advanced-Tech-Notes-(Abydos)",
            "Superior-Tech-Notes-(Abydos)",
            "Beginner-Tech-Notes-(Millennium)",
            "Normal-Tech-Notes-(Millennium)",
            "Advanced-Tech-Notes-(Millennium)",
            "Superior-Tech-Notes-(Millennium)",
            "Beginner-Tech-Notes-(Arius)",
            "Normal-Tech-Notes-(Arius)",
            "Advanced-Tech-Notes-(Arius)",
            "Superior-Tech-Notes-(Arius)",
            "Beginner-Tech-Notes-(Shanhaijing)",
            "Normal-Tech-Notes-(Shanhaijing)",
            "Advanced-Tech-Notes-(Shanhaijing)",
            "Superior-Tech-Notes-(Shanhaijing)",
            "Beginner-Tech-Notes-(Valkyrie)",
            "Normal-Tech-Notes-(Valkyrie)",
            "Advanced-Tech-Notes-(Valkyrie)",
            "Superior-Tech-Notes-(Valkyrie)"
          ],
          "Gift": []
        }
      },
      "Global": {
        "basic": {
          "Special": [
            "Keystone-Piece",
            "Keystone"
          ],
          "Equipment": [],
          "Furniture": [],
          "Decoration": [],
          "Interior": [],
          "Eleph": [],
          "Coin": [],
          "Material": [
            "Nebra-Sky-Disk-Piece",
            "Broken-Nebra-Sky-Disk",
            "Damaged-Nebra-Sky-Disk",
            "Intact-Nebra-Sky-Disk",
            "Phasitos-Disc-Piece",
            "Broken-Phaistos-Disc",
            "Damaged-Phaistos-Disc",
            "Intact-Phaistos-Disc",
            "Wolfsegg-Iron-ore",
            "Wolfsegg-steel",
            "Low-Purity-Wolfsegg-steel",
            "High-Purity-Wolfsegg-steel",
            "Nimrud-Lens-Piece",
            "Broken-Nimrud-Lens",
            "Damaged-Nimrud-Lens",
            "Intact-Nimrud-Lens",
            "Mandrake-Seed",
            "Mandrake-Sprout",
            "Mandrake-Juice",
            "Mandrake-Extract",
            "Rohonc-Codex-Page",
            "Broken-Rohonc-Codex",
            "Annotated-Rohonc-Codex",
            "Intact-Rohonc-Codex",
            "Aether-Dust",
            "Aether-Piece",
            "Aether-Shared",
            "Aether-Essence",
            "Antikythera-Mechanism-Piece",
            "Broken-Antikythera-Mechanism",
            "Damaged-Antikythera-Mechanism",
            "Intact-Antikythera-Mechanism",
            "Voynich-Manuscript-Page",
            "Damaged-Voynich-Manuscript",
            "Annotated-Voynich-Manuscript",
            "Intact-Voynich-Manuscript",
            "Crystal-Haniwa-Fragment",
            "Broken-Crystal-Haniwa",
            "Repaired-Crystal-Haniwa",
            "Intact-Crystal-Haniwa",
            "Totem-Pole-Piece",
            "Broken-Totem-Pole",
            "Repaired-Totem-Pole",
            "Intact-Totem-Pole",
            "Ancient-Battery-Piece",
            "Broken-Ancient-Battery",
            "Damaged-Ancient-Battery",
            "Intact-Ancient-Battery",
            "Golden-Fleece",
            "Golden-Yarn",
            "Golden-Wool",
            "Golden-Dress",
            "Okiku-Doll-Piece",
            "Broken-Okiku-Doll",
            "Repaired-Okiku-Doll",
            "Intact-Okiku-Doll",
            "Disco-Colgante-Piece",
            "Broken-Disco-Colgante",
            "Repaired-Disco-Colgante",
            "Intact-Disco-Colgante",
            "Atlantis-Medal-Piece",
            "Broken-Atlantis-Medal",
            "Damaged-Atlantis-Medal",
            "Intact-Atlantis-Medal",
            "Roman-Dodecahedron-Piece",
            "Broken-Roman-Dodecahedron",
            "Repaired-Roman-Dodecahedron",
            "Intact-Roman-Dodecahedron",
            "Quimbaya-Relic-Piece",
            "Broken-Quimbaya-Relic",
            "Repaired-Quimbaya-Relic",
            "Intact-Quimbaya-Relic",
            "Istanbul-Rocket-Piece",
            "Broken-Istanbul-Rocket",
            "Repaired-Istanbul-Rocket",
            "Intact-Istanbul-Rocket",
            "Winnipesaukee-Stone-Piece",
            "Broken-Winnipesaukee-Stone",
            "Damage-Winnipesaukee-Stone",
            "Intact-Winnipesaukee-Stone",
            "Beginner-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Normal-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Advanced-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Superior-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Beginner-Tactical-Training-Blu-ray-(Red Winter)",
            "Normal-Tactical-Training-Blu-ray-(Red Winter)",
            "Advanced-Tactical-Training-Blu-ray-(Red Winter)",
            "Superior-Tactical-Training-Blu-ray-(Red Winter)",
            "Beginner-Tactical-Training-Blu-ray-(Trinity)",
            "Normal-Tactical-Training-Blu-ray-(Trinity)",
            "Advanced-Tactical-Training-Blu-ray-(Trinity)",
            "Superior-Tactical-Training-Blu-ray-(Trinity)",
            "Beginner-Tactical-Training-Blu-ray-(Gehenna)",
            "Normal-Tactical-Training-Blu-ray-(Gehenna)",
            "Advanced-Tactical-Training-Blu-ray-(Gehenna)",
            "Superior-Tactical-Training-Blu-ray-(Gehenna)",
            "Beginner-Tactical-Training-Blu-ray-(Abydos)",
            "Normal-Tactical-Training-Blu-ray-(Abydos)",
            "Advanced-Tactical-Training-Blu-ray-(Abydos)",
            "Superior-Tactical-Training-Blu-ray-(Abydos)",
            "Beginner-Tactical-Training-Blu-ray-(Millennium)",
            "Normal-Tactical-Training-Blu-ray-(Millennium)",
            "Advanced-Tactical-Training-Blu-ray-(Millennium)",
            "Superior-Tactical-Training-Blu-ray-(Millennium)",
            "Beginner-Tactical-Training-Blu-ray-(Arius)",
            "Normal-Tactical-Training-Blu-ray-(Arius)",
            "Advanced-Tactical-Training-Blu-ray-(Arius)",
            "Superior-Tactical-Training-Blu-ray-(Arius)",
            "Beginner-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Normal-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Advanced-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Superior-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Beginner-Tactical-Training-Blu-ray-(Valkyrie)",
            "Normal-Tactical-Training-Blu-ray-(Valkyrie)",
            "Advanced-Tactical-Training-Blu-ray-(Valkyrie)",
            "Superior-Tactical-Training-Blu-ray-(Valkyrie)",
            "Beginner-Tech-Notes-(Hyakkiyako)",
            "Normal-Tech-Notes-(Hyakkiyako)",
            "Advanced-Tech-Notes-(Hyakkiyako)",
            "Superior-Tech-Notes-(Hyakkiyako)",
            "Beginner-Tech-Notes-(Red Winter)",
            "Normal-Tech-Notes-(Red Winter)",
            "Advanced-Tech-Notes-(Red Winter)",
            "Superior-Tech-Notes-(Red Winter)",
            "Beginner-Tech-Notes-(Trinity)",
            "Normal-Tech-Notes-(Trinity)",
            "Advanced-Tech-Notes-(Trinity)",
            "Superior-Tech-Notes-(Trinity)",
            "Beginner-Tech-Notes-(Gehenna)",
            "Normal-Tech-Notes-(Gehenna)",
            "Advanced-Tech-Notes-(Gehenna)",
            "Superior-Tech-Notes-(Gehenna)",
            "Beginner-Tech-Notes-(Abydos)",
            "Normal-Tech-Notes-(Abydos)",
            "Advanced-Tech-Notes-(Abydos)",
            "Superior-Tech-Notes-(Abydos)",
            "Beginner-Tech-Notes-(Millennium)",
            "Normal-Tech-Notes-(Millennium)",
            "Advanced-Tech-Notes-(Millennium)",
            "Superior-Tech-Notes-(Millennium)",
            "Beginner-Tech-Notes-(Arius)",
            "Normal-Tech-Notes-(Arius)",
            "Advanced-Tech-Notes-(Arius)",
            "Superior-Tech-Notes-(Arius)",
            "Beginner-Tech-Notes-(Shanhaijing)",
            "Normal-Tech-Notes-(Shanhaijing)",
            "Advanced-Tech-Notes-(Shanhaijing)",
            "Superior-Tech-Notes-(Shanhaijing)",
            "Beginner-Tech-Notes-(Valkyrie)",
            "Normal-Tech-Notes-(Valkyrie)",
            "Advanced-Tech-Notes-(Valkyrie)",
            "Superior-Tech-Notes-(Valkyrie)"
          ],
          "Gift": []
        }
      },
      "JP": {
        "basic": {
          "Special": [
            "Keystone-Piece",
            "Keystone"
          ],
          "Equipment": [],
          "Furniture": [],
          "Decoration": [],
          "Interior": [],
          "Eleph": [],
          "Coin": [],
          "Material": [
            "Nebra-Sky-Disk-Piece",
            "Broken-Nebra-Sky-Disk",
            "Damaged-Nebra-Sky-Disk",
            "Intact-Nebra-Sky-Disk",
            "Phasitos-Disc-Piece",
            "Broken-Phaistos-Disc",
            "Damaged-Phaistos-Disc",
            "Intact-Phaistos-Disc",
            "Wolfsegg-Iron-ore",
            "Wolfsegg-steel",
            "Low-Purity-Wolfsegg-steel",
            "High-Purity-Wolfsegg-steel",
            "Nimrud-Lens-Piece",
            "Broken-Nimrud-Lens",
            "Damaged-Nimrud-Lens",
            "Intact-Nimrud-Lens",
            "Mandrake-Seed",
            "Mandrake-Sprout",
            "Mandrake-Juice",
            "Mandrake-Extract",
            "Rohonc-Codex-Page",
            "Broken-Rohonc-Codex",
            "Annotated-Rohonc-Codex",
            "Intact-Rohonc-Codex",
            "Aether-Dust",
            "Aether-Piece",
            "Aether-Shared",
            "Aether-Essence",
            "Antikythera-Mechanism-Piece",
            "Broken-Antikythera-Mechanism",
            "Damaged-Antikythera-Mechanism",
            "Intact-Antikythera-Mechanism",
            "Voynich-Manuscript-Page",
            "Damaged-Voynich-Manuscript",
            "Annotated-Voynich-Manuscript",
            "Intact-Voynich-Manuscript",
            "Crystal-Haniwa-Fragment",
            "Broken-Crystal-Haniwa",
            "Repaired-Crystal-Haniwa",
            "Intact-Crystal-Haniwa",
            "Totem-Pole-Piece",
            "Broken-Totem-Pole",
            "Repaired-Totem-Pole",
            "Intact-Totem-Pole",
            "Ancient-Battery-Piece",
            "Broken-Ancient-Battery",
            "Damaged-Ancient-Battery",
            "Intact-Ancient-Battery",
            "Golden-Fleece",
            "Golden-Yarn",
            "Golden-Wool",
            "Golden-Dress",
            "Okiku-Doll-Piece",
            "Broken-Okiku-Doll",
            "Repaired-Okiku-Doll",
            "Intact-Okiku-Doll",
            "Disco-Colgante-Piece",
            "Broken-Disco-Colgante",
            "Repaired-Disco-Colgante",
            "Intact-Disco-Colgante",
            "Atlantis-Medal-Piece",
            "Broken-Atlantis-Medal",
            "Damaged-Atlantis-Medal",
            "Intact-Atlantis-Medal",
            "Roman-Dodecahedron-Piece",
            "Broken-Roman-Dodecahedron",
            "Repaired-Roman-Dodecahedron",
            "Intact-Roman-Dodecahedron",
            "Quimbaya-Relic-Piece",
            "Broken-Quimbaya-Relic",
            "Repaired-Quimbaya-Relic",
            "Intact-Quimbaya-Relic",
            "Istanbul-Rocket-Piece",
            "Broken-Istanbul-Rocket",
            "Repaired-Istanbul-Rocket",
            "Intact-Istanbul-Rocket",
            "Winnipesaukee-Stone-Piece",
            "Broken-Winnipesaukee-Stone",
            "Damage-Winnipesaukee-Stone",
            "Intact-Winnipesaukee-Stone",
            "Physical-Education-Workbook",
            "Shooting-Workbook",
            "Hygiene-Workbook",
            "Beginner-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Normal-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Advanced-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Superior-Tactical-Training-Blu-ray-(Hyakkiyako)",
            "Beginner-Tactical-Training-Blu-ray-(Red Winter)",
            "Normal-Tactical-Training-Blu-ray-(Red Winter)",
            "Advanced-Tactical-Training-Blu-ray-(Red Winter)",
            "Superior-Tactical-Training-Blu-ray-(Red Winter)",
            "Beginner-Tactical-Training-Blu-ray-(Trinity)",
            "Normal-Tactical-Training-Blu-ray-(Trinity)",
            "Advanced-Tactical-Training-Blu-ray-(Trinity)",
            "Superior-Tactical-Training-Blu-ray-(Trinity)",
            "Beginner-Tactical-Training-Blu-ray-(Gehenna)",
            "Normal-Tactical-Training-Blu-ray-(Gehenna)",
            "Advanced-Tactical-Training-Blu-ray-(Gehenna)",
            "Superior-Tactical-Training-Blu-ray-(Gehenna)",
            "Beginner-Tactical-Training-Blu-ray-(Abydos)",
            "Normal-Tactical-Training-Blu-ray-(Abydos)",
            "Advanced-Tactical-Training-Blu-ray-(Abydos)",
            "Superior-Tactical-Training-Blu-ray-(Abydos)",
            "Beginner-Tactical-Training-Blu-ray-(Millennium)",
            "Normal-Tactical-Training-Blu-ray-(Millennium)",
            "Advanced-Tactical-Training-Blu-ray-(Millennium)",
            "Superior-Tactical-Training-Blu-ray-(Millennium)",
            "Beginner-Tactical-Training-Blu-ray-(Arius)",
            "Normal-Tactical-Training-Blu-ray-(Arius)",
            "Advanced-Tactical-Training-Blu-ray-(Arius)",
            "Superior-Tactical-Training-Blu-ray-(Arius)",
            "Beginner-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Normal-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Advanced-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Superior-Tactical-Training-Blu-ray-(Shanhaijing)",
            "Beginner-Tactical-Training-Blu-ray-(Valkyrie)",
            "Normal-Tactical-Training-Blu-ray-(Valkyrie)",
            "Advanced-Tactical-Training-Blu-ray-(Valkyrie)",
            "Superior-Tactical-Training-Blu-ray-(Valkyrie)",
            "Beginner-Tech-Notes-(Hyakkiyako)",
            "Normal-Tech-Notes-(Hyakkiyako)",
            "Advanced-Tech-Notes-(Hyakkiyako)",
            "Superior-Tech-Notes-(Hyakkiyako)",
            "Beginner-Tech-Notes-(Red Winter)",
            "Normal-Tech-Notes-(Red Winter)",
            "Advanced-Tech-Notes-(Red Winter)",
            "Superior-Tech-Notes-(Red Winter)",
            "Beginner-Tech-Notes-(Trinity)",
            "Normal-Tech-Notes-(Trinity)",
            "Advanced-Tech-Notes-(Trinity)",
            "Superior-Tech-Notes-(Trinity)",
            "Beginner-Tech-Notes-(Gehenna)",
            "Normal-Tech-Notes-(Gehenna)",
            "Advanced-Tech-Notes-(Gehenna)",
            "Superior-Tech-Notes-(Gehenna)",
            "Beginner-Tech-Notes-(Abydos)",
            "Normal-Tech-Notes-(Abydos)",
            "Advanced-Tech-Notes-(Abydos)",
            "Superior-Tech-Notes-(Abydos)",
            "Beginner-Tech-Notes-(Millennium)",
            "Normal-Tech-Notes-(Millennium)",
            "Advanced-Tech-Notes-(Millennium)",
            "Superior-Tech-Notes-(Millennium)",
            "Beginner-Tech-Notes-(Arius)",
            "Normal-Tech-Notes-(Arius)",
            "Advanced-Tech-Notes-(Arius)",
            "Superior-Tech-Notes-(Arius)",
            "Beginner-Tech-Notes-(Shanhaijing)",
            "Normal-Tech-Notes-(Shanhaijing)",
            "Advanced-Tech-Notes-(Shanhaijing)",
            "Superior-Tech-Notes-(Shanhaijing)",
            "Beginner-Tech-Notes-(Valkyrie)",
            "Normal-Tech-Notes-(Valkyrie)",
            "Advanced-Tech-Notes-(Valkyrie)",
            "Superior-Tech-Notes-(Valkyrie)"
          ],
          "Gift": []
        }
      }
    },
    "create_phase2_recommended_priority": {
      "爱丽丝宝贝":[3,4,2],
      "女仆爱丽丝宝贝":[7,4,2],
      "白子":[2],
      "白子(骑行)":[2,8],
      "白子(泳装)":[2,14],
      "芹香":[8],
      "芹香(新年)":[8],
      "星野":[8],
      "星野(泳装)":[8,14],
      "野宫":[5],
      "野宫(泳装)":[5,14],
      "绫音":[4],
      "绫音(泳装)":[4,14],
      "真琴":[8,7],
      "伊吕波":[4,2,3],
      "伊吹":[7,6],
      "日奈":[8],
      "日奈(泳装)":[8,14],
      "日奈(礼服)":[8,9],
      "亚子":[8,13],
      "亚子(礼服)":[8,13,4],
      "伊织":[5,6],
      "伊织(泳装)":[5,6],
      "千夏":[4],
      "千夏(温泉)":[4],
      "阿露":[8],
      "阿露(新年)":[8],
      "阿露(礼服)":[8],
      "睦月":[7],
      "睦月(正月)":[7],
      "佳代子":[3],
      "佳代子(正月)":[3,12,8],
      "佳代子(礼服)":[3],
      "遥香":[8,7,11],
      "遥香(正月)":[8,7,11],
      "晴奈":[12],
      "晴奈(正月)":[12,10],
      "晴奈(泳装)":[2,6],
      "淳子":[6],
      "淳子(正月)":[6],
      "泉":[6],
      "泉(泳装)":[6,14],
      "明里":[9,6],
      "明里(正月)":[9,6],
      "枫香":[10],
      "枫香(正月)":[10,13],
      "朱莉":[7],
      "濑名":[1,4, 13],
      "霞":[8,7],
      "惠":[7,11],
      "优香":[7],
      "优香(体操服)":[7],
      "诺亚":[4],
      "小雪":[7,8],
      "千寻":[3],
      "真纪":[7],
      "晴":[3,4],
      "晴(野营)":[3,4],
      "小玉":[7],
      "小玉(野营)":[7],
      "妮露":[7],
      "妮露(兔女郎)":[3,2,4],
      "花凛":[7],
      "花凛(兔女郎)":[7],
      "朱音":[10],
      "朱音(兔女郎)":[10],
      "明日奈":[5],
      "明日奈(兔女郎)":[5,6],
      "时":[2,4,13],
      "时(兔女郎)":[2,4,13],
      "响":[3],
      "响(应援团)":[3,10,8],
      "歌原":[7],
      "歌原(应援团)":[7,3],
      "琴里":[4,13],
      "琴里(应援团)":[2,7,13,4],
      "堇":[2],
      "日鞠":[8],
      "艾米":[8,3],
      "艾米(泳装)":[3,8,14],
      "柚子":[3,2,4,3,12],
      "柚子(女仆)":[3,2,4],
      "绿":[1],
      "桃井":[4,2,3],
      "渚":[8,6],
      "未花":[5,6],
      "和纱":[5,6],
      "夏":[8,6],
      "爱莉":[6],
      "好美":[6],
      "玲纱":[6,3,8],
      "铃美":[7],
      "鹤城":[4],
      "鹤城(泳装)":[4,14],
      "莲见":[6,9],
      "莲见(体操服)":[6,9],
      "真白":[5,6],
      "真白(泳装)":[5,6,14],
      "一花":[3,5,12],
      "美祢":[5],
      "花绘":[5],
      "花绘(圣诞)":[2,13],
      "芹娜":[1],
      "芹娜(圣诞)":[1,13],
      "日富美":[2,1],
      "日富美(泳装)":[2,1,14],
      "梓":[2,1,12],
      "梓(泳装)":[7,1,14,7],
      "小春":[4,5,2],
      "小春(泳装)":[14,4],
      "花子":[4,8],
      "花子(泳装)":[5,14,12],
      "忧":[4],
      "忧(泳装)":[4,14,8],
      "志美子":[4],
      "樱子":[6],
      "玛丽":[11,12],
      "玛丽(体操服)":[11,12],
      "日向":[11,12],
      "日向(泳装)":[10,14,12],
      "果穗":[4],
      "千世":[4],
      "千世(泳装)":[4,14],
      "椿":[1],
      "椿(导游)":[1,4],
      "三森":[10,12],
      "三森(泳装)":[10,4,5],
      "莲华":[9,10,4,14],
      "桔梗":[4,13],
      "缘里":[6,12],
      "枫":[3,7,11],
      "静子":[13,8,4],
      "静子(泳装)":[13,14],
      "菲娜":[9],
      "海香":[8,7,11],
      "满":[8],
      "泉奈":[12],
      "泉奈(泳装)":[12,14],
      "月咏":[7,8,11],
      "若藻":[7],
      "若藻(泳装)":[7,8],
      "男":[8,7,11],
      "瞬":[5],
      "瞬(幼)":[7,6],
      "心奈":[6],
      "纱绫":[13,4],
      "纱绫(私服)":[7,6,11],
      "瑠美":[10,12,8],
      "切里诺":[8,6,11],
      "切里诺(温泉)":[8,7,11,7],
      "巴":[4,12],
      "玛丽娜":[8,7],
      "实梨":[4],
      "梅露":[7,4],
      "红叶":[4,5],
      "和香":[6,7],
      "和香(温泉)":[9,6,7],
      "时雨":[4,13],
      "时雨(温泉)":[4,13],
      "康娜":[4,13],
      "桐乃":[6,12],
      "吹雪":[6],
      "宫子":[6,4,5],
      "宫子(泳装)":[4,14,6],
      "咲":[8,13,5],
      "咲(泳装)":[8,13,5,6],
      "美游":[5,6,12,6,14],
      "美游(泳装)":[5,6,12],
      "萌绘":[3,5,6],
      "纱织":[7,5],
      "美咲":[7],
      "日和":[10],
      "亚津子":[4,13]
    },
    "create_material_information": {
      "Keystone": {
        "weight": 10,
        "availability": {
          "phase1": true,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Special"
      },
      "Keystone-Piece": {
        "weight": 1,
        "availability": {
          "phase1": true,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Special"
      },
      "Nebra-Sky-Disk-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Nebra-Sky-Disk": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Nebra-Sky-Disk": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Nebra-Sky-Disk": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Phasitos-Disc-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Phaistos-Disc": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Phaistos-Disc": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Phaistos-Disc": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Wolfsegg-Iron-ore": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Wolfsegg-steel": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Low-Purity-Wolfsegg-steel": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "High-Purity-Wolfsegg-steel": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Nimrud-Lens-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Nimrud-Lens": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Nimrud-Lens": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Nimrud-Lens": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Mandrake-Seed": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Mandrake-Sprout": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Mandrake-Juice": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Mandrake-Extract": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Rohonc-Codex-Page": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Rohonc-Codex": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Annotated-Rohonc-Codex": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Rohonc-Codex": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Aether-Dust": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Aether-Piece": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Aether-Shared": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Aether-Essence": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Antikythera-Mechanism-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Antikythera-Mechanism": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Antikythera-Mechanism": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Antikythera-Mechanism": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Voynich-Manuscript-Page": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Voynich-Manuscript": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Annotated-Voynich-Manuscript": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Voynich-Manuscript": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Crystal-Haniwa-Fragment": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Crystal-Haniwa": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Crystal-Haniwa": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Crystal-Haniwa": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Totem-Pole-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Totem-Pole": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Totem-Pole": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Totem-Pole": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Ancient-Battery-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Ancient-Battery": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Ancient-Battery": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Ancient-Battery": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Golden-Fleece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Golden-Yarn": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Golden-Wool": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Golden-Dress": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Okiku-Doll-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Okiku-Doll": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Okiku-Doll": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Okiku-Doll": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Disco-Colgante-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Disco-Colgante": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Disco-Colgante": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Disco-Colgante": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Atlantis-Medal-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Atlantis-Medal": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damaged-Atlantis-Medal": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Atlantis-Medal": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Roman-Dodecahedron-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Roman-Dodecahedron": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Roman-Dodecahedron": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Roman-Dodecahedron": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Quimbaya-Relic-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Quimbaya-Relic": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Quimbaya-Relic": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Quimbaya-Relic": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Istanbul-Rocket-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Istanbul-Rocket": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Repaired-Istanbul-Rocket": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Istanbul-Rocket": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Winnipesaukee-Stone-Piece": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Broken-Winnipesaukee-Stone": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Damage-Winnipesaukee-Stone": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Intact-Winnipesaukee-Stone": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Physical-Education-Workbook": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Shooting-Workbook": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Hygiene-Workbook": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Hyakkiyako)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Hyakkiyako)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Hyakkiyako)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Hyakkiyako)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Red Winter)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Red Winter)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Red Winter)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Red Winter)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Trinity)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Trinity)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Trinity)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Trinity)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Gehenna)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Gehenna)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Gehenna)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Gehenna)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Abydos)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Abydos)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Abydos)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Abydos)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Millennium)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Millennium)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Millennium)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Millennium)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Arius)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Arius)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Arius)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Arius)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Shanhaijing)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Shanhaijing)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Shanhaijing)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Shanhaijing)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tactical-Training-Blu-ray-(Valkyrie)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tactical-Training-Blu-ray-(Valkyrie)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tactical-Training-Blu-ray-(Valkyrie)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tactical-Training-Blu-ray-(Valkyrie)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Hyakkiyako)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Hyakkiyako)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Hyakkiyako)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Hyakkiyako)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Red Winter)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Red Winter)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Red Winter)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Red Winter)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Trinity)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Trinity)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Trinity)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Trinity)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Gehenna)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Gehenna)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Gehenna)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Gehenna)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Abydos)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Abydos)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Abydos)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Abydos)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Millennium)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Millennium)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Millennium)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Millennium)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Arius)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Arius)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Arius)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Arius)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Shanhaijing)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Shanhaijing)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Shanhaijing)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Shanhaijing)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Beginner-Tech-Notes-(Valkyrie)": {
        "weight": 1,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Normal-Tech-Notes-(Valkyrie)": {
        "weight": 2,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": false
        },
        "material_type": "Material"
      },
      "Advanced-Tech-Notes-(Valkyrie)": {
        "weight": 4,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      },
      "Superior-Tech-Notes-(Valkyrie)": {
        "weight": 10,
        "availability": {
          "phase1": false,
          "phase2": true,
          "phase3": true
        },
        "material_type": "Material"
      }
    },
    "lesson_region_name":{
      "CN": [
          "沙勒业务区",
          "沙勒生活区",
          "歌赫娜中央区",
          "阿拜多斯高等学院",
          "千禧年学习区",
          "崔尼蒂广场区",
          "红冬联邦学院",
          "百鬼夜行中心",
          "D.U.白鸟区"
          ],
      "Global_en-us": [
          "Schale Office",
          "Schale Residence Hall",
          "Gehenna Hub",
          "Abydos Main Building",
          "Millennium Study Center",
          "Trinity Plaza Area",
          "Red Winter Federal Academy",
          "Hyakkiyako Central Area",
          "D.U. Shiratori City",
          "Shanhaijing Main Special Zone",
          "Haruhabara Electric Town"
      ],
        "Global_zh-tw": [
          "夏萊辦公室",
          "夏萊居住區",
          "格黑娜學園中央區",
          "阿拜多斯高中",
          "千年研究區域",
          "三一廣場臨",
          "赤冬聯邦學園",
          "百鬼夜行中心部",
          "D.U.白鳥區",
          "山海經中央特區",
          "春葉原"
      ],
      "Global_ko-kr": [
            "살레 업무관",
            "살레 생활관",
            "게헨나 중앙구",
            "아비도스 본관",
            "밀레니엄 학습관",
            "트리니티 광장 구역",
            "붉은겨울 연방학원",
            "백귀야행 중심부",
            "D.U.시라토리구",
            "산해경 중앙특구",
            "하루하바라 전자상가"
      ],
      "JP": [
          "シャーレオフィス",
          "シャーレ居住区",
          "ゲヘナ学園・中央区",
          "アビドス高等学校",
          "ミレニアム・スタデイーエリア",
          "トリニティ・スクエア",
          "レッドウインター連邦学園",
          "百鬼夜行中心部",
          "D.U.シラトリ区",
          "山海経中央特区",
          "春葉原"
        ]
    },
    "current_game_activity": {
        "CN": "GetSetGoKivotosHaloGames",
        "Global": "SunlightGirlsNightSong",
        "JP": "LivelyandBusily"
    },
    "dailyGameActivity": {
        "CN": null,
        "Global": null,
        "JP": null
    },
    "package_name": {
        "官服": "com.RoamingStar.BlueArchive",
        "B服": "com.RoamingStar.BlueArchive.bilibili",
        "国际服": "com.nexon.bluearchive",
        "国际服青少年": "com.nexon.bluearchiveteen",
        "韩国ONE": "com.nexon.bluearchiveone",
        "日服": "com.YostarJP.BlueArchive"
    },
    "activity_name": {
        "官服": "com.yostar.sdk.bridge.YoStarUnityPlayerActivity",
        "B服": "com.yostar.sdk.bridge.YoStarUnityPlayerActivity",
        "国际服": ".MxUnityPlayerActivity",
        "国际服青少年": ".MxUnityPlayerActivity",
        "韩国ONE": ".MxUnityPlayerActivity",
        "日服": "com.yostarjp.bluearchive.MxUnityPlayerActivity"
    },
    "total_assault_difficulties": {
        "CN": [ "NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME", "INSANE"],
        "Global": [ "NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME", "INSANE", "TORMENT" ],
        "JP": [ "NORMAL", "HARD", "VERYHARD", "HARDCORE", "EXTREME" , "INSANE", "TORMENT" ]
    },
    "hard_task_student_material" : [
        ["1-1", "优香"] , ["1-2", "铃美"] , ["1-3", "芹香"] ,
        ["2-1", "琴里"] , ["2-2", "明里"] , ["2-3", "纯子"] ,
        ["3-1", "铃美"] , ["3-2", "莲见"] , ["3-3", "白子"] ,
        ["4-1", "明日奈"] , ["4-2", "菲娜"] , ["4-3", "优香"] ,
        ["5-1", "明里"] , ["5-2", "纯子"] , ["5-3", "日富美"] ,
        ["6-1", "铃美"] , ["6-2", "菲娜"] , ["6-3", "纯子"] ,
        ["7-1", "明日奈"] , ["7-2", "芹香"] , ["7-3", "星野"] ,
        ["8-1", "琴里"] , ["8-2", "莲见"] , ["8-3", "晴奈"] ,
        ["9-1", "明里"] , ["9-2", "芹香"] , ["9-3", "白子"] ,
        ["10-1", "铃美"] , ["10-2", "菲娜"] , ["10-3", "日富美"] ,
        ["11-1", "明里"] , ["11-2", "莲见"] , ["11-3", "星野"] ,
        ["12-1", "琴里"] , ["12-2", "优香"] , ["12-3", "晴奈"] ,
        ["13-1", "遥香"] , ["13-2", "睦月"] , ["13-3", "泉"] ,
        ["14-1", "佳代子"] , ["14-2", "千世"] , ["14-3", "伊织"] ,
        ["15-1", "遥香"] , ["15-2", "椿"] , ["15-3", "妮露"] ,
        ["16-1", "明日奈"] , ["16-2", "睦月"] , ["16-3", "日奈"] ,
        ["17-1", "好美"] , ["17-2", "千世"] , ["17-3", "花凛"] ,
        ["18-1", "志美子"] , ["18-2", "绫音"] , ["18-3", "爱露"] ,
        ["19-1", "朱莉"] , ["19-2", "爱莉"] , ["19-3", "泉奈"] ,
        ["20-1", "芹娜"] , ["20-2", "晴"] , ["20-3", "伊织"] ,
        ["21-1", "铃美"] , ["21-2", "佳代子"] , ["21-3", "日富美(泳装)"] ,
        ["22-1", "志美子"] , ["22-2", "桐乃"] , ["22-3", "响"] ,
        ["23-1", "朱莉"] , ["23-2", "椿"] , ["23-3", "爱丽丝宝贝"] ,
        ["24-1", "芹娜"] , ["24-2", "玛丽"] , ["24-3", "日奈"] ,
        ["25-1", "遥香"] , ["25-2", "绫音"] , ["25-3", "纱绫(私服)"],
        ["26-1", "好美"], ["26-2", "爱莉"], ["26-3", "瞬(小)"],
        ["27-1", "志美子"], ["27-2", "晴"], ["27-3", "千夏(温泉)"],
        ["28-1", "朱莉"], ["28-2", "玛丽"], ["28-3", "美咲"]
    ],
  "student_names": [
    {
      "CN_name": "日和(泳装)",
      "CN_implementation": false,
      "Global_name": "Hiyori (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "ヒヨリ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "纱织(泳装)",
      "CN_implementation": false,
      "Global_name": "Saori (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "サオリ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "亚津子(泳装)",
      "CN_implementation": false,
      "Global_name": "Atsuko (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "アツコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "白子＊恐怖",
      "CN_implementation": false,
      "Global_name": "Shiroko Terror",
      "Global_implementation": false,
      "JP_name": "シロコ＊テラー",
      "JP_implementation": true
    },
    {
      "CN_name": "星野(临战)",
      "CN_implementation": false,
      "Global_name": "Hoshino (Battle)",
      "Global_implementation": false,
      "JP_name": "ホシノ(臨戦)",
      "JP_implementation": true
    },
    {
      "CN_name": "星野(临战)",
      "CN_implementation": false,
      "Global_name": "Hoshino (Battle)",
      "Global_implementation": false,
      "JP_name": "ホシノ(臨戦)",
      "JP_implementation": true
    },
    {
      "CN_name": "萌绘(泳装)",
      "CN_implementation": false,
      "Global_name": "Moe (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "モエ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "桐乃(泳装)",
      "CN_implementation": false,
      "Global_name": "Kirino (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "キリノ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "吹雪(泳装)",
      "CN_implementation": false,
      "Global_name": "Fubuki (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "フブキ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "叶渚(泳装)",
      "CN_implementation": false,
      "Global_name": "Kanna (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "カンナ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "芹香(泳装)",
      "CN_implementation": false,
      "Global_name": "Serika (Swimsuit)",
      "Global_implementation": false,
      "JP_name": "セリカ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "绿(女仆)",
      "CN_implementation": false,
      "Global_name": "Midori (Maid)",
      "Global_implementation": false,
      "JP_name": "ミドリ(メイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "桃井(女仆)",
      "CN_implementation": false,
      "Global_name": "Momoi (Maid)",
      "Global_implementation": false,
      "JP_name": "モモイ(メイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "绮罗罗",
      "CN_implementation": false,
      "Global_name": "Kirara",
      "Global_implementation": false,
      "JP_name": "キララ",
      "JP_implementation": true
    },
    {
      "CN_name": "爱莉(乐队)",
      "CN_implementation": false,
      "Global_name": "Airi (Band)",
      "Global_implementation": false,
      "JP_name": "アイリ(バンド)",
      "JP_implementation": true
    },
    {
      "CN_name": "好美(乐队)",
      "CN_implementation": false,
      "Global_name": "Yoshimi (Band)",
      "Global_implementation": false,
      "JP_name": "ヨシミ(バンド)",
      "JP_implementation": true
    },
    {
      "CN_name": "和纱(乐队)",
      "CN_implementation": false,
      "Global_name": "Kazusa (Band)",
      "Global_implementation": false,
      "JP_name": "カズサ(バンド)",
      "JP_implementation": true
    },
    {
      "CN_name": "椿(导游)",
      "CN_implementation": false,
      "Global_name": "Tsubaki (Guide)",
      "Global_implementation": false,
      "JP_name": "ツバキ(ガイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "海香",
      "CN_implementation": false,
      "Global_name": "Umika",
      "Global_implementation": false,
      "JP_name": "ウミカ",
      "JP_implementation": true
    },
    {
      "CN_name": "明里(正月)",
      "CN_implementation": false,
      "Global_name": "Akari (New Year)",
      "Global_implementation": false,
      "JP_name": "アカリ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "阿露(礼服)",
      "CN_implementation": false,
      "Global_name": "Aru (Dress)",
      "Global_implementation": false,
      "JP_name": "アル(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "佳代子(礼服)",
      "CN_implementation": false,
      "Global_name": "Kayoko (Dress)",
      "Global_implementation": false,
      "JP_name": "カヨコ(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "日奈(礼服)",
      "CN_implementation": false,
      "Global_name": "Hina (Dress)",
      "Global_implementation": true,
      "JP_name": "ヒナ(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "真琴",
      "CN_implementation": false,
      "Global_name": "Makoto",
      "Global_implementation": true,
      "JP_name": "マコト",
      "JP_implementation": true
    },
    {
      "CN_name": "伊吹",
      "CN_implementation": false,
      "Global_name": "Ibuki",
      "Global_implementation": true,
      "JP_name": "イブキ",
      "JP_implementation": true
    },
    {
      "CN_name": "亚子(礼服)",
      "CN_implementation": false,
      "Global_name": "Ako (Dress)",
      "Global_implementation": true,
      "JP_name": "アコ(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "晴(露营)",
      "CN_implementation": false,
      "Global_name": "Hare (Camp)",
      "Global_implementation": true,
      "JP_name": "ハレ(キャンプ)",
      "JP_implementation": true
    },
    {
      "CN_name": "小玉(露营)",
      "CN_implementation": false,
      "Global_name": "Kotama (Camp)",
      "Global_implementation": true,
      "JP_name": "コタマ(キャンプ)",
      "JP_implementation": true
    },
    {
      "CN_name": "艾米(泳装)",
      "CN_implementation": false,
      "Global_name": "Eimi (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "エイミ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "桔梗",
      "CN_implementation": false,
      "Global_name": "Kikyou",
      "Global_implementation": true,
      "JP_name": "キキョウ",
      "JP_implementation": true
    },
    {
      "CN_name": "莲华",
      "CN_implementation": false,
      "Global_name": "Renge",
      "Global_implementation": true,
      "JP_name": "レンゲ",
      "JP_implementation": true
    },
    {
      "CN_name": "紫草",
      "CN_implementation": false,
      "Global_name": "Yukari",
      "Global_implementation": true,
      "JP_name": "ユカリ",
      "JP_implementation": true
    },
    {
      "CN_name": "佐天泪子",
      "CN_implementation": false,
      "Global_name": "Saten Ruiko",
      "Global_implementation": true,
      "JP_name": "佐天涙子",
      "JP_implementation": true
    },
    {
      "CN_name": "食蜂操祈",
      "CN_implementation": false,
      "Global_name": "Shokuhou Misaki",
      "Global_implementation": true,
      "JP_name": "食蜂操祈",
      "JP_implementation": true
    },
    {
      "CN_name": "御坂美琴",
      "CN_implementation": false,
      "Global_name": "Misaka Mikoto",
      "Global_implementation": true,
      "JP_name": "御坂美琴",
      "JP_implementation": true
    },
    {
      "CN_name": "时雨(温泉)",
      "CN_implementation": false,
      "Global_name": "Shigure (Hot Spring)",
      "Global_implementation": true,
      "JP_name": "シグレ(温泉)",
      "JP_implementation": true
    },
    {
      "CN_name": "霞",
      "CN_implementation": false,
      "Global_name": "Kasumi",
      "Global_implementation": true,
      "JP_name": "カスミ",
      "JP_implementation": true
    },
    {
      "CN_name": "一花",
      "CN_implementation": false,
      "Global_name": "Ichika",
      "Global_implementation": true,
      "JP_name": "イチカ",
      "JP_implementation": true
    },
    {
      "CN_name": "晴奈(运动服)",
      "CN_implementation": false,
      "Global_name": "Haruna (Track)",
      "Global_implementation": true,
      "JP_name": "ハルナ(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "琴里(应援团)",
      "CN_implementation": false,
      "Global_name": "Kotori (Cheer Squad)",
      "Global_implementation": true,
      "JP_name": "コトリ(応援団)",
      "JP_implementation": true
    },
    {
      "CN_name": "红叶",
      "CN_implementation": false,
      "Global_name": "Momiji",
      "Global_implementation": true,
      "JP_name": "モミジ",
      "JP_implementation": true
    },
    {
      "CN_name": "芽留",
      "CN_implementation": false,
      "Global_name": "Meru",
      "Global_implementation": true,
      "JP_name": "メル",
      "JP_implementation": true
    },
    {
      "CN_name": "三森(泳装)",
      "CN_implementation": false,
      "Global_name": "Mimori (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ミモリ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "花子(泳装)",
      "CN_implementation": false,
      "Global_name": "Hanako (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ハナコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "小春(泳装)",
      "CN_implementation": false,
      "Global_name": "Koharu (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "コハル(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "日向(泳装)",
      "CN_implementation": false,
      "Global_name": "Hinata (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ヒナタ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "忧(泳装)",
      "CN_implementation": false,
      "Global_name": "Ui (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ウイ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "白子(泳装)",
      "CN_implementation": false,
      "Global_name": "Shiroko (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "シロコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "美游(泳装)",
      "CN_implementation": false,
      "Global_name": "Miyu (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ミユ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "咲(泳装)",
      "CN_implementation": false,
      "Global_name": "Saki (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "サキ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "宫子(泳装)",
      "CN_implementation": false,
      "Global_name": "Miyako (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ミヤコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "实里",
      "CN_implementation": false,
      "Global_name": "Minori",
      "Global_implementation": true,
      "JP_name": "ミノリ",
      "JP_implementation": true
    },
    {
      "CN_name": "弥奈",
      "CN_implementation": false,
      "Global_name": "Mina",
      "Global_implementation": true,
      "JP_name": "ミナ",
      "JP_implementation": true
    },
    {
      "CN_name": "瑠美",
      "CN_implementation": false,
      "Global_name": "Rumi",
      "Global_implementation": true,
      "JP_name": "ルミ",
      "JP_implementation": true
    },
    {
      "CN_name": "玲纱",
      "CN_implementation": true,
      "Global_name": "Reisa",
      "Global_implementation": true,
      "JP_name": "レイサ",
      "JP_implementation": true
    },
    {
      "CN_name": "柚子(女仆)",
      "CN_implementation": true,
      "Global_name": "Yuzu (Maid)",
      "Global_implementation": true,
      "JP_name": "ユズ(メイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "时(邦妮)",
      "CN_implementation": true,
      "Global_name": "Toki (Bunny)",
      "Global_implementation": true,
      "JP_name": "トキ(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "爱丽丝(女仆)",
      "CN_implementation": true,
      "Global_name": "Aris (Maid)",
      "Global_implementation": true,
      "JP_name": "アリス(メイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "果穗",
      "CN_implementation": false,
      "Global_name": "Kaho",
      "Global_implementation": true,
      "JP_name": "カホ",
      "JP_implementation": true
    },
    {
      "CN_name": "春香(新年)",
      "CN_implementation": true,
      "Global_name": "Haruka (New Year)",
      "Global_implementation": true,
      "JP_name": "ハルカ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "佳代子(新年)",
      "CN_implementation": true,
      "Global_name": "Kayoko (New Year)",
      "Global_implementation": true,
      "JP_name": "カヨコ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "小雪",
      "CN_implementation": true,
      "Global_name": "Koyuki",
      "Global_implementation": true,
      "JP_name": "コユキ",
      "JP_implementation": true
    },
    {
      "CN_name": "渚",
      "CN_implementation": true,
      "Global_name": "Nagisa",
      "Global_implementation": true,
      "JP_name": "ナギサ",
      "JP_implementation": true
    },
    {
      "CN_name": "时",
      "CN_implementation": true,
      "Global_name": "Toki",
      "Global_implementation": true,
      "JP_name": "トキ",
      "JP_implementation": true
    },
    {
      "CN_name": "樱子",
      "CN_implementation": true,
      "Global_name": "Sakurako",
      "Global_implementation": true,
      "JP_name": "サクラコ",
      "JP_implementation": true
    },
    {
      "CN_name": "康娜",
      "CN_implementation": true,
      "Global_name": "Kanna",
      "Global_implementation": true,
      "JP_name": "カンナ",
      "JP_implementation": true
    },
    {
      "CN_name": "惠",
      "CN_implementation": true,
      "Global_name": "Megu",
      "Global_implementation": true,
      "JP_name": "メグ",
      "JP_implementation": true
    },
    {
      "CN_name": "未花",
      "CN_implementation": true,
      "Global_name": "Mika",
      "Global_implementation": true,
      "JP_name": "ミカ",
      "JP_implementation": true
    },
    {
      "CN_name": "美祢",
      "CN_implementation": true,
      "Global_name": "Mine",
      "Global_implementation": true,
      "JP_name": "ミネ",
      "JP_implementation": true
    },
    {
      "CN_name": "纯子(新年)",
      "CN_implementation": true,
      "Global_name": "Junko (New Year)",
      "Global_implementation": true,
      "JP_name": "ジュンコ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "风香(新年)",
      "CN_implementation": true,
      "Global_name": "Fuuka (New Year)",
      "Global_implementation": true,
      "JP_name": "フウカ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "晴奈(新年)",
      "CN_implementation": true,
      "Global_name": "Haruna (New Year)",
      "Global_implementation": true,
      "JP_name": "ハルナ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "花江(圣诞)",
      "CN_implementation": true,
      "Global_name": "Hanae (Christmas)",
      "Global_implementation": true,
      "JP_name": "ハナエ(クリスマス)",
      "JP_implementation": true
    },
    {
      "CN_name": "芹娜(圣诞)",
      "CN_implementation": true,
      "Global_name": "Serina (Christmas)",
      "Global_implementation": true,
      "JP_name": "セリナ(クリスマス)",
      "JP_implementation": true
    },
    {
      "CN_name": "时雨",
      "CN_implementation": false,
      "Global_name": "Shigure",
      "Global_implementation": true,
      "JP_name": "シグレ",
      "JP_implementation": true
    },
    {
      "CN_name": "日鞠",
      "CN_implementation": false,
      "Global_name": "Himari",
      "Global_implementation": true,
      "JP_name": "ヒマリ",
      "JP_implementation": true
    },
    {
      "CN_name": "莲见(体操服)",
      "CN_implementation": true,
      "Global_name": "Hasumi (Track)",
      "Global_implementation": true,
      "JP_name": "ハスミ(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "玛丽(体操服)",
      "CN_implementation": true,
      "Global_name": "Mari (Track)",
      "Global_implementation": true,
      "JP_name": "マリー(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "优香(体操服)",
      "CN_implementation": true,
      "Global_name": "Yuuka (Track)",
      "Global_implementation": true,
      "JP_name": "ユウカ(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "茜(邦妮)",
      "CN_implementation": true,
      "Global_name": "Akane (Bunny)",
      "Global_implementation": true,
      "JP_name": "アカネ(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "响(应援团)",
      "CN_implementation": true,
      "Global_name": "Hibiki (Cheer Squad)",
      "Global_implementation": true,
      "JP_name": "ヒビキ(応援団)",
      "JP_implementation": true
    },
    {
      "CN_name": "诺亚",
      "CN_implementation": true,
      "Global_name": "Noa",
      "Global_implementation": true,
      "JP_name": "ノア",
      "JP_implementation": true
    },
    {
      "CN_name": "歌原(应援团)",
      "CN_implementation": true,
      "Global_name": "Utaha (Cheer Squad)",
      "Global_implementation": true,
      "JP_name": "ウタハ(応援団)",
      "JP_implementation": true
    },
    {
      "CN_name": "心奈",
      "CN_implementation": false,
      "Global_name": "Kokona",
      "Global_implementation": true,
      "JP_name": "ココナ",
      "JP_implementation": true
    },
    {
      "CN_name": "和纱",
      "CN_implementation": true,
      "Global_name": "Kazusa",
      "Global_implementation": true,
      "JP_name": "カズサ",
      "JP_implementation": true
    },
    {
      "CN_name": "萌绘",
      "CN_implementation": true,
      "Global_name": "Moe",
      "Global_implementation": true,
      "JP_name": "モエ",
      "JP_implementation": true
    },
    {
      "CN_name": "纱织",
      "CN_implementation": true,
      "Global_name": "Saori",
      "Global_implementation": true,
      "JP_name": "サオリ",
      "JP_implementation": true
    },
    {
      "CN_name": "千世(泳装)",
      "CN_implementation": true,
      "Global_name": "Chise (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "チセ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "泉奈(泳装)",
      "CN_implementation": true,
      "Global_name": "Izuna (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "イズナ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "静子(泳装)",
      "CN_implementation": true,
      "Global_name": "Shizuko (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "シズコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "星野(泳装)",
      "CN_implementation": true,
      "Global_name": "Hoshino (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ホシノ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "绫音(泳装)",
      "CN_implementation": true,
      "Global_name": "Ayane (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "アヤネ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "野宫(泳装)",
      "CN_implementation": true,
      "Global_name": "Nonomi (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ノノミ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "若藻(泳装)",
      "CN_implementation": true,
      "Global_name": "Wakamo (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ワカモ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "亚津子",
      "CN_implementation": true,
      "Global_name": "Atsuko",
      "Global_implementation": true,
      "JP_name": "アツコ",
      "JP_implementation": true
    },
    {
      "CN_name": "日和",
      "CN_implementation": true,
      "Global_name": "Hiyori",
      "Global_implementation": true,
      "JP_name": "ヒヨリ",
      "JP_implementation": true
    },
    {
      "CN_name": "美咲",
      "CN_implementation": true,
      "Global_name": "Misaki",
      "Global_implementation": true,
      "JP_name": "ミサキ",
      "JP_implementation": true
    },
    {
      "CN_name": "月咏",
      "CN_implementation": true,
      "Global_name": "Tsukuyo",
      "Global_implementation": true,
      "JP_name": "ツクヨ",
      "JP_implementation": true
    },
    {
      "CN_name": "满",
      "CN_implementation": true,
      "Global_name": "Michiru",
      "Global_implementation": true,
      "JP_name": "ミチル",
      "JP_implementation": true
    },
    {
      "CN_name": "伊吕波",
      "CN_implementation": true,
      "Global_name": "Iroha",
      "Global_implementation": true,
      "JP_name": "イロハ",
      "JP_implementation": true
    },
    {
      "CN_name": "枫",
      "CN_implementation": true,
      "Global_name": "Kaede",
      "Global_implementation": true,
      "JP_name": "カエデ",
      "JP_implementation": true
    },
    {
      "CN_name": "美游",
      "CN_implementation": true,
      "Global_name": "Miyu",
      "Global_implementation": true,
      "JP_name": "ミユ",
      "JP_implementation": true
    },
    {
      "CN_name": "咲",
      "CN_implementation": true,
      "Global_name": "Saki",
      "Global_implementation": true,
      "JP_name": "サキ",
      "JP_implementation": true
    },
    {
      "CN_name": "宫子",
      "CN_implementation": true,
      "Global_name": "Miyako",
      "Global_implementation": true,
      "JP_name": "ミヤコ",
      "JP_implementation": true
    },
    {
      "CN_name": "真里奈",
      "CN_implementation": true,
      "Global_name": "Marina",
      "Global_implementation": true,
      "JP_name": "マリナ",
      "JP_implementation": true
    },
    {
      "CN_name": "日向",
      "CN_implementation": true,
      "Global_name": "Hinata",
      "Global_implementation": true,
      "JP_name": "ヒナタ",
      "JP_implementation": true
    },
    {
      "CN_name": "忧",
      "CN_implementation": true,
      "Global_name": "Ui",
      "Global_implementation": true,
      "JP_name": "ウイ",
      "JP_implementation": true
    },
    {
      "CN_name": "三森",
      "CN_implementation": true,
      "Global_name": "Mimori",
      "Global_implementation": true,
      "JP_name": "ミモリ",
      "JP_implementation": true
    },
    {
      "CN_name": "千寻",
      "CN_implementation": true,
      "Global_name": "Chihiro",
      "Global_implementation": true,
      "JP_name": "チヒロ",
      "JP_implementation": true
    },
    {
      "CN_name": "濑名",
      "CN_implementation": true,
      "Global_name": "Sena",
      "Global_implementation": true,
      "JP_name": "セナ",
      "JP_implementation": true
    },
    {
      "CN_name": "吹雪",
      "CN_implementation": true,
      "Global_name": "Fubuki",
      "Global_implementation": true,
      "JP_name": "フブキ",
      "JP_implementation": true
    },
    {
      "CN_name": "若藻",
      "CN_implementation": true,
      "Global_name": "Wakamo",
      "Global_implementation": true,
      "JP_name": "ワカモ",
      "JP_implementation": true
    },
    {
      "CN_name": "芹香(新年)",
      "CN_implementation": true,
      "Global_name": "Serika (New Year)",
      "Global_implementation": true,
      "JP_name": "セリカ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "睦月(新年)",
      "CN_implementation": true,
      "Global_name": "Mutsuki (New Year)",
      "Global_implementation": true,
      "JP_name": "ムツキ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "爱露(新年)",
      "CN_implementation": true,
      "Global_name": "Aru (New Year)",
      "Global_implementation": true,
      "JP_name": "アル(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "和香(温泉)",
      "CN_implementation": true,
      "Global_name": "Nodoka (Hot Spring)",
      "Global_implementation": true,
      "JP_name": "ノドカ(温泉)",
      "JP_implementation": true
    },
    {
      "CN_name": "巴",
      "CN_implementation": true,
      "Global_name": "Tomoe",
      "Global_implementation": true,
      "JP_name": "トモエ",
      "JP_implementation": true
    },
    {
      "CN_name": "千夏(温泉)",
      "CN_implementation": true,
      "Global_name": "Chinatsu (Hot Spring)",
      "Global_implementation": true,
      "JP_name": "チナツ(温泉)",
      "JP_implementation": true
    },
    {
      "CN_name": "切里诺(温泉)",
      "CN_implementation": true,
      "Global_name": "Cherino (Hot Spring)",
      "Global_implementation": true,
      "JP_name": "チェリノ(温泉)",
      "JP_implementation": true
    },
    {
      "CN_name": "亚子",
      "CN_implementation": true,
      "Global_name": "Ako",
      "Global_implementation": true,
      "JP_name": "アコ",
      "JP_implementation": true
    },
    {
      "CN_name": "初音未来",
      "CN_implementation": true,
      "Global_name": "Hatsune Miku",
      "Global_implementation": true,
      "JP_name": "初音ミク",
      "JP_implementation": true
    },
    {
      "CN_name": "玛丽",
      "CN_implementation": true,
      "Global_name": "Mari",
      "Global_implementation": true,
      "JP_name": "マリー",
      "JP_implementation": true
    },
    {
      "CN_name": "夏",
      "CN_implementation": true,
      "Global_name": "Natsu",
      "Global_implementation": true,
      "JP_name": "ナツ",
      "JP_implementation": true
    },
    {
      "CN_name": "明日奈(邦妮)",
      "CN_implementation": true,
      "Global_name": "Asuna (Bunny)",
      "Global_implementation": true,
      "JP_name": "アスナ(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "花凛(邦妮)",
      "CN_implementation": true,
      "Global_name": "Karin (Bunny)",
      "Global_implementation": true,
      "JP_name": "カリン(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "妮露(邦妮)",
      "CN_implementation": true,
      "Global_name": "Neru (Bunny)",
      "Global_implementation": true,
      "JP_name": "ネル(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "纱绫(便服)",
      "CN_implementation": true,
      "Global_name": "Saya (Casual)",
      "Global_implementation": true,
      "JP_name": "サヤ(私服)",
      "JP_implementation": true
    },
    {
      "CN_name": "桐乃",
      "CN_implementation": true,
      "Global_name": "Kirino",
      "Global_implementation": true,
      "JP_name": "キリノ",
      "JP_implementation": true
    },
    {
      "CN_name": "瞬(小)",
      "CN_implementation": true,
      "Global_name": "Shun (Small)",
      "Global_implementation": true,
      "JP_name": "シュン(幼女)",
      "JP_implementation": true
    },
    {
      "CN_name": "白子(骑行)",
      "CN_implementation": true,
      "Global_name": "Shiroko (Cycling)",
      "Global_implementation": true,
      "JP_name": "シロコ(ライディング)",
      "JP_implementation": true
    },
    {
      "CN_name": "泉(泳装)",
      "CN_implementation": true,
      "Global_name": "Izumi (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "イズミ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "伊织(泳装)",
      "CN_implementation": true,
      "Global_name": "Iori (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "イオリ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "日奈(泳装)",
      "CN_implementation": true,
      "Global_name": "Hina (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ヒナ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "日富美(泳装)",
      "CN_implementation": true,
      "Global_name": "Hifumi (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ヒフミ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "鹤城(泳装)",
      "CN_implementation": true,
      "Global_name": "Tsurugi (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "ツルギ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "真白(泳装)",
      "CN_implementation": true,
      "Global_name": "Mashiro (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "マシロ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "梓(泳装)",
      "CN_implementation": true,
      "Global_name": "Azusa (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "アズサ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "小春",
      "CN_implementation": true,
      "Global_name": "Koharu",
      "Global_implementation": true,
      "JP_name": "コハル",
      "JP_implementation": true
    },
    {
      "CN_name": "花子",
      "CN_implementation": true,
      "Global_name": "Hanako",
      "Global_implementation": true,
      "JP_name": "ハナコ",
      "JP_implementation": true
    },
    {
      "CN_name": "梓",
      "CN_implementation": true,
      "Global_name": "Azusa",
      "Global_implementation": true,
      "JP_name": "アズサ",
      "JP_implementation": true
    },
    {
      "CN_name": "柚子",
      "CN_implementation": true,
      "Global_name": "Yuzu",
      "Global_implementation": true,
      "JP_name": "ユズ",
      "JP_implementation": true
    },
    {
      "CN_name": "和香",
      "CN_implementation": true,
      "Global_name": "Nodoka",
      "Global_implementation": true,
      "JP_name": "ノドカ",
      "JP_implementation": true
    },
    {
      "CN_name": "切里诺",
      "CN_implementation": true,
      "Global_name": "Cherino",
      "Global_implementation": true,
      "JP_name": "チェリノ",
      "JP_implementation": true
    },
    {
      "CN_name": "桃",
      "CN_implementation": true,
      "Global_name": "Momoi",
      "Global_implementation": true,
      "JP_name": "モモイ",
      "JP_implementation": true
    },
    {
      "CN_name": "绿",
      "CN_implementation": true,
      "Global_name": "Midori",
      "Global_implementation": true,
      "JP_name": "ミドリ",
      "JP_implementation": true
    },
    {
      "CN_name": "爱丽丝",
      "CN_implementation": true,
      "Global_name": "Aris",
      "Global_implementation": true,
      "JP_name": "アリス",
      "JP_implementation": true
    },
    {
      "CN_name": "静子",
      "CN_implementation": true,
      "Global_name": "Shizuko",
      "Global_implementation": true,
      "JP_name": "シズコ",
      "JP_implementation": true
    },
    {
      "CN_name": "泉奈",
      "CN_implementation": true,
      "Global_name": "Izuna",
      "Global_implementation": true,
      "JP_name": "イズナ",
      "JP_implementation": true
    },
    {
      "CN_name": "真白",
      "CN_implementation": true,
      "Global_name": "Mashiro",
      "Global_implementation": true,
      "JP_name": "マシロ",
      "JP_implementation": true
    },
    {
      "CN_name": "好美",
      "CN_implementation": true,
      "Global_name": "Yoshimi",
      "Global_implementation": true,
      "JP_name": "ヨシミ",
      "JP_implementation": true
    },
    {
      "CN_name": "志美子",
      "CN_implementation": true,
      "Global_name": "Shimiko",
      "Global_implementation": true,
      "JP_name": "シミコ",
      "JP_implementation": true
    },
    {
      "CN_name": "芹娜",
      "CN_implementation": true,
      "Global_name": "Serina",
      "Global_implementation": true,
      "JP_name": "セリナ",
      "JP_implementation": true
    },
    {
      "CN_name": "朱莉",
      "CN_implementation": true,
      "Global_name": "Juri",
      "Global_implementation": true,
      "JP_name": "ジュリ",
      "JP_implementation": true
    },
    {
      "CN_name": "小玉",
      "CN_implementation": true,
      "Global_name": "Kotama",
      "Global_implementation": true,
      "JP_name": "コタマ",
      "JP_implementation": true
    },
    {
      "CN_name": "千夏",
      "CN_implementation": true,
      "Global_name": "Chinatsu",
      "Global_implementation": true,
      "JP_name": "チナツ",
      "JP_implementation": true
    },
    {
      "CN_name": "绫音",
      "CN_implementation": true,
      "Global_name": "Ayane",
      "Global_implementation": true,
      "JP_name": "アヤネ",
      "JP_implementation": true
    },
    {
      "CN_name": "歌原",
      "CN_implementation": true,
      "Global_name": "Utaha",
      "Global_implementation": true,
      "JP_name": "ウタハ",
      "JP_implementation": true
    },
    {
      "CN_name": "晴",
      "CN_implementation": true,
      "Global_name": "Hare",
      "Global_implementation": true,
      "JP_name": "ハレ",
      "JP_implementation": true
    },
    {
      "CN_name": "花江",
      "CN_implementation": true,
      "Global_name": "Hanae",
      "Global_implementation": true,
      "JP_name": "ハナエ",
      "JP_implementation": true
    },
    {
      "CN_name": "风香",
      "CN_implementation": true,
      "Global_name": "Fuuka",
      "Global_implementation": true,
      "JP_name": "フウカ",
      "JP_implementation": true
    },
    {
      "CN_name": "爱理",
      "CN_implementation": true,
      "Global_name": "Airi",
      "Global_implementation": true,
      "JP_name": "アイリ",
      "JP_implementation": true
    },
    {
      "CN_name": "纱绫",
      "CN_implementation": true,
      "Global_name": "Saya",
      "Global_implementation": true,
      "JP_name": "サヤ",
      "JP_implementation": true
    },
    {
      "CN_name": "花凛",
      "CN_implementation": true,
      "Global_name": "Karin",
      "Global_implementation": true,
      "JP_name": "カリン",
      "JP_implementation": true
    },
    {
      "CN_name": "响",
      "CN_implementation": true,
      "Global_name": "Hibiki",
      "Global_implementation": true,
      "JP_name": "ヒビキ",
      "JP_implementation": true
    },
    {
      "CN_name": "菲娜",
      "CN_implementation": true,
      "Global_name": "Pina",
      "Global_implementation": true,
      "JP_name": "フィーナ",
      "JP_implementation": true
    },
    {
      "CN_name": "铃美",
      "CN_implementation": true,
      "Global_name": "Suzumi",
      "Global_implementation": true,
      "JP_name": "スズミ",
      "JP_implementation": true
    },
    {
      "CN_name": "琴里",
      "CN_implementation": true,
      "Global_name": "Kotori",
      "Global_implementation": true,
      "JP_name": "コトリ",
      "JP_implementation": true
    },
    {
      "CN_name": "明日奈",
      "CN_implementation": true,
      "Global_name": "Asuna",
      "Global_implementation": true,
      "JP_name": "アスナ",
      "JP_implementation": true
    },
    {
      "CN_name": "春香",
      "CN_implementation": true,
      "Global_name": "Haruka",
      "Global_implementation": true,
      "JP_name": "ハルカ",
      "JP_implementation": true
    },
    {
      "CN_name": "优香",
      "CN_implementation": true,
      "Global_name": "Yuuka",
      "Global_implementation": true,
      "JP_name": "ユウカ",
      "JP_implementation": true
    },
    {
      "CN_name": "椿",
      "CN_implementation": true,
      "Global_name": "Tsubaki",
      "Global_implementation": true,
      "JP_name": "ツバキ",
      "JP_implementation": true
    },
    {
      "CN_name": "芹香",
      "CN_implementation": true,
      "Global_name": "Serika",
      "Global_implementation": true,
      "JP_name": "セリカ",
      "JP_implementation": true
    },
    {
      "CN_name": "纯子",
      "CN_implementation": true,
      "Global_name": "Junko",
      "Global_implementation": true,
      "JP_name": "ジュンコ",
      "JP_implementation": true
    },
    {
      "CN_name": "睦月",
      "CN_implementation": true,
      "Global_name": "Mutsuki",
      "Global_implementation": true,
      "JP_name": "ムツキ",
      "JP_implementation": true
    },
    {
      "CN_name": "佳代子",
      "CN_implementation": true,
      "Global_name": "Kayoko",
      "Global_implementation": true,
      "JP_name": "カヨコ",
      "JP_implementation": true
    },
    {
      "CN_name": "野宫",
      "CN_implementation": true,
      "Global_name": "Nonomi",
      "Global_implementation": true,
      "JP_name": "ノノミ",
      "JP_implementation": true
    },
    {
      "CN_name": "莲见",
      "CN_implementation": true,
      "Global_name": "Hasumi",
      "Global_implementation": true,
      "JP_name": "ハスミ",
      "JP_implementation": true
    },
    {
      "CN_name": "明里",
      "CN_implementation": true,
      "Global_name": "Akari",
      "Global_implementation": true,
      "JP_name": "アカリ",
      "JP_implementation": true
    },
    {
      "CN_name": "千世",
      "CN_implementation": true,
      "Global_name": "Chise",
      "Global_implementation": true,
      "JP_name": "チセ",
      "JP_implementation": true
    },
    {
      "CN_name": "茜",
      "CN_implementation": true,
      "Global_name": "Akane",
      "Global_implementation": true,
      "JP_name": "アカネ",
      "JP_implementation": true
    },
    {
      "CN_name": "鹤城",
      "CN_implementation": true,
      "Global_name": "Tsurugi",
      "Global_implementation": true,
      "JP_name": "ツルギ",
      "JP_implementation": true
    },
    {
      "CN_name": "堇",
      "CN_implementation": true,
      "Global_name": "Sumire",
      "Global_implementation": true,
      "JP_name": "スミレ",
      "JP_implementation": true
    },
    {
      "CN_name": "瞬",
      "CN_implementation": true,
      "Global_name": "Shun",
      "Global_implementation": true,
      "JP_name": "シュン",
      "JP_implementation": true
    },
    {
      "CN_name": "白子",
      "CN_implementation": true,
      "Global_name": "Shiroko",
      "Global_implementation": true,
      "JP_name": "シロコ",
      "JP_implementation": true
    },
    {
      "CN_name": "泉",
      "CN_implementation": true,
      "Global_name": "Izumi",
      "Global_implementation": true,
      "JP_name": "イズミ",
      "JP_implementation": true
    },
    {
      "CN_name": "妮露",
      "CN_implementation": true,
      "Global_name": "Neru",
      "Global_implementation": true,
      "JP_name": "ネル",
      "JP_implementation": true
    },
    {
      "CN_name": "真纪",
      "CN_implementation": true,
      "Global_name": "Maki",
      "Global_implementation": true,
      "JP_name": "マキ",
      "JP_implementation": true
    },
    {
      "CN_name": "伊织",
      "CN_implementation": true,
      "Global_name": "Iori",
      "Global_implementation": true,
      "JP_name": "イオリ",
      "JP_implementation": true
    },
    {
      "CN_name": "星野",
      "CN_implementation": true,
      "Global_name": "Hoshino",
      "Global_implementation": true,
      "JP_name": "ホシノ",
      "JP_implementation": true
    },
    {
      "CN_name": "日奈",
      "CN_implementation": true,
      "Global_name": "Hina",
      "Global_implementation": true,
      "JP_name": "ヒナ",
      "JP_implementation": true
    },
    {
      "CN_name": "日富美",
      "CN_implementation": true,
      "Global_name": "Hifumi",
      "Global_implementation": true,
      "JP_name": "ヒフミ",
      "JP_implementation": true
    },
    {
      "CN_name": "晴奈",
      "CN_implementation": true,
      "Global_name": "Haruna",
      "Global_implementation": true,
      "JP_name": "ハルナ",
      "JP_implementation": true
    },
    {
      "CN_name": "艾米",
      "CN_implementation": true,
      "Global_name": "Eimi",
      "Global_implementation": true,
      "JP_name": "エイミ",
      "JP_implementation": true
    },
    {
      "CN_name": "爱露",
      "CN_implementation": true,
      "Global_name": "Aru",
      "Global_implementation": true,
      "JP_name": "アル",
      "JP_implementation": true
    }
  ]
}
'''

# Delete QFluentWidgets Pro Alert
try:
    import os
    import importlib.util as iu

    _init_path = iu.find_spec("qfluentwidgets").origin
    _init_path = os.path.dirname(_init_path)
    _init_path = os.path.join(_init_path, "common", "config.py")

    fr = open(_init_path, "r")
    _init_content = fr.read().replace("print(ALERT)", "pass")
    fr.close()

    fw = open(_init_path, "w")
    fw.write(_init_content)
    fw.close()
except:
    pass
