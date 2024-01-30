stage_data = {
    '15': {
        'SUB': "mystic1"
    },
    '15-1': {
        'start': {
            'mystic1': (376, 344),
            'mystic2': (1044, 609),
        },
        'action': [

            {'t': 'click', 'p': (629, 329), 'ec': True},
            {'t': 'click_and_teleport', 'ec': True, "wait-over": True, 'p': (824, 365)},

            {'t': 'exchange_and_click', 'p': (678, 357), 'ec': True},
            {'t': 'choose_and_change', 'p': (679, 347)},
            {'t': 'click', 'p': (794, 352), 'wait-over': True},

            {'t': 'click', 'p': (823, 413), 'ec': True},
            {'t': 'click', 'p': (444, 446)},
        ]
    },
    '15-2': {
        'start': {
            'mystic1': (407, 259),
            'mystic2': (751, 487),
        },
        'action': [

            {'t': 'click', 'p': (636, 317), 'ec': True},
            {'t': 'click', 'p': (673, 385), 'ec': True},

            {'t': 'exchange_and_click', 'p': (727, 349), 'ec': True},
            {'t': 'choose_and_change', 'p': (727, 342)},
            {'t': 'click', 'p': (838, 344), 'wait-over': True},

            {'t': ['exchange_and_click','teleport'], 'ec': True, 'p': (432, 451)},
            {'t': 'click', 'p': (814, 245)},
        ]
    },
    '15-3': {
        'start': {
            'mystic1': (757, 144),
            'mystic2': (407, 188),
        },
        'action': [

            {'t': 'click', 'p': (728, 461), 'ec': True},
            {'t': 'click_and_teleport', 'ec': True, 'p': (576, 399)},

            {'t': 'choose_and_change', 'p': (680, 452)},
            {'t': 'click', 'p': (623, 541), 'ec': True},
            {'t': 'click', 'p': (797, 421), 'ec': True, 'wait-over': True},

            {'t': 'exchange_and_click', 'ec': True, 'p': (835, 425)},
            {'t': 'choose_and_change', 'p': (610, 459)},
            {'t': 'click', 'p': (512, 452)},
            {'t': 'click', 'p': (674, 537)}
        ]
    },
    '15-4': {
        'start': {
            'mystic1': (824, 554),
            'mystic2': (665, 66),
        },
        'action': [

            {'t': 'click', 'p': (546, 498), 'ec': True},
            {'t': 'click', 'p': (687, 343), 'ec': True, 'wait-over': True},

            {'t': 'click', 'p': (547, 419), 'ec': True},
            {'t': 'click_and_teleport', 'ec': True, 'wait-over': True, 'p': (801, 275)},

            {'t': 'exchange_and_click', 'p': (460, 498), 'ec': True},
            {'t': 'choose_and_change', 'p': (528, 457)},
            {'t': 'click', 'p': (408, 468), 'wait-over': True},

            {'t': 'exchange_and_click', 'p': (897, 416), 'wait-over': True},
            {'t': 'click', 'p': (435, 446)},
        ]
    },
    '15-5': {
        'start': {
            'mystic1': (314, 300),
            'mystic2': (490, 526),
        },
        'action': [

            {'t': 'exchange_and_click', 'p': (608, 384), 'ec': True},

            {'t': 'choose_and_change', 'p': (610, 388)},
            {'t': 'click', 'p': (730, 388), 'wait-over': True},

            {'t': 'click', 'p': (784, 218), 'ec': True},
            {'t': 'click_and_teleport', 'ec': True, 'wait-over': True, 'p': (579, 234)},

            {'t': 'click_and_teleport', 'ec': True, 'wait-over': True, 'p': (788, 216)},
            {'t': 'click', 'p': (651, 373), 'wait-over': True},

            {'t': 'click', 'p': (803, 491), 'ec': True},
            {'t': 'click', 'p': (734, 354), 'wait-over': True},
            {'t': 'click', 'p': (779, 511)},
        ]
    },
}
