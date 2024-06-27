stage_data = {
    '26-1-sss-present-task': {
        'start': [
            ['mystic1', (461, 305)],
            ['burst1', (630, 674)],
        ],
        'action': [
            {'t': 'click', 'p': (637, 364), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click_and_teleport', 'p': (788, 502), 'ec': True, 'wait-over': True, 'desc': "2 right and tp"},

            {'t': 'exchange_and_click', 'p': (784, 377), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (508, 583), "wait-over": True, "desc": "1 lower left"},

            {'t': 'click', 'p': (686, 495), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (687, 190), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (765, 278), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (756, 508), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (696, 353), 'ec': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (700, 424), 'desc': "1 upper right"}
        ]
    },
    '26-2-sss-present-task': {
        'start': [
            ['mystic1', (700, 603)],
            ['burst1', (781, 159)],
        ],
        'action': [
            {'t': 'click', 'p': (555, 424), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (747, 359), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (674, 321), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (726, 476), 'wait-over': True, 'ec': True, 'desc': "2 lower left"},

            {'t': 'choose_and_change', 'p': (666, 404), 'desc': "swap 1 2"},
            {'t': 'exchange_and_click', 'p': (488, 489), 'ec': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (619, 195), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'click', 'p': (485, 354), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (647, 418), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (494, 275), 'wait-over': True, 'desc': "1 left"},
            {'t': 'click', 'p': (621, 418), 'desc': "2 upper left"},
        ]
    },
    '26-3-sss-present-task': {
        'start': [
            ['mystic1', (371, 305)],
            ['burst1', (1160, 431)],
            ['mystic2', (369, 484)],
        ],
        'action': [
            {'t': 'click', 'p': (565, 267), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (663, 406), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (622, 437), 'ec': True, 'wait-over': True, 'desc': "3 right"},

            {'t': 'exchange_twice_and_click', 'p': (720, 504), 'ec': True, 'desc': "3 right"},
            {'t': ['exchange', 'choose_and_change'], 'p': (717, 523), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (580, 501), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (454, 255), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'click', 'p': (600, 266), 'ec': True, 'desc': "1 upper right"},
            {'t': 'exchange_and_click', 'p': (663, 379), 'ec': True, 'desc': "3 left"},
            {'t': 'choose_and_change', 'p': (663, 379), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (606, 297), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (664, 303), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (626, 472), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (623, 476), 'ec': True, 'wait-over': True, 'desc': "3 left"},

            {'t': 'exchange_and_click', 'p': (720, 439), 'ec': True, 'desc': "2 lower left"},
            {'t': ['exchange_twice', 'choose_and_change'], 'p': (678, 394), 'wait-over': True, 'desc': "swap 2 3"},
            {'t': 'click', 'p': (556, 395), 'ec': True, 'desc': "3 left"},
            {'t': 'choose_and_change', 'p': (577, 406), 'desc': "swap 1 3"},
            {'t': 'click', 'p': (514, 493), 'ec': True, 'desc': "1 lower left"},
        ]
    },
}
