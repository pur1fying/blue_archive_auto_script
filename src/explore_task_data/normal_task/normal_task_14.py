stage_data = {
    '14': {
        'SUB': "burst1"  # 支线用爆发1
    },
    '14-1': {
        'start': {
            '1': (460, 383),  # 1队开始坐标
            '2': (572, 303)  # 2队开始坐标
        },
        'attr': {
            '1': 'burst1',  # 1队爆发
            '2': 'mystic1'  # 2对神秘
        },
        'action': [
            # 第一回合
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (756, 388), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (636, 555), 'wait-over': True, "desc": "1 lower right"},
            # 第二回合
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (867, 316), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (619, 461), 'wait-over': True, "desc": "1 lower right"},
            # 第三回合
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (839, 298), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (669, 491), "desc": "1 right"},
        ]
    },
    '14-2': {
        'start': {
            '1': (611, 299),  # 1队开始做坐标
            '2': (880, 559)  # 2对开始坐标
        },
        'attr': {
            '1': 'burst1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (590, 396), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (685, 390), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            # 第二回合
            {'t': 'click', 'p': (514, 466), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (580, 380), 'ec': True, "wait-over": True, "desc": "2 left"},

            # 第三回合
            {'before': 2, 't': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (600, 228), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (545, 443), "wait-over": True, "desc": "1 left"},

            # 第四回合
            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (802, 280), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (493, 402), "desc": "1 upper left"},
        ]
    },
    '14-3': {
        'start': {
            '1': (583, 306),
            '2': (520, 560)
        },
        'attr': {
            '1': 'burst1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (745, 410), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (686, 491), "wait-over": True, 'ec': True, "desc": "2 right"},

            # 第二回合
            {'t': 'click', 'p': (866, 408), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (677, 396), "wait-over": True, "after": 5, "desc": "2 upper right"},

            # 第三回合
            {'t': 'click', 'p': (842, 317), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (412, 339), 'ec': True, "wait-over": True, "desc": "2 left"},

            # 第四回合
            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (439, 303), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (767, 399), "desc": "1 lower right"},

        ]
    },
    '14-4': {
        'start': {
            '1': (818, 302),
            '2': (535, 498)
        },
        'attr': {
            '1': 'burst1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (647, 317), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (610, 381), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            # 第二回合
            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (547, 302), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (547, 302), "desc": "choose 2"},
            {'t': 'click', 'p': (448, 293), "desc": "change 1 2"},
            {'t': 'click', 'p': (493, 219), "wait-over": True, "desc": "1 upper left"},

            # 第三回合
            {'before': 3, 't': 'click', 'p': (412, 315), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (763, 408), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            # 第四回合
            {'t': 'click', 'p': (454, 420), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (724, 512), "desc": "2 lower left"},

        ]
    },
    '14-5': {
        'start': {
            '1': (880, 388),
            '2': (246, 302)
        },
        'attr': {
            '1': 'burst1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (724, 330), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (559, 283), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            # 第二回合
            {'t': 'click', 'p': (540, 267), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (630, 336), 'ec': True, "wait-over": True, "desc": "2 right"},

            # 第三回合
            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (581, 407), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (581, 407), "desc": "choose 2"},
            {'t': 'click', 'p': (478, 401), "desc": "change 1 2"},
            {'t': 'click', 'p': (517, 494), "wait-over": True, "after": 5, "desc": "1 lower left"},

            # 第四回合
            {"before": 3, 't': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (727, 483), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (519, 409), "desc": "1 lower left"},
        ]
    },
}
