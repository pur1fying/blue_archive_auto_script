stage_data = {
    '9': {
        'SUB': 'burst1',
    },
    '9-1': {
        'start': {
            'burst1': (492, 302),
            'pierce1': (812, 398),
        },
        'action': [
            {'t': 'click', 'p': (441, 415), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (664, 407), "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (675, 491), "ec": True, "desc": "2 lower left"},
            {'t': 'click', 'p': (556, 482), "wait-over": True, "desc": "1 lower right"},

            {'t': 'exchange_and_click', 'p': (838, 279), "ec": True, "desc": "2 upper right"},
            {'t': 'click', 'p': (570, 532), "desc": "1 lower right"},

        ]
    },
    '9-2': {
        'start': {
            'burst1': (430, 345),
            'pierce1': (923, 443),
        },
        'action': [
            {'t': 'click', 'p': (618, 366), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (725, 500), 'wait-over': True, 'ec': True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (608, 485), "ec": True, "desc": "2 left"},
            {'t': 'click', 'p': (634, 328), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (657, 204), "desc": "1 upper right"},
        ]
    },
    '9-3': {
        'start': {
            'burst1': (430, 386),
            'pierce1': (623, 556),
        },
        'action': [
            {'t': 'click', 'p': (631, 326), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (688, 407), 'wait-over': True, 'ec': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (682, 421), "ec": True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (682, 421), "desc": "swap 1 2"},
            {'t': 'click', 'p': (807, 422), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (840, 506), "desc": "1 lower right"},
        ]
    },
    '9-4': {
        'start': {
            'burst1': (337, 555),
            'pierce1': (1116, 288),
        },
        'action': [
            {'t': 'click', 'p': (565, 352), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (713, 275), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (555, 331), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (653, 341), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (707, 418), "ec": True, "desc": "2 lower left"},
            {'t': 'click', 'p': (591, 396), "wait-over": True, "desc": "1 lower right"},

            {'t': 'click', 'p': (638, 440), 'ec': True, "desc": "1 right"},

        ]
    },
    '9-5': {
        'start': {
            'burst1': (433, 383),
            'pierce1': (626, 225),
        },
        'action': [

            {'t': 'click', 'p': (628, 425), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (695, 335), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (672, 354), "ec": True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (672,354), "desc": "swap 1 2"},
            {'t': 'click', 'p': (795, 355), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (902, 378), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (440, 303), "desc": "2 upper left"},
        ]
    },
}
