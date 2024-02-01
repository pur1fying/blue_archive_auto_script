stage_data = {
    '17': {
        'SUB': "pierce1"
    },
    '17-1': {
        'start': {
            'burst1': (550, 511),
            'pierce1': (344, 297),
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (631, 338), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (788, 392), "wait-over": True, "desc": "1 upper right"},

            {'t': 'click', 'p': (788, 392), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (637, 327), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (836, 351), "desc": "1 upper right"},
        ]
    },
    '17-2': {
        'start': {
            'burst1': (675, 433),
            'pierce1': (580, 475),
        },
        'action': [
            {'t': 'click', 'p': (637, 225), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (576, 356), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'click', 'p': (452, 361), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (427, 484), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (600, 279), 'ec': True, "desc": "1 upper left"},
            {'t': 'end-turn'}
        ]
    },
    '17-3': {
        'start': {
            'burst1': (279, 428),
            'pierce1': (1040, 490),
        },
        'action': [
            {'t': 'click', 'p': (555, 458), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (723, 330), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (615, 401), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (719, 273), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'click', 'p': (589, 379), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (883, 407), 'ec': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (842, 330), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (558, 288), "wait-over": True, "desc": "1 upper right"},

            {'t': 'click', 'p': (562, 291), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (723, 342), "desc": "2 upper left"},
        ]
    },
    '17-4': {
        'start': {
            'burst1': (580, 559),
            'pierce1': (374, 314),
        },
        'action': [
            {'t': 'click', 'p': (773, 401), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (627, 332), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (690, 251), "ec": True, "desc": "2 right"},
            {'t': 'choose_and_change', 'p': (631, 327), "desc": "swap 1 2"},
            {'t': 'click', 'p': (690, 251), "wait-over": True, "desc": "1 upper right"},

            {'t': 'click', 'p': (622, 192), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (738, 591), "desc": "2 lower right"},

        ]
    },
    '17-5': {
        'start': {
            'burst1': (940, 388),
            'pierce1': (604, 145),
        },
        'action': [
            {'t': 'click', 'p': (622, 472), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (469, 278), 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (556, 508), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (497, 377), 'ec': True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (565, 418), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (565, 418), "desc": "swap 1 2"},
            {'t': 'click', 'p': (449, 418), "wait-over": True, "desc": "1 left"},

            {'t': 'click', 'p': (433, 501), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (699, 547), 'ec': True, "desc": "2 lower left"},

            {'t': 'click', 'p': (669, 486), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (835, 529), "desc": "2 lower right"},
        ]
    },
}
