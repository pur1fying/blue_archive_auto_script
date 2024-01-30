stage_data = {
    '10': {
        'SUB': "burst1"
    },
    '10-1': {
        'start': {
            'burst1': (640, 261),
            'mystic1': (403, 560),
        },
        'action': [
            {'t': 'click', 'p': (811, 398), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (586, 546), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (779, 386), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (575, 363), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (487, 284), 'ec': True, "desc": "change to 2 and upper left"},
            {'t': 'click', 'p': (904, 392), "desc": "1 right"},
        ]
    },
    '10-2': {
        'start': {
            'burst1': (704, 558),
            'mystic1': (554, 480),
        },
        'action': [
            {'t': 'click', 'p': (620, 381), 'ec': True, "desc": "1 upper left"},
            {'t': 'choose_and_change', 'p': (620, 381), "desc": "swap 1 2"},
            {'t': 'click', 'p': (688, 303), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (880, 338), 'ec': True, "desc": "change to 2 and right"},
            {'t': 'click', 'p': (527, 414), "wait-over": True, "desc": "1 upper left"},

            {'t': 'click', 'p': (455, 497), "desc": "1 left"},
        ]
    },
    '10-3': {
        'start': {
            'burst1': (821, 344),
            'mystic1': (656, 351),
        },
        'action': [
            {'t': 'click', 'p': (701, 477), 'ec': True, "desc": "1 lower left"},
            {'t': 'choose_and_change', 'p': (701, 477), "desc": "swap 1 2"},
            {'t': 'click', 'p': (764, 556), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (713, 522), 'ec': True, "desc": "change to 2 and lower left"},
            {'t': 'click', 'p': (536, 273), "wait-over": True, "desc": "1 left"},

            {'t': 'click', 'p': (535, 272), "desc": "1 left"},
        ]
    },
    '10-4': {
        'start': {
            'burst1': (374, 263),
            'mystic1': (560, 582),
        },
        'action': [

            {'t': 'exchange_and_click', 'p': (688, 418), 'ec': True, "desc": "change to 2 and upper left"},
            {'t': 'click', 'p': (701, 278), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (680, 291), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (616, 543), "ec": True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (535, 590), 'ec': True, "desc": "change to 2 and lower left"},
            {'t': 'click', 'p': (736, 270), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (694, 495), 'ec': True, "desc": "change to 2 and right"},
            {'t': 'click', 'p': (739, 359), "desc": "1 lower left"},
        ]
    },
    '10-5': {
        'start': {
            'burst1': (374, 387),
            'mystic1': (562, 473),
        },
        'action': [
            {'t': 'click', 'p': (617, 381), "ec": True, "desc": "1 right"},
            {'t': 'choose_and_change', 'p': (617, 381), "desc": "swap 1 2"},
            {'t': 'click', 'p': (680, 300), "wait-over": True, "ec": True, "desc": "2 upper right"},

            {'t': 'click', 'p': (743, 498), "ec": True, "desc": "1 right"},
            {'t': 'click', 'p': (844, 308), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (506, 570), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (827, 290), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (794, 387), 'ec': True, "desc": "change to 2 and lower right"},
            {'t': 'click', 'p': (626, 439), "desc": "1 right"},
        ]
    },
}
