stage_data = {
    '21': {
        'SUB': "mystic1"
    },
    '21-1': {
        'start': [
            ['mystic1', (409, 386)],
            ['burst1', (920, 474)],
        ],
        'action': [
            {'t': 'click', 'p': (562, 283), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (666, 420), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (625, 471), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (644, 312), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (652, 477), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (652, 309), "wait-over": True, "desc": "1 left"},

            {'t': 'click', 'p': (778, 305), "desc": "1 left"},

        ]
    },
    '21-2': {
        'start': [
            ['mystic1', (499, 390)],
            ['burst1', (812, 299)],
        ],
        'action': [
            {'t': 'click', 'p': (626, 402), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (659, 335), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (649, 524), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (586, 419), 'ec': True, "wait-over": True, "desc": "2 lower left"},

            {'t': 'click', 'p': (557, 561), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (526, 246), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'ec': True, 'p': (536, 198), "desc": "2 upper left"},
            {'t': 'click', 'p': (605, 582), "desc": "1 lower left"},
        ]
    },
    '21-3': {
        'start': [
            ['mystic1', (616, 225)],
            ['burst1', (493, 418)],
        ],
        'action': [
            {'t': 'exchange_and_click', 'p': (632, 418), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (692, 329), "wait-over": True, "desc": "1 lower left"},

            {'t': 'click', 'p': (812, 342), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (658, 521), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (772, 373), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (866, 392), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'choose_and_change', 'p': (605, 452), "desc": "swap 1 2"},
            {'t': 'click', 'p': (488, 449), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (628, 285), "wait-over": True, "desc": "2 upper left"},

            {'t': 'click', 'p': (497, 420), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (811, 233), "desc": "2 upper right"},

        ]
    },
    '21-4': {
        'start': [
            ['mystic1', (398, 426)],
            ['burst1', (988, 413)],
        ],
        'action': [
            {'t': 'click', 'p': (617, 392), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (667, 392), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (664, 356), "wait-over": True, "desc": "2 left"},
            {'t': 'choose_and_change', 'p': (664, 348), "desc": "swap 1 2"},
            {'t': 'click', 'p': (782, 357), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (721, 441), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (601, 273), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            {'t': 'click', 'p': (767, 588), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (505, 209), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (518, 204), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (686, 456), "desc": "1 lower left"},

        ]
    },
    '21-5': {
        'start': [
            ['mystic1', (760, 303)],
            ['burst1', (335, 646)],
        ],
        'action': [
            {'t': 'click', 'p': (682, 390), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (600, 394), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (698, 405), 'ec': True, "desc": "1 lower left"},
            {'t': 'choose_and_change', 'p': (698, 405), "desc": "swap 1 2"},
            {'t': 'click', 'p': (755, 322), 'ec': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (652, 419), 'ec': True, "desc": "1 upper right"},
            {'t': 'choose_and_change', 'p': (652, 419), "desc": "swap 1 2"},
            {'t': 'click', 'p': (587, 330), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (656, 272), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (740, 434), "wait-over": True, "desc": "1 lower right"},

            {'t': 'exchange_and_click', 'p': (512, 209), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (772, 580), "desc": "1 lower right"},
        ]
    },
}
