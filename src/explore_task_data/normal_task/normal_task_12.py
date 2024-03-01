stage_data = {
    '12': {
        'SUB': "burst1"
    },
    '12-1': {
        'start': [
            ['mystic1', (370, 428)],
            ['burst1', (566, 328)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'ec': True, 'p': (640, 560), "desc": "1 lower right"},
            {'t': 'click', 'p': (704, 320), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (778, 373), 'ec': True, "desc": "2 right"},
            {'t': 'choose_and_change', 'p': (778, 373), "desc": "swap 1 2"},
            {'t': 'click', 'p': (901, 374), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (547, 556), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (772, 384), "desc": "1 lower right"},
        ]
    },
    '12-2': {
        'start': [
            ['mystic1', (733, 387)],
            ['burst1', (574, 474)],
        ],
        'action': [
            {'t': 'click', 'p': (581, 309), 'ec': True, "desc": "1 left"},
            {'t': 'choose_and_change', 'p': (581, 309), "desc": "swap 1 2"},
            {'t': 'click', 'p': (464, 306), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (526, 453), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (767, 401), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (845, 490), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (617, 383), "desc": "2 right"},
        ]
    },
    '12-3': {
        'start': [
            ['mystic1', (763, 558)],
            ['burst1', (586, 147)],
        ],
        'action': [
            {'t': 'click', 'p': (615, 413), 'ec': True},
            {'t': 'click', 'p': (724, 273), 'wait-over': True},

            {'t': ['exchange_and_click', 'teleport'],'wait-over':True, 'p': (642, 271)},
            {'t': 'click', 'p': (614, 350), 'ec': True},
            {'t': 'choose_and_change', 'p': (586, 371)},
            {'t': 'click', 'p': (471, 360), "wait-over": True},

            {'t': 'click', 'p': (440, 286), 'ec': True},
            {'t': 'end-turn'},
        ]
    },
    '12-4': {
        'start': [
            ['mystic1', (342, 386)],
            ['burst1', (619, 223)],
        ],
        'action': [
            {'t': 'click', 'p': (622, 424), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'ec': True, "wait-over": True, 'p': (746, 264), "desc": "2 right"},

            {'t': 'click', 'p': (657, 523), 'ec': True, "desc": "1 lower right"},
            {'t': 'choose_and_change', 'p': (654, 501), "desc": "swap 1 2"},
            {'t': 'click', 'p': (717, 588), "ec": True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (808, 496), 'ec': True, "desc": "2 right"},
            {'t': 'click_and_teleport', 'p': (579, 397), "desc": "1 teleport"},
            {'t': 'click', 'p': (700, 240), "desc": "1 right", "wait-over": True},

            {'t': 'click_and_teleport', 'p': (824, 291),'ec':True ,"desc": "1 right"},
            {'t': 'click', 'p': (740, 513), "desc": "2 right"},

        ]
    },
    '12-5': {
        'start': [
            ['mystic1', (549, 556)],
            ['burst1', (835, 478)],
        ],
        'action': [
            {'t': 'click_and_teleport', 'ec': True, 'p': (582, 359), "desc": "1 upper right"},
            {'t': 'choose_and_change', 'p': (781, 353), "desc": "swap 1 2"},
            {'t': 'click', 'p': (842, 272), "wait-over": True ,"desc": "2 upper right"},

            {'t': 'click_and_teleport', 'p': (665, 397),'ec':True ,"desc": "1 upper right"},
            {'t': 'click_and_teleport', 'p': (756, 317), "desc": "2 teleport"},
            {'t': 'click', 'p': (637, 327), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'click', 'p': (631, 386), 'ec': True, "desc": "1 upper left"},
            {'t': 'click_and_teleport', 'ec': True, 'p': (701, 248), "desc": "2 upper left"},

            {'t': 'click', 'p': (377, 392), 'ec': True, "desc": "1 left left"},
            {'t': 'click', 'p': (845, 309), 'ec': True, "desc": "2 upper right", "wait-over": True},

            {'t': 'exchange_and_click', 'p': (731, 299), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (385, 422), "desc": "1 left"},

        ]
    },
}
