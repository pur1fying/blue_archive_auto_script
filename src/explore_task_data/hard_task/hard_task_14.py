stage_data = {
    '14-1-sss-present-task': {
        'start': {
            'burst1': (550, 305),
            'mystic1': (581, 686),
        },
        'action': [
            {'t': 'click', 'p': (785, 275), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (715, 500), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'click', 'p': (780, 375), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (715, 420), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (895, 340), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (665, 365), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (412, 322), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (760, 405), 'wait-over': True, 'desc': "1 lower right"},

            {'t': 'exchange_and_click', 'p': (450, 420), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (715, 515), 'desc': "1 lower left"},
        ]
    },
    '14-2-sss-present-task': {
        'start': {
            'burst1': (875, 305),
            'mystic1': (475, 585),
        },
        'action': [
            {'t': 'click', 'p': (690, 390), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (605, 395), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (640, 320), 'ec': True, 'desc': "1 left"},
            {'t': 'choose_and_change', 'p': (643, 323), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (580, 235), 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'exchange_and_click', 'p': (520, 275), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (565, 445), 'wait-over': True, 'desc': "1 left"},

            {'t': 'exchange_and_click', 'p': (620, 200), 'wait-over': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (575, 425), 'desc': "1 upper left"},
        ]
    },
    '14-3-sss-present-task': {
        'start': {
            'burst1': (875, 345),
            'mystic1': (425, 200),
        },
        'action': [
            {'t': 'click', 'p': (655, 430), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (460, 405), 'ec': True, 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'click', 'p': (630, 465), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (550, 465), 'ec': True, 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'exchange_and_click', 'p': (625, 460), 'ec': True, 'desc': "2 lower right"},
            {'t': 'choose_and_change', 'p': (625, 460), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (565, 545), 'wait-over': True, 'desc': "1 lower left"},

            {'t': 'click', 'p': (390, 435), 'wait-over': True, 'desc': "1 left"},
            {'t': 'click', 'p': (825, 250), 'desc': "2 upper right"},
        ]
    },
}
