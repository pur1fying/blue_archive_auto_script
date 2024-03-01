stage_data = {
    '7': {
        'SUB': 'burst1',
    },
    '7-1': {
        'start': [
            ['burst1', (306, 470)],
            ['burst2', (511, 258)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'ec': True, 'p': (663, 461), "desc": "1 right and tp"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (622, 342), "desc": "2 right and tp"},

            {'t': 'click', 'p': (657, 309), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (596, 560), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (789, 278), 'ec': True, "desc": "1 right"},
            {'t': 'end-turn'},
        ]
    },
    '7-2': {
        'start': [
            ['burst1', (373, 386)],
            ['burst2', (563, 306)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (700, 475), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (700, 475), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (819, 476), 'wait-over': True, "desc": "1 right and tp"},

            {'t': 'click', 'p': (607, 490), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},

        ]
    },
    '7-3': {
        'start': [
            ['burst1', (579, 385)],
            ['burst2', (938, 476)],
        ],
        'action': [
            {'t': ['exchange', 'click_and_teleport'], 'p': (718, 345), 'ec': True, "desc": "2 upper left and tp"},
            {'t': 'choose_and_change', 'p': (564, 438), "desc": "swap 1 2"},
            {'t': 'click', 'p': (503, 522), 'wait-over': True, "desc": "1 lower left"},

            {'t': 'click', 'p': (425, 481), 'ec': True, "desc": "1 left"},
            {'t': 'click_and_teleport', 'p': (682, 354), "desc": "2 lower right"},
        ]
    },
    '7-4': {
        'start': [
            ['burst1', (395, 559)],
            ['burst2', (466, 365)],
        ],
        'action': [
            {'t': 'click', 'p': (679, 463), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'p': (619, 379), "wait-over": True, 'ec': True, "desc": "2 right and tp"},

            {'t': 'click', 'p': (715, 403), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (815, 275), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': ['exchange_and_click', 'teleport'], 'p': (770, 417), 'ec': True, "desc": "2 lower right and tp"},
            {'t': 'choose_and_change', 'p': (644, 455), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (641, 458), "wait-over": True, "desc": "1 teleport and tp"},
            {'t': 'click', 'p': (880, 300), "desc": "1 right"},

        ]
    },
    '7-5': {
        'start': [
            ['burst1', (523, 385)],
            ['burst2', (813, 309)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (706, 418), "ec": True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (706, 418), "desc": "swap 1 2"},
            {'t': 'click', 'p': (767, 500), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'click_and_teleport', 'ec': True, 'p': (685, 565), "desc": "1 lower left and tp"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (555, 472), "desc": "2 lower right and tp"},

            {'t': 'exchange_and_click', 'p': (378, 423), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (889, 351), "desc": "1 right"},
        ]
    },
}
