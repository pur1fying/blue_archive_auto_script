stage_data = {
    '16-1-sss-present-task': {
        'start': {
            '1': (670, 470),
            '2': (370, 215)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (605, 475), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (590, 385), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (565, 500), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (515, 410), 'ec': True, 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'click', 'p': (508, 580), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (630, 410), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (395, 450), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (900, 365), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (725, 450), 'wait-over': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (445, 330), 'desc': "2 lower left"},
        ]
    },
    '16-2-sss-present-task': {
        'start': {
            '1': (550, 385),
            '2': (520, 560)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (565, 325), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (505, 410), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (455, 330), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (510, 345), 'desc': "choose 2"},
            {'t': 'click', 'p': (405, 335), 'desc': "change 1 2"},
            {'t': 'click', 'p': (395, 340), 'wait-over': True, 'desc': "1 left"},

            {'t': 'click', 'p': (440, 445), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (845, 455), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (728, 468), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (555, 475), 'desc': "1 lower right"},
        ]
    },
    '16-3-sss-present-task': {
        'start': {
            '1': (940, 470),
            '2': (170, 425),
            '3': (380, 240),
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1',
            '3': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (665, 415), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (550, 315), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (640, 320), 'ec': True, 'wait-over': True, 'desc': "3 right"},

            {'t': 'click', 'p': (720, 280), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (565, 265), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (645, 320), 'desc': "choose 2"},
            {'t': 'click', 'p': (543, 313), 'desc': "change 2 3"},
            {'t': 'click', 'p': (760, 315), 'ec': True, 'wait-over': True, 'desc': "3 right"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'click', 'p': (440, 445), 'ec': True, 'desc': "2 lower left"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 3"},
            {'t': 'click', 'p': (835, 430), 'wait-over': True, 'desc': "3 lower right"},
            {'t': 'click', 'p': (665, 410), 'desc': "choose 2"},
            {'t': 'click', 'p': (565, 405), 'desc': "change 1 2"},
            {'t': 'click', 'p': (605, 495), 'wait-over': True, 'desc': "1 lower left"},

            {'t': 'exchange', 'ec': True, 'desc': "change to 2"},
            {'t': 'exchange', 'ec': True, 'desc': "change to 3"},
            {'t': 'click', 'p': (845, 325), 'ec': True, 'desc': "3 upper left"},
            {'t': 'click', 'p': (435, 490), 'desc': "1 lower left"},
        ]
    },
}
