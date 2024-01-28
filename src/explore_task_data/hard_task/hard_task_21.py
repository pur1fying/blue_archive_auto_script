stage_data = {
    '21-1-sss-present-task': {
        'start': {
            'mystic1': (727, 297),
            'burst1': (337, 647),
        },
        'action': [
            {'t': 'click', 'p': (682, 384), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (658, 477), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'click', 'p': (599, 432), 'ec': True, 'desc': "1 lower left"},
            {'t': 'choose_and_change', 'p': (623, 407), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (676, 322), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (614, 577), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (574, 280), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (530, 201), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (709, 450), 'wait-over': True, 'desc': "1 right"},

            {'t': 'click', 'p': (770, 407), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (452, 285), 'desc': "2 left"},
        ]
    },
    '21-2-sss-present-task': {
        'start': {
            'mystic1': (374, 305),
            'burst1': (563, 609),
        },
        'action': [
            {'t': 'click', 'p': (683, 288), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (691, 423), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'exchange_and_click', 'p': (721, 357), 'ec': True, 'desc': "2 upper right"},
            {'t': 'choose_and_change', 'p': (721, 357), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (839, 351), 'wait-over': True, 'desc': "1 right"},

            {'t': 'click', 'p': (838, 283), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (580, 235), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (721, 273), 'ec': True, 'desc': "1 upper left"},
            {'t': 'choose_and_change', 'p': (712, 285), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (770, 206), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (439, 332), 'ec': True, 'desc': "1 upper left"},
            {'t': 'click', 'p': (802, 258), 'desc': "2 upper right"},
        ]
    },
    '21-3-sss-present-task': {
        'start': {
            'mystic1': (314, 300),
            'burst1': (739, 692),
            'mystic2': (1085, 246),
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (616, 423), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (614, 378), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (727, 302), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'exchange_and_click', 'p': (569, 425), 'ec': True, 'desc': "2 upper left"},
            {'t': 'choose_and_change', 'p': (622, 491), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (679, 577), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (718, 278), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'click', 'p': (595, 386), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (581, 240), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (839, 441), 'wait-over': True, 'ec': True, 'desc': "3 lower right"},

            {'t': 'click', 'p': (640, 414), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (637, 317), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (668, 394), 'wait-over': True, 'ec': True, 'desc': "3 left"},

            {'t': 'exchange_and_click', 'p': (626, 338), 'ec': True, 'desc': "2 right"},
            {'t': 'exchange_twice_and_click', 'p': (664, 419), 'ec': True, 'desc': "3 left"},
            {'t': 'choose_and_change', 'p': (661, 411), 'desc': "swap 1 3"},
            {'t': 'choose_and_change', 'p': (605, 329), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (670, 255), 'desc': "1 upper right"},
        ]
    },
}
