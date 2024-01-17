stage_data = {
    '7-1-sss-present': {
        'start': {
            '1': (697, 473),
            '2': (328, 460)
        },
        'attr': {
            '1': 'burst1',
            '2': 'mystic1'
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
    '7-2-sss-present': {
        'start': {
            '1': (469, 229),
            '2': (650, 296)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2'
        },
        'action': [
            {'t': 'click', 'p': (583, 474), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (760, 394), 'ec': True, 'wait-over': True, "desc": "2 right"},
            {'t': 'click_and_teleport', 'ec': True, 'p': (523, 560), "desc": "1 lower left and tp"},
            {'t': 'click', 'p': (758, 365), 'wait-over': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (737, 411), "desc": "1 upper right"},
            {'t': 'end-turn'},
        ]
    },
    '7-2-task': {
        'start': {
            '1': (469, 229),
            '2': (650, 296)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2'
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (578, 473), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (578, 473), "desc": "swap 1 2"},
            {'t': 'click_and_teleport', 'p': (520, 560), 'wait-over': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (716, 378), "desc": "1 upper right"},
            {'t': 'end-turn'},
        ]
    },
    '7-3-sss-present-task': {
        'start': {
            '1': (943, 471),
            '2': (182, 260)
        },
        'attr': {
            '1': 'burst1',
            '2': 'burst2'
        },
        'action': [
            {'t': 'click', 'p': (659, 433), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (626, 350), 'wait-over': True, 'ec': True, "desc": "2 right"},
            {'t': 'click_and_teleport', 'ec': True, 'p': (667, 384), "desc": "1 left and tp"},
            {'t': 'click_and_teleport', 'ec': True, 'wait-over': True, 'p': (596, 382), "desc": "2 lower right and tp"},
            {'t': 'exchange_and_click', 'p': (451, 494), "wait-over": True, "desc": "2 left"},
            {'t': 'click', 'p': (841, 294), "desc": "1 right"},
        ]
    },
}
