stage_data = {
    "challenge2_sss": {
        'start': [
            ['burst1', (580, 180)],
            ['burst2', (943, 427)]
        ],
        'action': [
            {'t': 'click', 'p': (644, 312), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (714, 523), 'ec': True, 'wait-over': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (618, 377), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (588, 501), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (531, 407), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (531, 407), "desc": "swap 1 2"},
            {'t': 'click', 'p': (407, 410), 'wait-over': True, "desc": "1 left"},

            {'t': 'exchange_and_click', 'p': (440, 294), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (559, 550), "desc": "1 left"},

        ]
    },
    "challenge2_task": {
        'start': [
            ['burst1', (909, 345)],
            ['burst2', (424, 202)]
        ],
        'action': [
            {'t': 'click', 'p': (717, 519), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (409, 320), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click', 'p': (660, 425), 'ec': True, "desc": "1 left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (681, 392), 'ec': True, "desc": "1 upper left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (639, 464), 'ec': True, "desc": "1 left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (526, 484), "desc": "1 left"},
            {'t': 'end-turn'},
        ]
    },
    "challenge4_sss": {
        'start': [
            ['burst1', (1088, 391)],
            ['pierce1', (15, 228)],
            ['burst2', (1199, 196)]
        ],
        'action': [
            {'t': 'click', 'p': (606, 486), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (558, 297), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (656, 351), 'ec': True, 'wait-over': True, "desc": "3 left"},

            {'t': 'exchange_and_click', 'p': (621, 362), 'wait-over': True, "desc": "2 right"},
            {'t': ['exchange_twice','click_and_teleport'], 'p': (761, 329), 'wait-over': True, "desc": "3 choose self and teleport"},
            {'t': 'click', 'p': (553, 460), 'ec': True, "desc": "3 left"},
            {'t': 'click_and_teleport', 'p': (749, 472), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'choose_and_change', 'p': (485, 350), "desc": "swap 1 3"},
            {'t': 'click', 'p': (386, 354), 'wait-over': True, "desc": "1 left"},

            {'t': 'click_and_teleport', 'p': (559, 591), 'ec': True, "desc": "1 lower left and tp"},
            {'t': 'click', 'p': (805, 259), 'ec': True, "desc": "2 right"},
            {'t': 'click_and_teleport', 'p': (758, 460), 'wait-over': True, "desc": "3 choose self and tp"},
            {'t': 'click', 'p': (833, 472), 'ec': True, 'wait-over': True, "desc": "3 lower right"},

            {'t': 'click', 'p': (558, 475), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', 'p': (558, 440), 'ec': True, "desc": "2 lower right and tp"},
            {'t': 'click', 'p': (725, 484), 'ec': True, 'wait-over': True, "desc": "3 lower left"},

            {'t': 'exchange_and_click', 'p': (615, 406), 'ec': True, "desc": "2 lower left"},
            {'t': 'exchange_twice_and_click', 'p': (666, 395), 'ec': True, "desc": "3 left"},
            {'t': 'choose_and_change', 'p': (610, 382), "desc": "swap 1 2"},
            {'t': 'click', 'p': (731, 383), "desc": "1 right"},
        ]
    },
    "challenge4_task": {
        'start': [
            ['burst1', (1088, 391)],
            ['pierce1', (15, 228)],
            ['burst2', (1199, 196)]
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (606, 486), 'ec': True, "desc": "1 left and tp"},
            {'t': 'click', 'p': (558, 272), 'ec': True, "desc": "2 upper right"},
            {'t': 'click_and_teleport', 'p': (656, 351), 'ec': True, 'wait-over': True, "desc": "3 left and tp"},

            {'t': 'exchange_and_click', 'p': (626, 345), 'ec': True, "desc": "2 right"},
            {'t': 'exchange_twice_and_click', 'p': (659, 434), 'ec': True, "desc": "3 left"},
            {'t': 'choose_and_change', 'p': (645, 413), "desc": "swap 1 3"},
            {'t': 'click', 'p': (525, 412), 'wait-over': True, "desc": "1 left"},

            {'t': 'click_and_teleport', 'p': (559, 591), 'ec': True, "desc": "1 lower left and tp"},
            {'t': 'click', 'p': (570, 282), 'ec': True, "desc": "2 left"},
            {'t': 'click_and_teleport', 'p': (772, 445), 'wait-over': True, "desc": "3 choose self and tp"},
            {'t': 'click', 'p': (839, 467), 'ec': True, 'wait-over': True, "desc": "3 lower left"},

            {'t': 'click', 'p': (556, 476), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (484, 388), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (714, 526), 'ec': True, 'wait-over': True, "desc": "3 lower left"},

            {'t': 'click', 'p': (650, 467), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'p': (651, 361), 'ec': True, "desc": "2 lower right and tp"},
            {'t': 'click', 'p': (663, 424), 'ec': True, 'wait-over': True, "desc": "3 left"},

            {'t': 'click', 'p': (615, 382), "desc": "1 left"},
            {'t': 'end-turn'}
        ]
    }
}
