stage_data = {
    "SUB": "burst1",
    "story1": {
        'start': [
            ['burst1', (458, 468)],
        ],
        'action': [
            {'t': 'click', 'p': (650, 440), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (737, 414), "desc": "1 right"},
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
    "challenge2_sss": {
        'start': [
            ['mystic1', (817, 182)],
            ['pierce1', (484, 620)]
        ],
        'action': [
            {'t': 'click', 'p': (773, 371), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (686, 494), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'click', 'p': (631, 362), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (611, 401), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'choose_and_change', 'p': (611, 401), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (611, 401), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'click', 'p': (443, 386), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (667, 396), 'ec': True, 'wait-over': True, "desc": "2 left"},
        ]
    },
    "challenge2_task": {
        'start': [
            ['mystic1', (580, 513)]
        ],
        'action': [
            {'t': 'click', 'p': (718, 477), 'wait-over': True, "desc": "1 right"},

            {'t': 'click_and_teleport', 'p': (701, 354), 'wait-over': True, "desc": "1 upper right and tp"},

            {'t': 'click', 'p': (482, 380), "desc": "1 lower left"},

        ]
    },
    "challenge4_sss": {
        'start': [
            ['swipe', (778, 263, 778, 600, 0.5)],
            ['mystic1', (464, 71)],
            ['swipe', (962, 561, 400, 100, 0.5)],
            ['burst1', (937, 599)],
            ['swipe', (368, 464, 910, 464, 0.5)],
            ['burst2', (2, 635)]
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (610, 359), 'ec': True, "desc": "1 lower right and tp"},
            {'t': 'click', 'p': (722, 323), 'ec': True, "desc": "2 upper left"},
            {'t': 'click_and_teleport', 'p': (614, 416), 'ec': True, 'wait-over': True, "desc": "3 right and tp"},

            {'t': 'click', 'p': (506, 441), 'ec': True, "desc": "1 left"},
            {'t': 'click_and_teleport', 'p': (785, 374), 'wait-over': True, "desc": "2 choose self and tp"},
            {'t': 'click', 'p': (557, 416), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (793, 383), 'ec': True, 'wait-over': True, "desc": "3 lower right"},

            {'t': 'exchange_and_click', 'p': (557, 501), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (557, 501), "desc": "swap 1 2"},
            {'t': 'click', 'p': (496, 578), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (799, 386), 'wait-over': True, "desc": "3 lower right"},

            {'t': 'click', 'p': (655, 471), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'p': (896, 359), 'ec': True, "desc": "2 right and tp"},
            {'t': 'click', 'p': (694, 380), 'ec': True, 'wait-over': True, "desc": "3 upper left"},

            {'t': 'exchange_and_click', 'p': (587, 356), 'ec': True, "desc": "2 lower left"},
            {'t': 'exchange_twice_and_click', 'p': (658, 435), 'ec': True, "desc": "3 left"},
            {'t': 'click_and_teleport', 'p': (554, 487), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'choose_and_change', 'p': (685, 335), "desc": "swap 1 3"},
            {'t': 'click', 'p': (590, 452), "desc": "1 lower left"},
        ]
    },
    "challenge4_task": {
        'start': [
            ['mystic1', (82, 709)],
            ['swipe', (1034, 444, 500, 444, 0.5)],
            ['burst1', (1253, 269)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (613, 410), 'ec': True, "desc": "1 right and tp"},
            {'t': 'click_and_teleport', 'p': (715, 353), 'ec': True, 'wait-over': True, "desc": "2 upper left and tp"},

            {'t': 'exchange_and_click', 'p': (565, 524), 'ec': True, "desc": "2 lower left"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (607, 569), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (673, 380), "desc": "1 lower left"},
        ]
    }
}
