stage_data = {
    '15-1-sss-present-task': {
        'start': [
            ['mystic1', (795, 560)],
            ['mystic2', (350, 470)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (900, 410), 'desc': "1 right and tp"},
            {'t': 'click', 'p': (555, 315), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (685, 230), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (555, 340), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (565, 355), 'ec': True, 'desc': "2 upper right"},
            {'t': 'choose_and_change', 'p': (570, 355), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (510, 275), 'wait-over': True, 'desc': "1 upper left"},

            {'t': 'exchange_and_click', 'p': (655, 410), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (450, 290), 'desc': "1 left"},
        ]
    },
    '15-2-sss-present-task': {
        'start': [
            ['mystic1', (400, 475)],
            ['mystic2', (700, 515)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (445, 485), 'desc': "1 lower left and tp"},
            {'t': 'click', 'p': (700, 320), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click_and_teleport', 'wait-over': True, 'p': (790, 475), 'desc': "1 lower right and tp"},
            {'t': 'click', 'p': (630, 270), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (670, 220), 'ec': True, 'desc': "2 upper right"},
            {'t': 'choose_and_change', 'p': (670, 275), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (725, 195), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'exchange_and_click', 'p': (765, 535), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (775, 280), 'desc': "1 right"},
        ]
    },
    '15-3-sss-present-task': {
        'start': [
            ['mystic1', (425, 600)],
            ['mystic2', (385, 225)],
            ['pierce1', (645, 155)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (545, 505), 'desc': "1 left and tp"},
            {'t': 'click', 'p': (670, 300), 'ec': True, 'desc': "2 right"},
            {'t': 'click_and_teleport', 'wait-over': True, 'p': (765, 270), 'desc': "3 right and tp"},

            {'t': 'exchange_and_click', 'p': (705, 370), 'ec': True, 'desc': "2 right"},
            {'t': ['exchange_twice', 'choose_and_change'], 'p': (705, 370), 'desc': "swap 2 3"},
            {'t': 'click', 'p': (820, 370), 'ec': True, 'desc': "3 right"},
            {'t': 'choose_and_change', 'p': (785, 375), 'desc': "swap 1 3"},
            {'t': 'click', 'p': (905, 375), 'wait-over': True, 'desc': "1 right"},

            {'t': 'click', 'p': (905, 380), 'ec': True, 'desc': "1 right"},
            {'t': 'click_and_teleport', 'p': (500, 425), "wait-over":True ,'desc': "2 tp"},
            {'t': 'click_and_teleport', 'p': (645, 155), 'wait-over': True, 'desc': "2 upper right and tp"},
            {'t': 'click', 'p': (695, 595), 'wait-over': True, 'desc': "3 upper right"},

            {'t': 'click', 'p': (815, 405), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (635, 205), 'ec': True, 'desc': "2 upper right"},
            {'t': 'end-turn'},

            {'t': 'exchange_and_click', 'p': (675, 355), 'ec': True, 'desc': "2 lower right"},
            {'t': 'exchange_twice_and_click', 'p': (465, 550), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (715, 425), 'desc': "1 lower left"},
        ]
    },
}
