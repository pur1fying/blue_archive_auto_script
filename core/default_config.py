STATIC_DEFAULT_CONFIG = """
{
  "basic": {
    "activity_list": [
      "arena",
      "cafe_reward",
      "lesson",
      "group",
      "mail",
      "collect_daily_power",
      "common_shop",
      "tactical_challenge_power",
      "rewarded_task",
      "normal_task",
      "hard_task",
      "scrimmage",
      "clear_special_task_power",
      "collect_reward",
      "momo_talk",
      "create",
      "total_force_fight"
    ],
  },
  "totalForceFight": {
    "start_time": 0,
    "end_time": 1,
    "has_collect_reward": false
  }
}
"""
EVENT_DEFAULT_CONFIG = """
[
  {
    "enabled": true,
    "priority": 1,
    "interval": 10800,
    "next_tick": 1697280134,
    "event_name": "咖啡厅",
    "func_name": "cafe_reward"
  },
  {
    "enabled": true,
    "priority": 2,
    "interval": 0,
    "next_tick": 1697279908,
    "event_name": "日程",
    "func_name": "lesson"
  },
  {
    "enabled": true,
    "priority": 3,
    "interval": 1000,
    "next_tick": 1699453666,
    "event_name": "收集每日体力",
    "func_name": "collect_daily_power"
  },
  {
    "event_name": "收集小组体力",
    "func_name": "group",
    "next_tick": 1697279810,
    "priority": 4,
    "enabled": true,
    "interval": 0
  },
  {
    "enabled": true,
    "priority": 5,
    "interval": 0,
    "next_tick": 1697280258,
    "event_name": "查收邮箱",
    "func_name": "mail"
  },
  {
    "enabled": true,
    "priority": 6,
    "interval": 0,
    "next_tick": 1697279828,
    "event_name": "商店购买",
    "func_name": "common_shop"
  },
  {
    "enabled": true,
    "priority": 7,
    "interval": 0,
    "next_tick": 1697279828,
    "event_name": "竞技场商店购买",
    "func_name": "tactical_challenge_shop"
  },
  {
    "enabled": true,
    "priority": 8,
    "interval": 0,
    "next_tick": 1697280038,
    "event_name": "普通关清体力",
    "func_name": "normal_task"
  },
  {
    "enabled": true,
    "priority": 8,
    "interval": 0,
    "next_tick": 1697280038,
    "event_name": "困难关清体力",
    "func_name": "hard_task"
  },
  {
    "enabled": true,
    "priority": 9,
    "interval": 0,
    "next_tick": 1697279418,
    "event_name": "每日特别委托",
    "func_name": "clear_special_task_power"
  },
  {
    "enabled": true,
    "priority": 10,
    "interval": 0,
    "next_tick": 1697279503,
    "event_name": "悬赏通缉",
    "func_name": "rewarded_task"
  },
  {
    "enabled": true,
    "priority": 11,
    "interval": 0,
    "next_tick": 1697279787,
    "event_name": "竞技场",
    "func_name": "arena"
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 0,
    "next_tick": 1697280685,
    "event_name": "自动制造",
    "func_name": "create"
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 0,
    "next_tick": 1697279362,
    "event_name": "总力战",
    "func_name": "total_force_fight"
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 0,
    "next_tick": 1697280072,
    "event_name": "自动MomoTalk",
    "func_name": "momo_talk"
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 0,
    "next_tick": 1697287970,
    "event_name": "收集奖励",
    "func_name": "collect_reward"
  },
  {
    "enabled": true,
    "priority": 0,
    "interval": 0,
    "next_tick": 1697280134,
    "event_name": "学院交流会",
    "func_name": "scrimmage"
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
   "purchase_arena_ticket_times": "0",
    "screenshot_interval": "0.1",
    "ArenaLevelDiff": 5,
    "maxArenaRefreshTimes": 10,
    "createPriority": "花>Mo>情人节>果冻>色彩>灿烂>光芒>玲珑>白金>黄金>铜>白银>金属>隐然",
    "createTime": "3",
    "totalForceFightDifficulty": "NORMAL",
    "hardPriority": "1-1-1",
    "mainlinePriority": "5-1-1",
    "rewarded_task_times": "2,2,2",
    "purchase_rewarded_task_ticket_times": "0",
    "special_task_times": "1,1",
    "purchase_scrimmage_ticket_times": "0",
    "scrimmage_times": "2,2,2",
    "patStyle": "地毯",
    "antiHarmony": true,
    "bannerVisibility": true,
    "favorStudent": [
        "爱丽丝"
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
    "purchase_lesson_ticket_times": "0",
    "explore_normal_task_regions": [

    ],
    "explore_hard_task_regions": [

    ],
    "manual_boss": false,
    "burst1": "1",
    "burst2": "2",
    "pierce1": "1",
    "pierce2": "2",
    "mystic1": "1",
    "mystic2": "2",
    "TacticalChallengeShopRefreshTime": "0",
    "TacticalChallengeShopList": [
        0,
        0,
        0,
        1,
        1,
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
        "config": "featureSwitch",
        "name": "功能开关",
        "sort": 0,
        "tip": "重要，此处为功能开关，控制各功能是否开启，启动前请检查是否开启。",
        "type": "SwitchSettingCard"
    },
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
        "config": "specialDaily",
        "name": "悬赏通缉",
        "sort": 10,
        "tip": "帮助你打每日悬赏通缉",
        "type": "SpecStageSettingCard"
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
    }
]

'''
