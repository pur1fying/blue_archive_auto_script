stage_data = {
    "challenge2_sss": {
        'start': [
            ['pierce1', (1081, 471)],
            ['mystic1', (871, 387)]
        ],
        'action': [
            {'t': 'click', 'p': (616, 375), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (896, 360), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click_and_teleport', 'p': (616, 375), 'ec': True, "desc": "1 right and tp"},
            {'t': 'click_and_teleport', 'p': (896, 360), 'ec': True, 'wait-over': True, "desc": "2 right and tp"},

            {'t': 'exchange_and_click', 'p': (652, 321), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (568, 189), "desc": "swap 1 2"},
            {'t': 'click', 'p': (580, 242), 'wait-over': True, "desc": "1 right"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (790, 405), 'wait-over': True, "desc": "2 choose self and tp"},
            {'t': 'click', 'p': (680, 328), "desc": "1 right"},

        ]
    },
    "challenge2_task": {
        'start': [
            ['pierce1', (1081, 471)]
        ],
        'action': [
            {'t': 'click', 'p': (571, 420), 'wait-over': True, "desc": "lower right"},
            {'t': 'click_and_teleport', 'p': (571, 420), 'wait-over': True, "desc": "right and tp"},
            {'t': 'click', 'p': (571, 420), 'wait-over': True, "desc": "lower right"},
            {'t': 'click', 'p': (571, 420), 'wait-over': True, "desc": "right"},
            {'t': 'click', 'p': (571, 420), 'wait-over': True, "desc": "right"},
        ]
    },
    "challenge4_sss": {
        'start': [
            ['pierce1', (493, 380)],
            ['burst1', (871, 387)],
            ['mystic', (1081, 471)]
        ],
        'action': [
            {'t': 'click', 'p': (616, 375), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (721, 333), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (571, 420), 'ec': True, 'wait-over': True, "desc": "3 left"},

            {'t': 'click', 'p': (616, 375), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (721, 333), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (571, 420), 'ec': True, 'wait-over': True, "desc": "3 upper left"},

            {'t': 'exchange_and_click', 'p': (565, 267), 'ec': True, "desc": "2 lower left"},
            {'t': 'exchange_twice_and_click', 'p': (565, 267), 'ec': True, "desc": "3 upper right"},
            {'t': 'choose_and_change', 'p': (568, 189), "desc": "swap 1 3"},
            {'t': 'choose_and_change', 'p': (568, 189), "desc": "swap 1 2"},
            {'t': 'click', 'p': (683, 359), "desc": "1 left"},

        ]
    },
    "challenge4_task": {
        'start': [
            ['pierce1', (493, 380)],
            ['burst1', (871, 387)],
        ],
        'action': [
            {'t': 'click', 'p': (616, 375), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (571, 420), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click', 'p': (557, 333), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (694, 558), 'ec': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (565, 267), 'ec': True, "desc": "2 lower left"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (652, 321), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (568, 189), "desc": "swap 1 2"},
            {'t': 'click', 'p': (580, 242), 'wait-over': True, "desc": "1 upper left"},

            {'t': 'click', 'p': (683, 359),'ec':True , "desc": "1 left"},
            {'t': 'end-turn'},
        ]
    }
}
