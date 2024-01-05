stage_data = {
    '15-1-sss-present-task': {
        'start': {
            '1': (795, 560),
            '2': (350, 470)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'mystic2'
        },
        'action': [
            {'t': 'click', 'p': (900, 410), 'desc': "1 right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (555, 315), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (685, 230), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (555, 340), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (565, 355), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (570, 355), 'desc': "choose 2"},
            {'t': 'click', 'p': (460, 350), 'desc': "change 1 2"},
            {'t': 'click', 'p': (510, 275), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (655, 410), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (450, 290), 'desc': "1 left"},
        ]
    },
    '15-2-sss-present-task': {
        'start': {
            '1': (400, 475),
            '2': (700, 515)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'mystic2'
        },
        'action': [
            {'t': 'click', 'p': (445, 485), 'desc': "1 lower left"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (700, 320), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (790, 475), 'desc': "1 lower right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (630, 270), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (670, 220), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (670, 275), 'desc': "choose 2"},
            {'t': 'click', 'p': (563, 270), 'desc': "change 1 2"},
            {'t': 'click', 'p': (725, 195), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (765, 535), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (775, 280), 'desc': "1 right"},
        ]
    },
    '15-3-sss-present-task': {
        'start': {
            '1': (425, 600),
            '2': (385, 225),
            '3': (645, 155),
        },
        'attr': {
            '1': 'mystic1',
            '2': 'mystic2',
            '3': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (545, 505), 'desc': "1 left"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (670, 300), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (765, 270), 'desc': "3 right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (705, 370), 'ec': True, 'desc': "2 right"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 1"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 3"},
            {'t': 'click', 'p': (705, 370), 'desc': "choose 2"},
            {'t': 'click', 'p': (600, 365), 'desc': "change 2 3"},
            {'t': 'click', 'p': (820, 370), 'ec': True, 'desc': "3 right"},
            {'t': 'click', 'p': (785, 375), 'desc': "choose 3"},
            {'t': 'click', 'p': (680, 365), 'desc': "change 1 3"},
            {'t': 'click', 'p': (905, 375), 'wait-over': True, 'desc': "1 right"},

            {'t': 'click', 'p': (905, 380), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (500, 425), 'desc': "choose self"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (645, 155), 'desc': "2 upper right"},
            {'t': 'move', 'wait-over': True, 'desc': "teleport"},
            {'t': 'click', 'p': (695, 595), 'wait-over': True, 'desc': "3 upper right"},

            {'t': 'click', 'p': (815, 405), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (635, 205), 'ec': True, 'desc': "2 upper right"},
            {'t': 'end-turn', 'wait-over': True},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (675, 355), 'ec': True, 'desc': "2 lower right"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 3"},
            {'t': 'click', 'p': (465, 550), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (715, 425), 'desc': "1 lower left"},
        ]
    },
}
