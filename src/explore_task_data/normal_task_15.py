stage_data = {
    '15': {
        'SUB': "mystic1"  # 支线用神秘1
    },
    '15-1': {
        'start': {
            '1': (376, 344),  # 1队开始坐标
            '2': (1044, 609)  # 2队开始坐标
        },
        'attr': {
            '1': 'mystic1',  # 1队主神秘
            '2': 'mystic2'  # 2队副神秘
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (629, 329), 'ec': True},  # 主➡️
            {'t': 'click', 'p': (824, 365)},  # 副↗️
            {'t': 'move', 'ec': True, "wait-over": True},  # 传送
            # 第二回合
            {'t': 'exchange', 'ec': True},  # 切到副队
            {'t': 'click', 'p': (678, 357), 'ec': True},  # 副队↘️
            {'t': 'click', 'p': (679, 347)},  # 点击副队
            {'t': 'click', 'p': (576, 347)},  # 确认交换
            {'t': 'click', 'p': (794, 352), 'after': 10, 'wait-over': True},  # 主队➡️
            # 第三回合
            {'t': 'click', 'p': (823, 413), 'ec': True},  # 主队↘️
            {'t': 'click', 'p': (444, 446)},  # 副队↙️️
        ]
    },
    '15-2': {
        'start': {
            '1': (407, 259),  # 1队开始坐标
            '2': (751, 487)  # 2队开始坐标
        },
        'attr': {
            '1': 'mystic1',  # 1队主神秘
            '2': 'mystic2'  # 2队副神秘
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (636, 317), 'ec': True},  # 主➡️
            {'t': 'click', 'p': (673, 385), 'ec': True},  # 副↖️
            {'t': 'exchange', 'ec': True, 'before': 2},  # 切到副队
            # 第二回合
            {'t': 'click', 'p': (727, 349), 'ec': True},  # 副队先↗️
            {'t': 'click', 'p': (727, 342)},  # 点击副队
            {'t': 'click', 'p': (620, 344)},  # 确认交换
            {'t': 'click', 'p': (838, 344), 'after': 5, 'wait-over': True},  # 主队➡️
            # 第三回合
            {'t': 'exchange', 'ec': True, 'before': 2},  # 切到副队
            {'t': 'click', 'p': (432, 451)},  # 副队先↙️
            {'t': 'move', 'ec': True},  # 传送
            {'t': 'click', 'p': (814, 245)},  # 主队↗️
        ]
    },
    '15-3': {
        'start': {
            '1': (757, 144),  # 1队开始坐标
            '2': (407, 188)  # 2队开始坐标
        },
        'attr': {
            '1': 'mystic1',  # 1队主神秘
            '2': 'mystic2'  # 2队副神秘
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (728, 461), 'ec': True},  # 主↙️
            {'t': 'click', 'p': (576, 399)},  # 副↘️
            {'t': 'move', 'ec': True},  # 副队传送
            # 第二回合
            {'t': 'click', 'p': (680, 452)},  # 点击副队
            {'t': 'click', 'p': (572, 448)},  # 点击交换
            {'t': 'click', 'p': (623, 541), 'ec': True},  # 主队↙️️
            {'t': 'click', 'p': (797, 421), 'ec': True, 'wait-over': True},  # 副队↘️
            # 第三回合
            {'t': 'exchange', 'ec': True},  # 切换部队
            {'t': 'click', 'p': (835, 425)},  # 副队↘️
            {'t': 'move', 'ec': True},  # 确认传送
            # 第四回合
            {'t': 'click', 'p': (610, 459)},  # 点击副队
            {'t': 'click', 'p': (512, 452)},  # 点击交换
            {'t': 'click', 'p': (674, 537)},  # 主队↘️Boss
        ]
    },
    '15-4': {
        'start': {
            '1': (824, 554),  # 1队开始坐标
            '2': (665, 66)  # 2队开始坐标
        },
        'attr': {
            '1': 'mystic1',  # 1队主神秘
            '2': 'mystic2'  # 2队副神秘
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (546, 498), 'ec': True},  # 主⬅️
            {'t': 'click', 'p': (687, 343), 'ec': True, 'wait-over': True},  # 副↘️
            # 第二回合
            {'t': 'click', 'p': (547, 419), 'ec': True},  # 主队↖️
            {'t': 'click', 'p': (801, 275)},  # 副队➡️传送
            {'t': 'move', 'ec': True, 'wait-over': True},  # 确认传送
            # 第三回合
            {'t': 'exchange', 'ec': True},  # 切换部队
            {'t': 'click', 'p': (460, 498), 'ec': True},  # 副队↙️
            {'t': 'click', 'p': (528, 457)},  # 点击副队
            {'t': 'click', 'p': (423, 455)},  # 点击交换
            {'t': 'click', 'p': (408, 468), 'wait-over': True},  # 主队⬅️
            # 第四回合
            {'t': 'exchange', 'ec': True},  # 切换部队
            {'t': 'click', 'p': (897, 416), 'wait-over': True},  # 副队➡️
            {'t': 'click', 'p': (435, 446)},  # 主队↙️Boss
        ]
    },
    '15-5': {
        'start': {
            '1': (314, 300),  # 1队开始坐标
            '2': (490, 526)  # 2队开始坐标
        },
        'attr': {
            '1': 'mystic1',  # 1队主神秘
            '2': 'mystic2'  # 2队副神秘
        },
        'action': [
            # 第一回合
            {'t': 'exchange', 'ec': True},  # 切换部队
            {'t': 'click', 'p': (608, 384), 'ec': True},  # 副队↗️
            # 第二回合
            {'t': 'click', 'p': (610, 388)},  # 点击副队
            {'t': 'click', 'p': (505, 382)},  # 点击交换
            {'t': 'click', 'p': (730, 388), 'wait-over': True},  # 主队➡️
            # 第三回合
            {'t': 'click', 'p': (784, 218), 'ec': True},  # 主队↗️
            {'t': 'click', 'p': (579, 234)},  # 副队↗️
            {'t': 'move', 'ec': True, 'wait-over': True},  # 副队传送
            # 第四回合
            {'t': 'click', 'p': (788, 216)},  # 主队↗️
            {'t': 'move', 'ec': True, 'wait-over': True},  # 主队传送
            {'t': 'click', 'p': (651, 373), 'wait-over': True},  # 副队↙️
            # 第五回合
            {'t': 'click', 'p': (803, 491), 'ec': True},  # 主队➡️
            {'t': 'click', 'p': (734, 354), 'wait-over': True},  # 副队↘️
            {'t': 'click', 'p': (779, 511)},  # 主队➡️ Boss
        ]
    },
}
