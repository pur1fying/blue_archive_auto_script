stage_data = {
    '20-1-sss-present-task': {
        'start': [
            ['burst1', (284, 341)],
            ['pierce1', (1099, 537)],
        ],
        'action': [
            {'t': 'click', 'p': (562, 439), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (836, 348), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (614, 378), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (841, 300), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (556, 325), 'ec': True, 'desc': "1 upper right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (448, 270), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (641, 463), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (676, 390), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (484, 228), 'desc': "1 upper left"},
        ]
    },
    '20-2-sss-present-task': {
        'start': [
            ['burst1', (317, 426)],
            ['pierce1', (913, 164)],
        ],
        'action': [
            {'t': 'click', 'p': (640, 456), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (814, 401), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (757, 413), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (710, 423), 'ec': True, 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'exchange_and_click', 'p': (668, 383), 'ec': True, 'desc': "2 left"},
            {'t': 'choose_and_change', 'p': (668, 383), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (608, 302), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'click', 'p': (650, 204), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (592, 554), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange_and_click', 'p': (530, 587), 'ec': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (742, 194), 'desc': "1 upper right"},
        ]
    },
    '20-3-sss-present-task': {
        'start': [
            ['burst1', (760, 387)],
            ['pierce1', (352, 147)],
            ['burst2', (475, 702)],
        ],
        'action': [
            {'t': 'click', 'p': (725, 280), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (697, 285), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (536, 418), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'click', 'p': (829, 258), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (710, 283), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (586, 333), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'exchange_and_click', 'p': (812, 283), 'ec': True, 'desc': "2 right"},
            {'t': 'choose_and_change', 'p': (757, 322), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (874, 323), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (392, 447), 'ec': True, 'wait-over': True, 'desc': "3 left"},

            {'t': 'exchange_twice_and_click', 'p': (443, 335), 'ec': True, 'desc': "3 upper left"},
            {'t': 'click', 'p': (836, 429), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (646, 584), 'ec': True, 'wait-over': True ,'desc': "2 lower left"},

            {'t': 'exchange_and_click', 'p': (539, 581), 'ec': True, 'desc': "2 lower right"},
            {'t': 'exchange_twice_and_click', 'p': (439, 277), 'ec': True, 'desc': "3 upper left"},
            {'t': 'click', 'p': (727, 459), 'desc': "1 lower left"},
        ]
    },
}
