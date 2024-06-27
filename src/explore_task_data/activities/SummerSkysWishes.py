stage_data = {
    "SUB": "burst1",
    "story1": {
        'start': [
            ['burst1', (344, 264)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (630, 330), 'wait-over': True, "desc": "1 right and tp"},
            {'t': 'click', 'p': (720, 464), "desc": "1 lower left"},
        ]
    },
    "story2": {
        'start': [
            ['burst1', (493, 383)],
        ],
        'action': [
            {'t': 'click', 'p': (629, 386), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (689, 467), "desc": "1 lower right"},
        ]
    },
    "story3": {
        'start': [
            ['burst1', (502, 386)],
        ],
        'action': [
            {'t': 'click', 'p': (637, 390), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (533, 491), 'wait-over': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (676, 467), "desc": "1 right"},
        ]
    },
    "story4": {
        'start': [
            ['burst1', (521, 387)],
        ],
        'action': [
            {'t': 'click', 'p': (757, 392), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (877, 390), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (731, 474), "desc": "1 lower right"},
        ]
    },
    "story5": {
        'start': [
            ['burst1', (463, 429)]
        ],
        'action': [
            {'t': 'click', 'p': (637, 418), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (682, 306), 'wait-over': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (739, 232), "desc": "1 upper right"},
        ]
    },
    "challenge1_sss": {
        'start': [
            ['pierce1', (823, 517)],
            ['burst1', (437, 374)]
        ],
        'action': [
            {'t': 'click', 'p': (884, 440), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (559, 443), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (503, 409), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (381, 424), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (503, 425), "desc": "2 choose self and tp"},
            {'t': 'click', 'p': (850, 267), 'ec': True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (725, 311), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (787, 229), 'wait-over': True, "desc": "1 upper right and tp"},

            {'t': 'click', 'p': (494, 275), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (634, 589), 'ec': True, 'wait-over': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (451, 294), 'ec': True, "desc": "1 left"},
            {'t': 'click_and_teleport', 'p': (832, 493), 'ec': True, 'wait-over': True, "desc": "2 right and tp"},

            {'t': 'exchange_and_click', 'p': (531, 365), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (531, 365), "desc": "swap 1 2"},
            {'t': 'click', 'p': (412, 364), "desc": "1 left"},
        ]
    },
    "challenge1_task": {
        'start': [
            ['pierce1', (523, 430)],
            ['burst1', (841, 513)]
        ],
        'action': [
            {'t': 'click', 'p': (556, 460), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (814, 368), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'click_and_teleport', 'p':(391, 448), 'ec': True, "desc": "1 left and tp"},
            {'t': 'click', 'p': (722, 279), 'ec': True, 'wait-over': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (650, 534), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', 'p': (708, 258), 'ec': True, 'wait-over': True, "desc": "2 upper right and tp"},

            {'t': 'click', 'p': (637, 591), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (637, 323), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click_and_teleport', 'p': (815, 504), 'ec': True, "desc": "1 right and tp"},
            {'t': 'click', 'p': (525, 276), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (500, 382), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (500, 382), "desc": "swap 1 2"},
            {'t': 'click', 'p': (385, 383), "desc": "1 left"},

        ]
    },
}
