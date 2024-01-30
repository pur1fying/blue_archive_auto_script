stage_data = {
    '10-1-task-present': {
        'start': {
            'burst1': (757, 260),
            'mystic1': (501, 284),
        },
        'action': [
            {'t': 'click', 'p': (701, 386), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (463, 384), 'wait-over': True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (441, 475), 'ec': True, "desc": "change to 2 and lower left"},
            {'t': 'click', 'p': (764, 398), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'click', 'p': (825, 476), "desc": "1 lower right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (832, 342), "desc": "1 upper right"},
        ]
    },
    '10-1-sss': {
        'start': {
            'burst1': (757, 260),
            'mystic1': (501, 284),
        },
        'action': [
            {'t': 'click', 'p': (642, 296), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (460, 386), 'ec': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (739, 396), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (440, 473), 'ec': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (645, 396), 'ec': True, "desc": "1 lower left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (849, 394), 'ec': True, "desc": "1 right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (901, 388), "desc": "1 right"},
        ]
    },

    '10-2-sss-present': {
        'start': {
            'burst1': (463, 260),
            'mystic1': (637, 305),
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (577, 472), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (583, 468), "desc": "swap 1 2"},
            {'t': 'click', 'p': (640, 555), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'exchange_and_click', 'p': (463, 425), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (743, 424), 'wait-over': True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (469, 234), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (773, 387), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (773, 265), "desc": "1 upper right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (897, 399), "desc": "1 right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (721, 490), "desc": "1 lower left"},
        ]
    },
    '10-2-task': {
        'start': {
            'burst1': (463, 260),
            'mystic1': (637, 305),
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (577, 472), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (583, 468), "desc": "swap 1 2"},
            {'t': 'click', 'p': (640, 555), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'exchange_and_click', 'p': (463, 425), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (743, 424), 'wait-over': True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (469, 234), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (773, 387), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (833, 349), "desc": "1 right"},
        ]
    },

    '10-3-sss-present': {
        'start': {
            'burst1': (697, 473),
            'mystic1': (328, 460),
        },
        'action': [
            {'t': 'click', 'p': (663, 406), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (558, 317), 'wait-over': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (672, 320), 'ec': True, "desc": "2 right"},
            {'t': 'choose_and_change', 'p': (481, 389), "desc": "swap 1 2"},
            {'t': 'click', 'p': (554, 306), 'wait-over': True, "desc": "1 upper right"},

            {'t': 'click', 'p': (499, 224), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (742, 505), 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (750, 416), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (567, 214), 'wait-over': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (468, 393), "desc": "1 lower left"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (391, 349), "desc": "1 left"},
        ]
    },
    '10-3-task': {
        'start': {
            'burst1': (697, 473),
            'mystic1': (328, 460),
        },
        'action': [
            {'t': 'click', 'p': (663, 406), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (558, 317), 'wait-over': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (672, 320), 'ec': True, "desc": "2 right"},
            {'t': 'choose_and_change', 'p': (481, 389), "desc": "swap 1 2"},
            {'t': 'click', 'p': (554, 306), 'wait-over': True, "desc": "1 upper right"},

            {'t': 'click', 'p': (499, 224), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (742, 505), 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (750, 416), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (506, 293), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (387, 347), "desc": "1 left"},

        ]
    },

}
