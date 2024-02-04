stage_data = {
    '18': {
        'SUB': "mystic1"
    },
    '18-1': {
        'start': {
            'mystic1': (464, 261),
            'burst1': (463, 558),
        },
        'action': [
            {'t': 'click', 'p': (738, 273), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (701, 492), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (793, 278), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', 'p': (659, 419), "wait-over": True, 'ec': True, "desc": "2 upper right and tp"},

            {'t': 'exchange_and_click', 'p': (767, 415), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (705, 193), "desc": "1 upper right"},

        ]
    },
    '18-2': {
        'start': {
            'mystic1': (368, 472),
            'burst1': (639, 260),
        },
        'action': [
            {'t': 'click', 'p': (687, 498), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (568, 333), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (811, 510), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (656, 305), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (805, 561), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', 'p': (639, 204), "desc": "2 upper right and tp"},
        ]
    },
    '18-3': {
        'start': {
            'mystic1': (365, 603),
            'swipe': (300, 100, 300, 510, 0.1),
            'burst1': (549, 175),
        },
        'action': [
            {'t': 'click', 'p': (663, 416), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (692, 353), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (741, 419), 'wait-over': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (720, 357), "wait-over": True, 'ec': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (765, 412), 'ec': True, "desc": "1 upper right"},
            {'t': 'choose_and_change', 'p': (765, 412), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (702, 496), "wait-over": True, "desc": "1 lower left and tp"},

            {'t': 'exchange_and_click', 'p': (817, 556), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (594, 226), "wait-over": True, "desc": "1 upper right"},

            {'t': 'click', 'p': (677, 195), "desc": "1 upper right"},
        ]
    },
    '18-4': {
        'start': {
            'mystic1': (1146, 386),
            'burst1': (186, 562),
        },
        'action': [
            {'t': 'click', 'p': (660, 357), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (622, 428), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click_and_teleport', 'p': (719, 272), 'ec': True, "desc": "1 upper left and tp"},
            {'t': 'click', 'p': (418, 476), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (547, 273), 'ec': True, "desc": "1 left"},
            {'t': 'click_and_teleport', 'p': (450, 534), 'wait-over': True, "desc": "2 left and tp"},

            {'t': 'exchange_and_click', 'p': (378, 386), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (656, 342), "wait-over": True, "desc": "1 left"},

            {'t': 'click', 'p': (725, 292), "ec": True, "desc": "1 upper left"},
            {'t': 'end-turn'}
        ]
    },
    '18-5': {
        'start': {
            'mystic1': (400, 513),
            'burst1': (415, 284),
        },
        'action': [
            {'t': 'click', 'p': (753, 496), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (640, 320), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (756, 342), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (701, 306), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange'},
            {'t': 'choose_and_change', 'p': (758, 385), "desc": "swap 1 2"},
            {'t': 'click', 'p': (877, 392), "ec": True, "desc": "2 right"},
            {'t': 'click_and_teleport', 'p': (552, 388), "wait-over": True, "desc": "1 lower left and tp"},

            {'t': 'click', 'p': (827, 288), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (731, 511), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (800, 282), "desc": "1 right"}
        ]
    },
}
