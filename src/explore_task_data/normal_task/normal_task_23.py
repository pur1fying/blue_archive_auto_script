stage_data = {
    '23': {
        'SUB': "burst1"
    },
    '23-1': {
        'start': [
            ['burst1', (430, 430)],
            ['pierce1', (874, 414)],
        ],
        'action': [
            {'t': 'click', 'p': (557, 319), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (664, 400), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (631, 327), 'ec': True, "desc": "1 right"},
            {'t': 'choose_and_change', 'p': (631, 327), "desc": "swap 1 2"},
            {'t': 'click', 'p': (516, 327), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (831, 414), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (444, 279), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (389, 342), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (763 ,411), "desc": "1 lower right"},
        ]
    },
    '23-2': {
        'start': [
            ['burst1', (401, 390)],
            ['pierce1', (802, 468)],
        ],
        'action': [
            {'t': 'click', 'p': (619, 373), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (641, 441), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (583, 534), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (655, 249), "wait-over": True, "desc": "1 upper right"},

            {'t': 'exchange_and_click', 'p': (477, 503), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (800, 280), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (614, 387), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (879, 322), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (450, 361), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (774, 394), "desc": "1 lower right"},
        ]
    },
    '23-3': {
        'start': [
            ['burst1', (671, 557)],
            ['pierce1', (303, 313)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (626, 339), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (703, 367), "wait-over": True, "desc": "1 upper left"},

            {'t': 'exchange_and_click', 'p': (560, 432), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (560, 432), "desc": "swap 1 2"},
            {'t': 'click', 'p': (506, 351), "wait-over": True, "desc": "1 upper left"},

            {'t': 'click', 'p': (643, 319), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (686, 558), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            {'t': 'click', 'p': (665, 191), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (601, 460), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (500, 507), 'ec': True, "desc": "2 left and tp"},
            {'t': 'choose_and_change', 'p': (709, 236), "desc": "swap 1 2"},
            {'t': 'click', 'p': (810, 280), "desc": "1 right"},
        ]
    },
    '23-4': {
        'start': [
            ['burst1', (817, 223)],
            ['pierce1', (623, 459)],
        ],
        'action': [
            {'t': 'click', 'p': (600, 290), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (530, 539), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (644, 587), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (587, 355), "wait-over": True, "desc": "1 lower left"},

            {'t': 'click', 'p': (470, 357), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (658, 572), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            {'t': 'click', 'p': (760, 369), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (742, 418), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (578, 403), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (578, 403), "desc": "swap 1 2"},
            {'t': 'click', 'p': (462, 403), "desc": "1 left"},
        ]
    },
    '23-5': {
        'start': [
            ['burst1', (704,515)],
            ['pierce1', (566, 139)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (563, 495), 'ec': True, "desc": "1 left"},
            {'t': 'choose_and_change', 'p': (548, 267), "desc": "swap 1 2"},
            {'t': 'click', 'p': (500, 378), "wait-over": True, 'ec': True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (660, 528), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (835, 421), "wait-over": True, "desc": "1 lower left"},

            {'t': 'exchange_and_click', 'p': (479, 564), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (828, 414), "wait-over": True, "desc": "1 lower right"},

            {'t': 'click', 'p': (613, 385), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (554, 472), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': ['exchange', 'click_and_teleport', 'teleport'], 'p': (613, 405), 'ec': True, "desc": "2 right and tp"},
            {'t': 'choose_and_change', 'p': (653, 448), "desc": "swap 1 2"},
            {'t': 'click', 'p': (586, 534), "desc": "1 lower left"},
        ]
    },
}
