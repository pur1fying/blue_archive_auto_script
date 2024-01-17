stage_data = {
    '8': {
        'SUB': 'pierce1',
    },
    '8-1': {
        'start': {
            '1': (640, 303),
            '2': (518, 390)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2',
        },
        'action': [
            {'t': 'click', 'p': (877, 392), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (431, 390), "wait-over": True, "desc": "2 left"},

            {'t': 'exchange_and_click', 'p': (436, 474), "ec": True, "desc": "2 lower left"},
            {'t': 'click', 'p': (784, 354), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (841, 443), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', 'wait-over': True, 'ec': True, 'p': (556, 320), "desc": "2 upper right and tp"},

            {'t': 'exchange_and_click', 'p': (564, 515), "ec": True, "desc": "2 lower right"},
            {'t': 'click', 'p': (723, 451), "desc": "1 lower left"},

        ]
    },
    '8-2': {
        'start': {
            '1': (730, 558),
            '2': (567, 482)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2',
        },
        'action': [
            {'t': 'click', 'p': (634, 390), 'ec': True, "desc": "1 upper left"},
            {'t': 'click_and_teleport', 'wait-over': True, 'ec': True, 'p': (513, 390), "desc": "2 upper left and tp"},

            {'t': 'click', 'p': (838, 326), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (561, 281), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (640, 319), "ec": True, "desc": "2 right"},
            {'t': 'click', 'p': (784, 372), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (466, 240), "ec": True, "desc": "2 upper left"},
            {'t': 'click', 'p': (840, 520), "desc": "1 lower right"},
        ]
    },
    '8-3': {
        'start': {
            '1': (404, 343),
            '2': (618, 364)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2',
        },
        'action': [
            {'t': 'click', 'p': (582, 474), 'ec': True, "desc": "1 lower right"},
            {'t': 'choose_and_change', 'p': (582, 474), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'wait-over': True, 'ec': True, 'p': (640, 559), "desc": "2 lower right and tp"},

            {'t': 'click', 'p': (707, 364), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (798, 229), "wait-over": True, 'ec': True, "desc": "2 upper right"},

            {'t': 'click', 'p': (647, 337), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (757, 282), "desc": "2 right"},
        ]
    },
    '8-4': {
        'start': {
            '1': (335, 561),
            '2': (650, 451)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2',
        },
        'action': [
            {'t': 'click_and_teleport', 'ec': True, 'p': (580, 308), "desc": "1 upper right and tp"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (670, 395), "desc": "2 upper right and tp"},

            {'t': 'choose_and_change', 'p': (780, 357), "desc": "swap 1 2"},
            {'t': 'click', 'p': (899, 360), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (644, 314), "desc": "2 right and tp"},

            {'t': 'click', 'p': (727, 428), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (653, 469), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (900, 395), 'ec': True, "desc": "1 right"},

        ]
    },
    '8-5': {
        'start': {
            '1': (396, 469),
            '2': (577, 351)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2',
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (698, 482), "ec": True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (698, 482), "desc": "swap 1 2"},
            {'t': 'click', 'p': (816, 472), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (889, 448), 'ec': True, "desc": "1 right"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True, 'p': (439, 495), "desc": "2 lower left and tp"},

            {'t': 'exchange_and_click', 'p': (731, 276), 'ec': True, "desc": "2 left"},
            {'t': 'click', 'p': (743, 428), 'wait-over': True, "desc": "1 right"},

            {'t': 'click', 'p': (810, 515), 'ec': True, "desc": "1 lower right"},
            {'t': 'click_and_teleport', "wait-over": True, 'ec': True,'p': (710, 281), "desc": "2 right and tp"},

            {'t': 'exchange_and_click', 'p': (556, 305), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (711, 542), "desc": "1 lower left"},
        ]
    },
}
