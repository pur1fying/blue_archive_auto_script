stage_data = {
    '13': {
        'SUB': "pierce1"
    },
    '13-1': {
        'start': {
            'pierce1': (493, 305),
            'pierce2': (701, 570),
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (606, 374), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (574, 495), "wait-over": True, 'ec': True, "desc": "2 left"},
            # 第二回合
            {'t': 'click', 'p': (699, 344), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (461, 495), "wait-over": True, "desc": "2 left"},

            # 第三回合
            {'t': 'click', 'p': (851, 300), 'ec': True, "desc": "1 right"},
            {'t': 'end-turn'},
        ]
    },
    '13-2': {
        'start': {
            'pierce1': (728, 394),
            'pierce2': (409, 226),
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (630, 463), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (591, 400), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            # 第二回合
            {'t': 'click', 'p': (585, 565), 'ec': True, "desc": "lower left"},
            {'t': 'click', 'p': (666, 418), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            # 第三回合
            {'t': 'exchange_and_click', 'p': (823, 327), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (610, 570), "desc": "1 lower right"},
        ]
    },
    '13-3': {
        'start': {
            'pierce1': (427, 513),
            'pierce2': (779, 451),
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (579, 361), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (702, 354), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            # 第二回合
            {'t': 'choose_and_change', 'p': (782, 458), "desc": "swap 1 2"},
            {'t': 'click', 'p': (823, 357), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (722, 445), "wait-over": True, 'ec': True, "desc": "2 right"},

            # 第三回合
            {'t': 'click', 'p': (826, 282), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (762, 498), 'ec': True, "wait-over": True, "desc": "2 right"},

            # 第四回合
            {'t': 'click', 'p': (890, 365), "desc": "1 right"},
        ]
    },
    '13-4': {
        'start': {
            'pierce1': (580, 263),
            'pierce2': (875, 389),
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (604, 473), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (731, 473), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            # 第二回合
            {'t': 'exchange_and_click', 'p': (728, 473), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (728, 473), "desc": "swap 1 2"},
            {'t': 'click', 'p': (672, 567), "wait-over": True, "desc": "1 lower left"},

            # 第三回合
            {'t': 'click', 'p': (628, 475), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (738, 198), "desc": "2 upper right"},

        ]
    },
    '13-5': {
        'start': {
            'pierce1': (669, 223),
            'pierce2': (904, 419),
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (625, 355), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (651, 440), 'ec': True, "wait-over": True, "desc": "2 left"},

            # 第二回合
            {'t': 'exchange_and_click', 'p': (503, 371), 'ec': True, "desc": "2 left"},
            {'t': 'choose_and_change', 'p': (503, 371), "desc": "swap 1 2"},
            {'t': 'click', 'p': (443, 454), "wait-over": True, "desc": "1 lower left"},

            # 第三回合
            {'t': 'click', 'p': (454, 473), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (550, 275), 'ec': True, "wait-over": True, "desc": "2 left"},

            # 第四回合
            {'t': 'click', 'p': (476, 498), "desc": "1 lower left"},
        ]
    },
}
