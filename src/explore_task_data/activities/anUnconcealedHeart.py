stage_data = {
    "challenge2_sss": {
        'start': [
            ['pierce1', (275, 555)],
            ['mystic1', (527, 116)]
        ],
        'action': [
            {'t': 'click', 'p': (670, 415), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (684, 355), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click_and_teleport', 'p': (800, 500), 'ec': True, "desc": "1 right and tp"},
            {'t': 'click_and_teleport', 'p': (653, 311), 'ec': True, 'wait-over': True, "desc": "2 right and tp"},

            {'t': 'exchange_and_click', 'p': (726, 355), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (726, 355), "desc": "swap 1 2"},
            {'t': 'click', 'p': (842, 358), 'wait-over': True, "desc": "1 right"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (607, 455), 'wait-over': True,
             "desc": "2 choose self and tp"},
            {'t': 'click', 'p': (569, 479), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (895, 363), "desc": "1 right"},

        ]
    },
    "challenge2_task": {
        'start': [
            ['pierce1', (290, 225)]
        ],
        'action': [
            {'t': 'click', 'p': (568, 410), 'wait-over': True, "desc": "lower right"},
            {'t': 'click_and_teleport', 'p': (685, 409), 'wait-over': True, "desc": "right and tp"},
            {'t': 'click', 'p': (838, 459), 'wait-over': True, "desc": "lower right"},
            {'t': 'click', 'p': (888, 449), 'wait-over': True, "desc": "right"},
            {'t': 'click', 'p': (896, 425), "desc": "right"},
        ]
    },
    "challenge4_sss": {
        'start': [
            ['pierce1', (967, 344)],
            ['burst1', (665, 207)],
            ['mystic1', (535, 600)]
        ],
        'action': [
            {'t': 'click', 'p': (660, 346), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (532, 271), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (475, 502), 'ec': True, 'wait-over': True, "desc": "3 left"},

            {'t': 'click', 'p': (626, 309), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (514, 273), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (535, 416), 'ec': True, 'wait-over': True, "desc": "3 upper left"},

            {'t': 'exchange_and_click', 'p': (578, 357), 'ec': True, "desc": "2 lower left"},
            {'t': 'exchange_twice_and_click', 'p': (646, 417), 'ec': True, "desc": "3 upper right"},
            {'t': 'choose_and_change', 'p': (646, 417), "desc": "swap 1 3"},
            {'t': 'choose_and_change', 'p': (593, 334), "desc": "swap 1 2"},
            {'t': 'click', 'p': (470, 339), "desc": "1 left"},

        ]
    },
    "challenge4_task": {
        'start': [
            ['pierce1', (730, 516)],
            ['burst1', (814, 141)],
        ],
        'action': [
            {'t': 'click', 'p': (499, 507), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (579, 283), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click', 'p': (505, 408), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (547, 277), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (559, 359), 'ec': True, "desc": "2 lower left"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (635, 415), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (635, 415), "desc": "swap 1 2"},
            {'t': 'click', 'p': (576, 330), 'wait-over': True, "desc": "1 upper left"},

            {'t': 'click', 'p': (459, 330), 'ec': True, "desc": "1 left"},
            {'t': 'end-turn'},
        ]
    }
}
