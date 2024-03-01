stage_data = {
    '20': {
        'SUB': "burst1"
    },
    '20-1': {
        'start': [
            ['burst1', (581, 513)],
            ['pierce1', (421, 384)],
        ],
        'action': [
            {'t': 'click', 'p': (799, 471), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (557, 294), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (820, 356), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (589, 227), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (832, 345), 'ec': True, "desc": "upper right"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (382, 422), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (841, 280), "desc": "1 upper right"},
        ]
    },
    '20-2': {
        'start': [
            ['burst1', (407, 390)],
            ['pierce1', (742, 557)],
        ],
        'action': [
            {'t': 'click', 'p': (568, 252), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (667, 389), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'click', 'p': (601, 222), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (608, 423), 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (728, 275), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (478, 458), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (793, 219), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 470), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (854, 305), 'ec': True, "desc": "1 right"},
        ]
    },
    '20-3': {
        'start': [
            ['burst1', (311, 471)],
            ['pierce1', (979, 258)],
        ],
        'action': [
            {'t': 'click', 'p': (571, 519), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (710, 420), "wait-over": True, 'ec': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (650, 473), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (656, 338), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (614, 402), 'ec': True, "desc": "1 upper right"},
            {'t': 'choose_and_change', 'p': (614, 402), "desc": "swap 1 2"},
            {'t': 'click', 'p': (559, 325), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (679, 224), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (443, 335), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (628, 309), "desc": "1 left"},
        ]
    },
    '20-4': {
        'start': [
            ['burst1', (670, 560)],
            ['pierce1', (541, 154)],
        ],
        'action': [
            {'t': 'click', 'p': (616, 416), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (539, 351), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (641, 373), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (629, 366), "desc": "swap 1 2"},
            {'t': 'click', 'p': (578, 453), "wait-over": True, "desc": "1 lower right"},

            {'t': 'click', 'p': (472, 450), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (866, 437), 'wait-over': True, 'ec':True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (901, 401), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (377, 390), 'wait-over': True, "desc": "1 left"},

            {'t': 'exchange_and_click', 'p': (842, 311), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (437, 315), "desc": "1 upper left"},
        ]
    },
    '20-5': {
        'start': [
            ['burst1', (707, 557)],
            ['pierce1', (854, 232)],
        ],
        'action': [
            {'t': 'click', 'p': (536, 410), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (671, 212), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (596, 386), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (574, 278), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (511, 368), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (511, 368), "desc": "swap 1 2"},
            {'t': 'click', 'p': (398, 368), "wait-over": True, "desc": "1 left"},

            {'t': 'click', 'p': (502, 377), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (826, 495), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (823, 368), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (394, 338), "desc": "1 left"},
        ]
    },
}
