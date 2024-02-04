stage_data = {
    '18-1-sss-present-task': {
        'start': {
            'mystic1': (523, 60),
            'burst1': (358, 434),
        },
        'action': [
            {'t': 'click', 'p': (655, 362), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (569, 519), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (601, 447), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (586, 548), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (778, 380), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click_and_teleport', 'p': (661, 545), 'ec': True, 'wait-over': True, 'desc': "2 lower right and tp"},

            {'t': 'exchange_and_click', 'p': (820, 501), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (662, 360), 'wait-over': True, 'desc': "1 lower right"},

            {'t': 'exchange_and_click', 'p': (854, 476), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (673, 294), 'desc': "1 right"},
        ]
    },
    '18-2-sss-present-task': {
        'start': {
            'mystic1': (904, 264),
            'burst1': (187, 188),
        },
        'action': [
            {'t': 'click_and_teleport', 'p': (662, 416), 'ec': True, 'desc': "1 left and tp"},
            {'t': 'click', 'p': (592, 394), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (808, 529), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click_and_teleport', 'p': (680, 394), 'ec': True, 'wait-over': True, 'desc': "2 lower right and tp"},

            {'t': 'click', 'p': (559, 498), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (709, 251), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click_and_teleport', 'p': (620, 401), 'desc': "1 choose self and tp"},
            {'t': 'exchange_and_click', 'p': (619, 198), 'ec': True, 'desc': "2 upper left right"},
            {'t': 'click', 'p': (775, 509), 'wait-over': True, 'desc': "1 right"},

            {'t': 'exchange_and_click', 'p': (551, 191), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (811, 501), 'desc': "1 right"},
        ]
    },
    '18-3-sss-present-task': {
        'start': {
            'mystic1': (493, 141),
            'burst1': (1219, 357),
            'mystic2': (20, 463),
        },
        'action': [
            {'t': 'click', 'p': (680, 354), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (671, 381), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (379, 407), 'ec': True, 'wait-over': True, 'desc': "3 left"},

            {'t': 'click', 'p': (895, 351), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (667, 384), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (553, 474), 'ec': True, 'wait-over': True, 'desc': "3 lower right"},

            {'t': 'exchange_and_click', 'p': (667, 375), 'ec': True, 'desc': "2 right"},
            {'t': 'choose_and_change', 'p': (667, 375), 'desc': "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (667, 375), 'desc': "1 choose self and tp"},
            {'t': 'click', 'p': (779, 235), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (578, 540), 'wait-over': True, 'desc': "3 lower right"},

            {'t': 'exchange_twice_and_click', 'p': (598, 564), 'ec': True, 'desc': "3 lower right"},
            {'t': 'click', 'p': (854, 308), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (578, 549), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange_and_click', 'p': (613, 569), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (853, 330), 'desc': "1 right"},
        ]
    },
}
