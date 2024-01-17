stage_data = {
    '11-1-sss-present-task': {
        'start': {
            'pierce1': (795, 470),
            'mystic1': (865, 445),
        },
        'action': [
            {'t': 'click', 'p': (530, 425), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (650, 420), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': ['exchange', 'choose_and_change'], 'p': (535, 420), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (475, 340), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (560, 430), 'wait-over': True, 'desc': "1 left"},

            {'t': 'exchange_and_click', 'p': (570, 280), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (515, 360), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'exchange_and_click', 'p': (515, 200), 'wait-over': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (450, 450), 'desc': "1 left"},
        ]
    },
    '11-2-sss-present': {
        'start': {
            'pierce1': (395, 390),
            'mystic1': (620, 560),
        },
        'action': [
            {'t': 'click', 'p': (570, 245), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (705, 415), 'desc': "2 upper right"},

            {'t': 'click', 'p': (680, 190), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (655, 430), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (700, 285), 'ec': True, 'wait-over': True, 'desc': "1 right"},
            {'t': 'click', 'p': (700, 540), 'wait-over': True, 'desc': "2 lower left"},

            {'t': 'exchange_and_click', 'p': (720, 420), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (665, 405), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (635, 370), 'wait-over': True, 'desc': "1 lower right"},

            {'t': 'exchange_and_click', 'p': (760, 365), 'ec': True, 'desc': "2 upper right"},
            {'t': 'choose_and_change', 'p': (760, 360), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (875, 375), 'desc': "1 right"},
        ]
    },
    '11-2-task': {
        'start': {
            'pierce1': (395, 390),
            'mystic1': (620, 560),
        },
        'action': [
            {'t': 'click', 'p': (570, 245), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (705, 415), 'desc': "2 upper right and tp"},

            {'t': 'click', 'p': (680, 190), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (655, 430), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (700, 285), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (700, 375), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (650, 415), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (765, 410), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'choose_and_change', 'p': (765, 415), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (885, 415), 'desc': "1 right"},
        ]
    },
    '11-3-sss-present-task': {
        'start': {
            'pierce1': (790, 305),
            'mystic1': (530, 490),
        },
        'action': [
            {'t': 'click', 'p': (820, 400), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (470, 370), 'desc': "2 upper left and tp"},

            {'t': 'click', 'p': (715, 505), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (630, 335), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'click', 'p': (695, 550), 'wait-over': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (670, 295), 'desc': "2 right"},
        ]
    },
}
