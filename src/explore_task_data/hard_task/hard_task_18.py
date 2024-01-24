stage_data = {
    '18-1-sss-present-task': {
        'start': {
            'pierce1': (670, 470),
            'mystic1': (370, 215),
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

            {'t': 'exchange_and_click', 'p': (725, 450), 'wait-over': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (445, 330), 'desc': "2 lower left"},
        ]
    },
    '18-2-sss-present-task': {
        'start': {
            'pierce1': (550, 385),
            'mystic1': (520, 560),
        },
        'action': [
            {'t': 'click', 'p': (565, 325), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (505, 410), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (455, 330), 'ec': True, 'desc': "1 upper left"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (395, 340), 'wait-over': True, 'desc': "1 left"},

            {'t': 'click', 'p': (440, 445), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (845, 455), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange_and_click', 'p': (728, 468), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (555, 475), 'desc': "1 lower right"},
        ]
    },
    '18-3-sss-present-task': {
        'start': {
            'pierce1': (940, 470),
            'mystic1': (170, 425),
            'pierce2': (380, 240),
        },
        'action': [
            {'t': 'click', 'p': (665, 415), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (550, 315), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (640, 320), 'ec': True, 'wait-over': True, 'desc': "3 right"},

            {'t': 'click', 'p': (720, 280), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (565, 265), 'ec': True, 'desc': "2 upper right"},
            {'t': 'choose_and_change', 'p': (645, 320), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (760, 315), 'ec': True, 'wait-over': True, 'desc': "3 right"},

            {'t': 'exchange_and_click', 'p': (440, 445), 'ec': True, 'desc': "2 lower left"},
            {'t': 'exchange_twice_and_click', 'p': (835, 430), 'wait-over': True, 'desc': "3 lower right"},
            {'t': 'choose_and_change', 'p': (665, 410), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (605, 495), 'wait-over': True, 'desc': "1 lower left"},

            {'t': 'exchange_twice_and_click', 'p': (845, 325), 'ec': True, 'desc': "3 upper left"},
            {'t': 'click', 'p': (435, 490), 'desc': "1 lower left"},
        ]
    },
}
