stage_data = {
    '24-1-sss-present-task': {
        'start': [
            ['shock1', (403, 428)],
            ['burst1', (1044, 323)],
        ],
        'action': [
            {'t': 'click', 'p': (445, 327), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (665, 374), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click_and_teleport', 'p': (502, 427), 'desc': "1 choose self and tp"},
            {'t': 'click', 'p': (800, 511), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (665, 394), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (668, 562), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (604, 257), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click_and_teleport', 'p': (784, 507), 'ec': True, 'desc': "1 right and tp"},
            {'t': 'click', 'p': (461, 232), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (871, 320), 'desc': "1 right"},
        ]
    },
    '24-2-sss-present-task': {
        'start': [
            ['shock1', (401, 342)],
            ['burst1', (853, 198)],
        ],
        'action': [
            {'t': 'click', 'p': (565, 513), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (637, 317), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (610, 565), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click_and_teleport', 'p': (695, 278), 'desc': "2 choose self and tp"},
            {'t': 'click', 'p': (720, 371), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (764, 284), 'ec': True, 'desc': "2 upper right"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (683, 386), 'ec': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (460, 549), 'wait-over': True, 'desc': "1 lower left"},

            {'t': 'click_and_teleport', 'p': (707, 385), 'ec': True, 'desc': "1 upper right and tp"},
            {'t': 'click', 'p': (591, 193), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'choose_and_change', 'p': (607, 275), 'wait-over': True, 'desc': "change 1 2"},
            {'t': 'click', 'p': (663, 193), 'desc': "1 upper right"},
            {'t': 'end-turn'}
        ]
    },
    '24-3-sss-present-task': {
        'start': [
            ['shock1', (963, 261)],
            ['burst1', (476, 419)],
            ['shock2', (208, 192)],
        ],
        'action': [
            {'t': 'click', 'p': (719, 313), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (598, 379), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (570, 413), 'ec': True, 'wait-over': True, 'desc': "3 lower right"},

            {'t': 'click', 'p': (668, 397), 'ec': True, 'desc': "1 left"},
            {'t': 'choose_and_change', 'p': (668, 397), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (606, 308), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (430, 481), 'ec': True, 'wait-over': True, 'desc': "3 lower left"},

            {'t': 'click', 'p': (725, 489), 'ec': True, 'desc': "1 lower left"},
            {'t': 'exchange_and_click', 'p': (439, 513), 'ec': True, 'desc': "3 lower left"},
            {'t': 'click', 'p': (637, 317), 'wait-over': True, 'desc': "2 left"},

            {'t': 'click', 'p': (619, 589), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (744, 273), 'ec': True, 'desc': "2 right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (877, 461), 'ec': True, 'desc': "1 right"},
            {'t': 'click_and_teleport', 'p': (749, 199), 'ec': True, 'desc': "2 upper right and tp"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (805, 386), 'ec': True, 'desc': "2 right"},
            {'t': 'choose_and_change', 'p': (785, 388), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (901, 386), 'desc': "1 right"},
        ]
    },
}
