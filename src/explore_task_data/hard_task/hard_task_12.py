stage_data = {
    '12-1-sss-present-task': {
        'start': {
            '1': (335, 555),
            '2': (1130, 455)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (610, 395), 'wait-over': True, 'desc': "1 right"},
            {'t': 'click', 'p': (665, 390), 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (550, 310), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (725, 315), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (560, 345), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (680, 510), 'ec': True, 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (555, 505), 'wait-over': True, 'desc': "2 left"},
            {'t': 'click', 'p': (510, 250), 'desc': "1 upper left"},
        ]
    },
    '12-2-sss-present-task': {
        'start': {
            '1': (365, 385),
            '2': (620, 390)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (578, 475), 'wait-over': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (585, 480), 'desc': "choose 1"},
            {'t': 'click', 'p': (478, 468), 'desc': "change 1 2"},
            {'t': 'click', 'p': (640, 560), 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (785, 485), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (685, 235), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'click', 'p': (745, 270), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (800, 500), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (640, 415), 'wait-over': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (730, 275), 'desc': "1 right"},
        ]
    },
    '12-3-sss-present': {
        'start': {
            '1': (610, 385),
            '2': (580, 305)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (760, 390), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (760, 390), 'desc': "choose 2"},
            {'t': 'click', 'p': (660, 380), 'desc': "change 1 2"},
            {'t': 'click', 'p': (815, 310), 'desc': "2 upper right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},

            {'t': 'click', 'p': (895, 400), 'wait-over': True, 'desc': "1 right"},
            {'t': 'end-turn', 'wait-over': True},

            {'t': 'click', 'p': (730, 310), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (505, 390), 'ec': True, 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'click', 'p': (705, 250), 'desc': "1 upper left"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (725, 595), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (455, 290), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (605, 485), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (495, 380), 'desc': "1 lower left"}
        ]
    },
    '12-3-task': {
        'start': {
            '1': (610, 385),
            '2': (580, 305)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (760, 390), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (760, 390), 'desc': "choose 2"},
            {'t': 'click', 'p': (660, 380), 'desc': "change 1 2"},
            {'t': 'click', 'p': (815, 310), 'desc': "2 upper right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},

            {'t': 'click', 'p': (830, 315), 'desc': "1 upper right"},
            {'t': 'end-turn', 'wait-over': True},

            {'t': 'click', 'p': (710, 255), 'desc': "1 upper left"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'end-turn', 'wait-over': True},

            {'t': 'click', 'p': (400, 335), 'desc': "1 left"},
            {'t': 'end-turn', 'wait-over': True},

            {'t': 'click', 'p': (465, 400), 'desc': "1 lower left"},
        ]
    },
}
