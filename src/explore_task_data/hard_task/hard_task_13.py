stage_data = {
    '13-1-sss-present-task': {
        'start': {
            'pierce1': (730, 260),
            'pierce2': (845, 440),
        },
        'action': [
            {'t': 'click', 'p': (585, 340), 'wait-over': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (645, 420), 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (555, 430), 'ec': True, 'desc': "2 left"},
            {'t': 'choose_and_change', 'p': (560, 430), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (500, 515), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'click', 'p': (430, 475), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (840, 290), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange_and_click', 'p': (885, 340), 'wait-over': True, 'desc': "2 right"},
            {'t': 'click', 'p': (400, 465), 'desc': "1 right"},
        ]
    },
    '13-2-sss-present': {
        'start': {
            'pierce1': (758, 222),
            'pierce2': (845, 445),
        },
        'action': [
            {'t': 'click', 'p': (590, 340), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (650, 425), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (600, 350), 'ec': True, 'desc': "2 left"},
            {'t': 'choose_and_change', 'p': (600, 350), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (480, 350), 'wait-over': True, 'desc': "1 left"},

            {'t': 'exchange_and_click', 'p': (825, 290), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (455, 365), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'click', 'p': (440, 450), 'desc': "1  lower left"},
        ]
    },
    '13-2-task': {
        'start': {
            'pierce1': (758, 222),
            'pierce2': (845, 445),
        },
        'action': [
            {'t': 'click', 'p': (590, 340), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (650, 425), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (600, 350), 'ec': True, 'desc': "2 left"},
            {'t': 'choose_and_change', 'p': (600, 350), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (480, 350), 'wait-over': True, 'desc': "1 left"},

            {'t': 'exchange_and_click', 'p': (825, 290), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (395, 445), 'desc': "1 left"},
        ]
    },
    '13-3-sss-present-task': {
        'start': {
            'pierce1': (785, 185),
            'pierce2': (365, 275),
        },
        'action': [
            {'t': 'click', 'p': (660, 355), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (615, 370), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange_and_click', 'p': (675, 450), 'ec': True, 'desc': "2 lower right"},
            {'t': 'choose_and_change', 'p': (675, 445), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (615, 535), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'click', 'p': (590, 535), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (795, 380), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange_and_click', 'p': (840, 435), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (595, 560), 'desc': "1 lower right"},
        ]
    },
}
