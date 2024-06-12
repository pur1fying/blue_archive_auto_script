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
    "daily_reset": [[20, 0, 0]],
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
    "daily_reset": [[20, 0, 0], [8, 0, 0]],
    "next_tick": 0,
    "event_name": "咖啡厅邀请",
    "func_name": "cafe_invite",
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
    "program_address": "None",
    "open_emulator_stat": false,
    "emulator_wait_time": "180",
    "multi_emulator_check": false,
    "ArenaLevelDiff": 0,
    "maxArenaRefreshTimes": 10,
    "createPriority": "花>Mo>情人节>果冻>色彩>灿烂>光芒>玲珑>白金>黄金>铜>白银>金属>隐然",
    "use_acceleration_ticket": false,
    "createTime": "3",
    "last_refresh_config_time": "0",
    "alreadyCreateTime": "0",
    "totalForceFightDifficulty": "NORMAL",
    "hardPriority": "1-1-1",
    "unfinished_hard_tasks": [],
    "mainlinePriority": "5-1-1",
    "unfinished_normal_tasks": [],
    "explore_normal_task_force_each_fight" : false,
    "main_story_regions": "",
    "rewarded_task_times": "2,2,2",
    "purchase_rewarded_task_ticket_times": "0",
    "explore_normal_task_force_sss": true,
    "special_task_times": "1,1",
    "purchase_scrimmage_ticket_times": "0",
    "scrimmage_times": "2,2,2",
    "explore_normal_task_force_each_fight" : false,
    "patStyle": "拖动礼物",
    "antiHarmony": true,
    "bannerVisibility": true,
    "push_after_error":false,
    "push_after_completion":false,
    "push_json":"",
    "push_serverchan":"",
    "cafe_reward_lowest_affection_first": true,
    "cafe_reward_has_no2_cafe": false,
    "cafe_reward_collect_hour_reward": true,
    "cafe_reward_use_invitation_ticket": true,
    "favorStudent1": [
        "爱丽丝"
    ],
    "favorStudent2": [
        "爱丽丝(女仆)"
    ],
    "server": "官服",
    "adbPort": "5555",
    "lesson_times": [
        1,
        1,
        1,
        1,
        1,
        1
    ],
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
    "explore_normal_task_regions": [

    ],
    "explore_hard_task_list": "此处填写需要推图的关卡",
    "emulatorIsMultiInstance": false,
    "emulatorMultiInstanceNumber": 0,
    "multiEmulatorName": "mumu",
    "manual_boss": false,
    "explore_normal_task_force_sss": true,
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
    "activity_exchange_reward": false,
    "activity_exchange_50_times_at_once": false,
    "explore_hard_task_need_sss": true,
    "explore_hard_task_need_present": true,
    "explore_hard_task_need_task": true,
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
    ]
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
    }
]

'''
STATIC_DEFAULT_CONFIG = '''
{
    "common_shop_price_list": {
        "CN": [
            ["悬赏通缉[光碟]券",30,"pyroxene"],["悬赏通缉[技术笔记]券",30,"pyroxene"],["悬赏通缉[神秘古物]券",30,"pyroxene"],["日程券",30,"pyroxene"],
            ["学院交流会[崔尼蒂]券",30,"pyroxene"],["学院交流会[歌赫娜]券",30,"pyroxene"],["学院交流会[千禧年]券",30,"pyroxene"],["初级经验书", 12500, "creditpoints"],
            ["中级经验书", 125000, "creditpoints"],["高级经验书", 300000, "creditpoints"],["特级经验书",500000,"creditpoints"],["初级经验珠", 10000, "creditpoints"],
            ["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],["初级经验珠", 10000, "creditpoints"],
            ["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],["随机初级神秘古物", 8000, "creditpoints"],
            ["随机初级神秘古物", 8000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"],["随机中级神秘古物", 25000, "creditpoints"]
        ],
        "Global": [
            ["初级经验书", 12500, "creditpoints"],["中级经验书", 125000, "creditpoints"],["高级经验书", 300000, "creditpoints"],["特级经验书", 500000, "creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 10000, "creditpoints"],["中级经验珠", 40000, "creditpoints"],["高级经验珠", 96000, "creditpoints"],["特级经验珠", 128000, "creditpoints"],
            ["初级经验珠", 20000, "creditpoints"],["中级经验珠", 80000, "creditpoints"],["高级经验珠", 192000, "creditpoints"],["特级经验珠", 256000, "creditpoints"],
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
            ["真白神明文字x5",50],["纱绫神明文字x5",50],["风香神明文字x5",50],["歌原神明文字x5",50],
            ["30AP", 15],["60AP", 30], ["初级经验书x5", 5],["中级经验书x10", 25],
            ["高级经验书x3", 60],["特级经验书x1", 100],["信用点x5k", 4],["信用点x5k", 20],
            ["信用点x75k", 60],["信用点x125k", 10]
        ],
        "Global": [
             ["静子神明文字x5",50],["真白神明文字x5",50],["纱绫神明文字x5",50],["风香神明文字x5",50],
             ["歌原神明文字x5",50],["30AP", 15],["60AP", 30], ["初级经验书x5", 5],
             ["中级经验书x10", 25],["高级经验书x3", 60],["特级经验书x1", 100],["信用点x5k", 4],
             ["信用点x5k", 20],["信用点x75k", 60],["信用点x125k", 10]
        ],
        "JP": [
             ["静子神明文字x5",50],["真白神明文字x5",50],["纱绫神明文字x5",50],["风香神明文字x5",50],
             ["歌原神明文字x5",50],["30AP", 15],["60AP", 30], ["初级经验书x5", 5],
             ["中级经验书x10", 25],["高级经验书x3", 60],["特级经验书x1", 100],["信用点x5k", 4],
             ["信用点x5k", 20],["信用点x75k", 60],["信用点x125k", 100]
        ]
    },
    "create_default_priority": {
        "CN": [
                "花",
                "MomoFriends咖啡厅",
                "果冻游戏中心",
                "情人节",
                "夏日",
                "万圣节",
                "温泉浴场",
                "新年",
                "色彩",
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
        "Global":
            [
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
                "Department Store Set",
                "Gehenna Party Set",
                "Colorful",
                "Radiant",
                "Weapon Parts",
                "Copper",
                "Platinum",
                "Gold",
                "Silver",
                "Metal",
                "Shiny",
                "Brilliant",
                "Subtle"
        ],
        "JP": [
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
            ]
    },
    "lesson_region_name":{
        "CN": [
            "沙勒业务区",
            "沙勒生活区",
            "歌赫娜中央区",
            "阿拜多斯高等学院",
            "千禧年学习区",
            "崔尼蒂广场区",
            "红冬联邦学院"
            ],
        "Global": [
            "Schale Office",
            "Schale Residence Hall",
            "Gehenna Hub",
            "Abydos Main Building",
            "Millennium Study Center",
            "Trinity Plaza Area",
            "Red Winter Federal Academy",
            "Hyakkiyako Central Area",
            "D.U. Shiratori City",
            "Shanhaijing Main Special Zone"
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
            "山海経中央特区"
          ]
    },
    "current_game_activity": {
        "CN": "AbydosResortRestorationCommittee",
        "Global": null,
        "JP": null
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
        "日服": "com.YostarJP.BlueArchive"
    },
    "activity_name": {
        "官服": "com.yostar.sdk.bridge.YoStarUnityPlayerActivity",
        "B服": "com.yostar.sdk.bridge.YoStarUnityPlayerActivity",
        "国际服": ".MxUnityPlayerActivity",
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
        ["15-1", "遥香"] , ["15-2", "椿"] , ["15-3", "尼禄"] ,
        ["16-1", "明日奈"] , ["16-2", "睦月"] , ["16-3", "日奈"] ,
        ["17-1", "好美"] , ["17-2", "千世"] , ["17-3", "花凛"] ,
        ["18-1", "志美子"] , ["18-2", "绫音"] , ["18-3", "爱露"] ,
        ["19-1", "朱莉"] , ["19-2", "爱莉"] , ["19-3", "泉奈"] ,
        ["20-1", "芹娜"] , ["20-2", "晴"] , ["20-3", "伊织"] ,
        ["21-1", "铃美"] , ["21-2", "佳代子"] , ["21-3", "日富美(泳装)"] ,
        ["22-1", "志美子"] , ["22-2", "桐乃"] , ["22-3", "响"] ,
        ["23-1", "朱莉"] , ["23-2", "椿"] , ["23-3", "爱丽丝宝贝"] ,
        ["24-1", "芹娜"] , ["24-2", "玛丽"] , ["24-3", "日奈"] ,
        ["25-1", "遥香"] , ["25-2", "绫音"] , ["25-3", "纱绫(私服)"]
    ],
  "student_names": [
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
      "Global_implementation": false,
      "JP_name": "ヒナ(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "真琴",
      "CN_implementation": false,
      "Global_name": "Makoto",
      "Global_implementation": false,
      "JP_name": "マコト",
      "JP_implementation": true
    },
    {
      "CN_name": "伊吹",
      "CN_implementation": false,
      "Global_name": "Ibuki",
      "Global_implementation": false,
      "JP_name": "イブキ",
      "JP_implementation": true
    },
    {
      "CN_name": "亚子(礼服)",
      "CN_implementation": false,
      "Global_name": "Ako (Dress)",
      "Global_implementation": false,
      "JP_name": "アコ(ドレス)",
      "JP_implementation": true
    },
    {
      "CN_name": "晴(露营)",
      "CN_implementation": false,
      "Global_name": "Hare (Camp)",
      "Global_implementation": false,
      "JP_name": "ハレ(キャンプ)",
      "JP_implementation": true
    },
    {
      "CN_name": "小玉(露营)",
      "CN_implementation": false,
      "Global_name": "Kotama (Camp)",
      "Global_implementation": false,
      "JP_name": "コタマ(キャンプ)",
      "JP_implementation": true
    },
    {
      "CN_name": "艾米(泳装)",
      "CN_implementation": false,
      "Global_name": "Eimi (Swimsuit)",
      "Global_implementation": false,
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
      "CN_name": "流美",
      "CN_implementation": false,
      "Global_name": "Rumi",
      "Global_implementation": true,
      "JP_name": "ルミ",
      "JP_implementation": true
    },
    {
      "CN_name": "玲纱",
      "CN_implementation": false,
      "Global_name": "Reisa",
      "Global_implementation": true,
      "JP_name": "レイサ",
      "JP_implementation": true
    },
    {
      "CN_name": "柚子(女仆)",
      "CN_implementation": false,
      "Global_name": "Yuzu (Maid)",
      "Global_implementation": true,
      "JP_name": "ユズ(メイド)",
      "JP_implementation": true
    },
    {
      "CN_name": "时(兔女郎)",
      "CN_implementation": false,
      "Global_name": "Toki (Bunny)",
      "Global_implementation": true,
      "JP_name": "トキ(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "爱丽丝(女仆)",
      "CN_implementation": false,
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
      "CN_name": "春香(正月)",
      "CN_implementation": false,
      "Global_name": "Haruka (New Year)",
      "Global_implementation": true,
      "JP_name": "ハルカ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "佳代子(正月)",
      "CN_implementation": false,
      "Global_name": "Kayoko (New Year)",
      "Global_implementation": true,
      "JP_name": "カヨコ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "小雪",
      "CN_implementation": false,
      "Global_name": "Koyuki",
      "Global_implementation": true,
      "JP_name": "コユキ",
      "JP_implementation": true
    },
    {
      "CN_name": "渚",
      "CN_implementation": false,
      "Global_name": "Nagisa",
      "Global_implementation": true,
      "JP_name": "ナギサ",
      "JP_implementation": true
    },
    {
      "CN_name": "时",
      "CN_implementation": false,
      "Global_name": "Toki",
      "Global_implementation": true,
      "JP_name": "トキ",
      "JP_implementation": true
    },
    {
      "CN_name": "樱子",
      "CN_implementation": false,
      "Global_name": "Sakurako",
      "Global_implementation": true,
      "JP_name": "サクラコ",
      "JP_implementation": true
    },
    {
      "CN_name": "叶渚",
      "CN_implementation": false,
      "Global_name": "Kanna",
      "Global_implementation": true,
      "JP_name": "カンナ",
      "JP_implementation": true
    },
    {
      "CN_name": "惠久",
      "CN_implementation": false,
      "Global_name": "Megu",
      "Global_implementation": true,
      "JP_name": "メグ",
      "JP_implementation": true
    },
    {
      "CN_name": "未花",
      "CN_implementation": false,
      "Global_name": "Mika",
      "Global_implementation": true,
      "JP_name": "ミカ",
      "JP_implementation": true
    },
    {
      "CN_name": "峰",
      "CN_implementation": false,
      "Global_name": "Mine",
      "Global_implementation": true,
      "JP_name": "ミネ",
      "JP_implementation": true
    },
    {
      "CN_name": "纯子(正月)",
      "CN_implementation": false,
      "Global_name": "Junko (New Year)",
      "Global_implementation": true,
      "JP_name": "ジュンコ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "风香(正月)",
      "CN_implementation": false,
      "Global_name": "Fuuka (New Year)",
      "Global_implementation": true,
      "JP_name": "フウカ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "晴奈(正月)",
      "CN_implementation": false,
      "Global_name": "Haruna (New Year)",
      "Global_implementation": true,
      "JP_name": "ハルナ(正月)",
      "JP_implementation": true
    },
    {
      "CN_name": "花江(圣诞节)",
      "CN_implementation": false,
      "Global_name": "Hanae (Christmas)",
      "Global_implementation": true,
      "JP_name": "ハナエ(クリスマス)",
      "JP_implementation": true
    },
    {
      "CN_name": "芹娜(圣诞节)",
      "CN_implementation": false,
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
      "CN_name": "莲见(运动服)",
      "CN_implementation": false,
      "Global_name": "Hasumi (Track)",
      "Global_implementation": true,
      "JP_name": "ハスミ(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "玛丽(运动服)",
      "CN_implementation": false,
      "Global_name": "Mari (Track)",
      "Global_implementation": true,
      "JP_name": "マリー(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "优香(运动服)",
      "CN_implementation": false,
      "Global_name": "Yuuka (Track)",
      "Global_implementation": true,
      "JP_name": "ユウカ(体操服)",
      "JP_implementation": true
    },
    {
      "CN_name": "茜(兔女郎)",
      "CN_implementation": false,
      "Global_name": "Akane (Bunny)",
      "Global_implementation": true,
      "JP_name": "アカネ(バニーガール)",
      "JP_implementation": true
    },
    {
      "CN_name": "响(应援团)",
      "CN_implementation": false,
      "Global_name": "Hibiki (Cheer Squad)",
      "Global_implementation": true,
      "JP_name": "ヒビキ(応援団)",
      "JP_implementation": true
    },
    {
      "CN_name": "诺亚",
      "CN_implementation": false,
      "Global_name": "Noa",
      "Global_implementation": true,
      "JP_name": "ノア",
      "JP_implementation": true
    },
    {
      "CN_name": "歌原(应援团)",
      "CN_implementation": false,
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
      "CN_implementation": false,
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
      "CN_implementation": false,
      "Global_name": "Chise (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "チセ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "泉奈(泳装)",
      "CN_implementation": false,
      "Global_name": "Izuna (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "イズナ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "静子(泳装)",
      "CN_implementation": false,
      "Global_name": "Shizuko (Swimsuit)",
      "Global_implementation": true,
      "JP_name": "シズコ(水着)",
      "JP_implementation": true
    },
    {
      "CN_name": "星野(泳装)",
      "CN_implementation": false,
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
