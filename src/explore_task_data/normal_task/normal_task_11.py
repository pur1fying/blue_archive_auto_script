stage_data = {
    '11': {
        'SUB': "pierce1"
    },
    '11-1': {
        'start': [
            ['pierce1', (496, 525)],
            ['mystic1', (794, 130)],
        ],
        'action': [
            {'t': 'click', 'p': (499, 412), 'ec': True, "desc": "1 upper left"},
            {'t': 'click_and_teleport', 'p': (775, 368), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (556, 317), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (802, 388), "wait-over": True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (653, 434), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (469, 245), "desc": "1 upper left"},
        ]
    },
    '11-2': {
        'start': [
            ['pierce1', (281, 347)],
            ['mystic1', (791, 287)],
        ],
        'action': [
            {'t': 'click', 'p': (553, 478), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (823, 406), "desc": "2 lower right"},

            {'t': 'click', 'p': (616, 371), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (904, 412), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (553, 469), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (662, 419), "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (715, 270), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (624, 451), "desc": "1 right"},
        ]
    },
    '11-3': {
        'start': [
            ['pierce1', (315, 466)],
            ['mystic1', (919, 178)],
        ],
        'action': [
            {'t': 'click', 'p': (635, 461), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'ec': True, "wait-over": True, 'p': (693, 397), "desc": "2 lower left"},

            {'t': 'click', 'p': (613, 422), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (672, 365), "ec": True, "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (716, 427), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (555, 511), "desc": "1 lower right"},
        ]
    },
    '11-4': {
        'start': [
            ['pierce1', (940, 350)],
            ['mystic1', (841, 285)],
        ],
        'action': [

            {'t': 'click', 'p': (647, 323), 'ec': True, "desc": "1 upper left"},
            {'t': 'choose_and_change', 'p': (648, 318), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'ec': True, "wait-over": True, 'p': (530, 321), "desc": "2 left and tp"},

            {'t': 'click', 'p': (642, 330), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (558, 446), "ec": True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'click_and_teleport', 'p': (634, 318), 'ec': True, "desc": "1 left and tp"},
            {'t': 'click', 'p': (434, 422), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'choose_and_change', 'p': (494, 404), "desc": "swap 1 2"},
            {'t': 'click', 'p': (433, 489), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (525, 249), "desc": "2 left"},

        ]
    },
    '11-5': {
        'start': [
            ['pierce1', (374, 429)],
            ['mystic1', (1114, 591)],
        ],
        'action': [
            {'t': ['exchange', 'click_and_teleport'], 'ec': True, 'p': (719, 351), "desc": "2 upper left"},
            {'t': 'click', 'p': (613, 371), "desc": "1 right", "wait-over": True},

            {'t': 'click', 'p': (729, 377), "ec": True, "desc": "1 right"},
            {'t': 'click', 'p': (616, 216), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            {'t': 'click', 'p': (868, 437), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (683, 290), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click_and_teleport', 'ec': True, 'p': (715, 523), "desc": "1 lower left"},
            {'t': 'click', 'p': (835, 288), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (586, 549), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (662, 306), "desc": "1 right"},

        ]
    },
}
