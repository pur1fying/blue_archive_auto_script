stage_data = {
    "challenge2_sss": {
        'start': [
            ['burst1', (850, 472)],
            ['mystic1', (339, 350)]
        ],
        'action': [
            {'t': 'click', 'p': (839, 510), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (562, 273), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (610, 486), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (406, 321), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (594, 231), 'ec': True, "desc": "1 upper right and tp"},
            {'t': 'choose_and_change', 'p': (665, 421), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (663, 422), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'click', 'p': (500, 332), 'wait-over': True, "desc": "1 lower left", 'post-wait': 4},

            {'t': 'click', 'p': (455, 415), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (844, 317), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (835, 282), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (511, 400), 'wait-over': True, "desc": "1 lower left"},

            {'t': 'click_and_teleport', 'p': (636, 449), 'ec': True, "desc": "1 lower right and tp"},
            {'t': 'end-turn'}
        ]
    },
    "challenge2_task": {
        'start': [
            ['burst1', (429, 381)],
            ['mystic1', (922, 472)]
        ],
        'action': [
            {'t': 'click', 'p': (554, 283), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (780, 358), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (444, 441), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (841, 326), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (618, 374), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (435, 517), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},

            {'t': 'click_and_teleport', 'p': (635, 453), 'ec': True, "desc": "1 lower right and tp"},
            {'t': 'end-turn'}
        ]
    }
}
