stage_data = {
    "mission1_sss": {
        'start': [
            ['mystic1', (760, 345)],
        ],
        'action': [
            {'t': 'click', 'p': (697, 477), "wait-over": True, 'desc': "lower right"},
            {'t': 'click', 'p': (638, 560), "wait-over": True, 'desc': "lower left"},
            {'t': 'click', 'p': (515, 513), "wait-over": True, 'desc': "left"},
            {'t': 'click', 'p': (481, 389), 'desc': "upper left"},
        ]
    },
    "mission2_sss": {
        'start': [
            ['mystic1', (493, 302)],
        ],
        'action': [
            {'t': 'click', 'p': (572, 399), "wait-over": True, 'desc': "lower right"},
            {'t': 'click', 'p': (694, 399), 'desc': "right"},
        ]
    },
    "mission3_sss": {
        'start': [
            ['pierce1', (551, 513)],
        ],
        'action': [
            {'t': 'click', 'p': (525, 389), "wait-over": True, 'desc': "upper left"},
            {'t': 'click', 'p': (624, 438), "wait-over": True, 'desc': "right"},
            {'t': 'click', 'p': (721, 442), 'desc': "right"},
        ]
    },
    "mission4_sss": {
        'start': [
            ['burst1', (403, 302)],
            ['mystic1', (685, 257)],
        ],
        'action': [
            {'t': 'click', 'p': (572, 539), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (831, 335), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'click', 'p': (613, 380), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (758, 363), 'wait-over': True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (613, 405), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (554, 482), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'click', 'p': (489, 572), "desc": "1 lower left"},
        ]
    },
    "mission4_task": {
        'start': [
            ['burst1', (407, 307)],
        ],
        'action': [
            {'t': 'click', 'p': (562, 422), "wait-over": True, 'desc': "lower right"},
            {'t': 'click', 'p': (610, 369), "wait-over": True, 'desc': "right"},
            {'t': 'click', 'p': (705, 363), "wait-over": True, 'desc': "right"},
            {'t': 'click', 'p': (647, 445), "wait-over": True, 'desc': "lower left"},
            {'t': 'click', 'p': (587, 336), 'desc': "lower left"},
        ]
    },
    "mission5_sss": {
        'start': [
            ['burst1', (582, 304)],
            ['mystic1', (877, 389)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (844, 480), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (435, 454), 'wait-over': True, "desc": "1 lower left"},

            {'t': 'click', 'p': (554, 488), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (730, 480), "desc": "2 lower right"},
        ]
    },
    "mission5_task": {
        'start': [
            ['burst1', (582, 304)],
            ['mystic1', (877, 389)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (844, 480), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (435, 454), 'wait-over': True, "desc": "1 lower left"},

            {'t': 'click', 'p': (554, 488), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},
        ]
    },
    "mission6_sss": {
        'start': [
            ['burst1', (522, 345)],
            ['pierce1', (643, 559)]
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (699, 426), 'ec': True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (699, 426), "desc": "swap 1 2"},
            {'t': 'click', 'p': (818, 423), 'wait-over': True, "desc": "1 left"},

            {'t': 'click', 'p': (696, 500), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (565, 266), "desc": "2 upper right"},
        ]
    },
    "mission6_task": {
        'start': [
            ['burst1', (522, 345)],
            ['pierce1', (643, 559)]
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (699, 426), 'ec': True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (699, 426), "desc": "swap 1 2"},
            {'t': 'click', 'p': (818, 423), 'wait-over': True, "desc": "1 left"},

            {'t': 'click', 'p': (696, 500), 'ec': True, "desc": "1 lower right"},
            {'t': 'end-turn'},
        ]
    },
    "mission7_sss": {
        'start': [
            ['burst1', (550, 386)],
            ['mystic1', (638, 560)]
        ],
        'action': [
            {'t': 'click_and_teleport', 'p': (522, 344), 'ec': True, "desc": "1 left and tp"},
            {'t': 'click', 'p': (469, 489), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click', 'p': (722, 469), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (454, 364), "desc": "2 upper left"},
        ]
    },
    "mission7_task": {
        'start': [
            ['burst1', (789, 432)],
        ],
        'action': [
            {'t': 'click', 'p': (814, 377), "wait-over": True, 'desc': "left"},
            {'t': 'click', 'p': (725, 313), "wait-over": True, 'desc': "left"},
            {'t': 'click', 'p': (581, 564), 'desc': "upper left"},
        ]
    },
    "mission8_sss": {
        'start': [
            ['burst1', (579, 559)],
            ['mystic1', (484, 478)]
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (590, 374), 'ec': True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (590, 374), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (534, 288), 'wait-over': True, "desc": "1 upper left and teleport"},

            {'t': 'exchange_and_click', 'p': (758, 479), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (684, 214),'wait-over': True, "desc": "1 upper left"},

            {'t': 'click', 'p': (784, 295), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (752, 420), "desc": "2 upper right"},
        ]
    },
    "mission8_task": {
        'start': [
            ['burst1', (579, 559)],
            ['mystic1', (484, 478)]
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (590, 374), 'ec': True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (590, 374), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (534, 288), 'wait-over': True, "desc": "1 upper left and teleport"},

            {'t': 'exchange_and_click', 'p': (758, 479), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (684, 214),'wait-over': True, "desc": "1 upper left"},

            {'t': 'click', 'p': (784, 295), 'ec': True, "desc": "1 upper right"},
            {'t': 'end-turn'}
        ]
    },
    "mission9_sss": {
        'start': [
            ['burst1', (728, 183)],
            ['mystic1', (333, 604)]
        ],
        'action': [
            {'t': 'click', 'p': (672, 380), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (660, 480), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': ['exchange', 'click_and_teleport'], 'p': (572, 595), 'ec': True, "desc": "2 lower right and tp"},
            {'t': 'choose_and_change', 'p': (653, 369), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (654, 379), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'click', 'p': (590, 354), 'wait-over': True, "desc": "1 right"},

            {'t': 'click_and_teleport', 'p': (844, 489), 'ec': True, "desc": "1 right and tp"},
            {'t': 'click', 'p': (626, 439), "desc": "2 lower left"},
        ]
    },
    "mission9_task": {
        'start': [
            ['burst1', (876, 224)],
            ['pierce1', (280, 482)]
        ],
        'action': [
            {'t': 'click', 'p': (659, 333), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (626, 439), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'click_and_teleport', 'p': (563, 349), 'ec': True, "desc": "1 lower left and tp"},
            {'t': 'click', 'p': (659, 333), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (563, 349), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (1, 1), "desc": "swap 1 2"},
            {'t': 'click', 'p': (670, 235), 'wait-over': True, "desc": "1 left"},

            {'t': 'click_and_teleport', 'p': (563, 349), 'wait-over': True, "desc": "1 choose self and tp"},
            {'t': 'click', 'p': (659, 333), "desc": "1 upper right"},
        ]
    },
    "challenge3_sss": {
        'start': [
            ['burst1', (583, 429)],
            ['pierce1', (584, 148)],
            ['mystic1', (584, 148)]
        ],
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    },
    "challenge3_task": {
        'start': [
            ['burst1', (583, 429)],
            ['pierce1', (584, 148)],
            ['mystic1', (584, 148)]
        ],
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    }
}
