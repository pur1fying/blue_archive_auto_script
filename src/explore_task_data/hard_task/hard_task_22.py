stage_data = {
    '22-1-sss-present-task': {
        'start': {
            'pierce1': (607, 511),
            'mystic1': (328, 225),
        },
        'action': [
            {'t': 'click', 'p': (665, 398), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click_and_teleport', 'p': (593, 225), 'ec': True, 'wait-over': True, 'desc': "2 upper right and tp"},

            {'t': 'exchange_and_click', 'p': (799, 385), 'ec': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (415, 470), 'wait-over': True, 'desc': "1 left"},

            {'t': 'click', 'p': (553, 299), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (886, 452), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange_and_click', 'p': (827, 363), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (568, 251), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'exchange_and_click', 'p': (704, 365), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (632, 335), 'desc': "2 right"},
        ]
    },
    '22-2-sss-present-task': {
        'start': {
            'pierce1': (964, 222),
            'mystic1': (349, 575),
        },
        'action': [
            {'t': 'click', 'p': (701, 405), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (586, 380), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (541, 356), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (854, 369), 'wait-over': True, 'ec': True, 'desc': "2 right"},

            {'t': ['exchange', 'choose_and_change'], 'p': (739, 300), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (854, 330), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (415, 422), 'wait-over': True, 'desc': "1 left"},

            {'t': 'click', 'p': (520, 287), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (655, 339), 'wait-over': True, 'ec': True, 'desc': "2 left"},

            {'t': 'click', 'p': (673, 315), 'wait-over': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (718, 277), 'desc': "2 upper left"},
        ]
    },
    '22-3-sss-present-task': {
        'start': {
            'pierce1': (550, 177),
            'mystic1': (1013, 712),
            'pierce2': (619, 144),
        },
        'action': [
            {'t': 'click', 'p': (467, 235), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (667, 404), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (680, 356), 'ec': True, 'wait-over': True, 'desc': "3 lower right"},

            {'t': 'exchange_twice_and_click', 'p': (790, 399), 'ec': True, 'desc': "3 lower right"},
            {'t': ['exchange', 'choose_and_change'], 'p': (790, 394), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (724, 317), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (430, 300), 'wait-over': True, 'desc': "1 left"},

            {'t': 'click', 'p': (448, 423), 'ec': True, 'desc': "1 lower left"},
            {'t': 'exchange_and_click', 'p': (640, 413), 'ec': True, 'desc': "3 upper left"},
            {'t': 'choose_and_change', 'p': (640, 413), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (526, 411), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (463, 402), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (700, 375), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (724, 309), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'exchange_and_click', 'p': (733, 384), 'ec': True, 'desc': "2 upper right"},
            {'t': ['exchange_twice', 'choose_and_change'], 'p': (667, 384), 'desc': "3 upper left"},
            {'t': 'click', 'p': (610, 303), 'ec': True, 'desc': "3 upper left"},
            {'t': 'choose_and_change', 'p': (637, 315), 'desc': "swap 1 3"},
            {'t': 'click', 'p': (700, 238), 'desc': "1 upper right"},

        ]
    },
}
