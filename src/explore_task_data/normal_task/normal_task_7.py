stage_data = {
    '7': {
        'SUB': 'burst1',
    },
    '7-1': {
        'start': {
            '1': (306, 470),
            '2': (511, 258)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2',
        },
        'action': [
            {'t': 'click', 'p': (663, 461), "desc": "1 right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (622, 342),"desc": "2 right"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'click', 'p': (657, 309), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (596, 560), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (789, 278),'ec': True, "desc": "1 right"},
            {'t': 'end-turn'},

        ]
    },
    '7-2': {
        'start': {
            '1': (373, 386),
            '2': (563, 306)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2',
        },
        'action': [
            {'t': 'exchange', 'ec': True, 'desc': 'change to 2'},
            {'t': 'click', 'p': (700, 475), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (700, 475), "desc": "choose 2"},
            {'t': 'click', 'p': (600, 475), "desc": "change 1 2"},
            {'t': 'click', 'p': (819, 476),  "desc": "1 right"},
            {'t': 'move', 'wait-over': True, "desc": "teleport"},

            {'t': 'click', 'p': (607, 490), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},

        ]
    },
    '7-3': {
        'start': {
            '1': (579, 385),
            '2': (938, 476)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2',
        },
        'action': [
            {'t': 'exchange', 'ec': True, 'desc': 'change to 2'},
            {'t': 'click', 'p': (718, 345), "desc": "2 upper left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (564, 438), "desc": "choose 2"},
            {'t': 'click', 'p': (462, 431), "desc": "change 1 2"},
            {'t': 'click', 'p': (503, 522),'wait-over':True , "desc": "1 lower left"},

            {'t': 'click', 'p': (425, 481),'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (682, 354), "desc": "2 lower right"},
            {'t': 'move', "desc": "teleport"},
        ]
    },
    '7-4': {
        'start': {
            '1': (395, 559),
            '2': (486, 370)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2',
        },
        'action': [
            {'t': 'click', 'p': (679, 463),'ec': True,  "desc": "1 right"},
            {'t': 'click', 'p': (619, 379), "desc": "2 right"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'click', 'p': (715, 403), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (815, 275), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange', 'ec': True, 'desc': 'change to 2'},
            {'t': 'click', 'p': (770, 417), "desc": "2 lower right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (644, 455), "desc": "choose 2"},
            {'t': 'click', 'p': (544, 455), "desc": "change 1 2"},
            {'t': 'click', 'p': (641, 458), "desc": "choose 1"},
            {'t': 'move', "desc": "teleport"},
            {'t': 'click', 'p': (880, 300), "desc": "1 right"},

        ]
    },
    '7-5': {
        'start': {
            '1': (523, 385),
            '2': (813, 309)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2',
        },
        'action': [
            {'t': 'exchange', 'ec': True, 'desc': 'change to 2'},
            {'t': 'click', 'p': (706, 418), "ec": True, "desc": "2 lower left"},
            {'t': 'click', 'p': (706, 418), "desc": "choose 2"},
            {'t': 'click', 'p': (606, 418), "desc": "change 1 2"},
            {'t': 'click', 'p': (767, 500), 'wait-over':True,"desc": "1 lower right"},

            {'t': 'click', 'p': (685, 565), "desc": "1 lower left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (555, 472),"desc": "2 lower right"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'exchange', 'ec': True, 'desc': 'change to 2'},
            {'t': 'click', 'p': (378, 423), 'ec': True,"desc": "2 left"},
            {'t': 'click', 'p': (889, 351), "desc": "1 right"},
        ]
    },
}
