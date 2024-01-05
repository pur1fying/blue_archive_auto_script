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
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (672, 320), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (481, 389), "desc": "choose 2"},
            {'t': 'click', 'p': (377, 384), "desc": "change"},
            {'t': 'click', 'p': (554, 306), 'wait-over': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (499, 224), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (742, 505), 'wait-over': True, "desc": "2 right"},
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (750, 416), 'ec': True, "desc": "2 upper right"},
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
            {'t': 'click', 'p': (523, 560), "desc": "1 lower left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (758, 365), 'wait-over': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (737, 411), "desc": "1 upper right"},
            {'t': 'end-turn', 'desc': 'round-over'},
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
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (578, 473), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (578, 473), "desc": "choose 2"},
            {'t': 'click', 'p': (481, 467), "desc": "change 1 2"},
            {'t': 'click', 'p': (520, 560), "desc": "1 lower left"},
            {'t': 'move', 'desc': 'teleport', 'wait-over': True},
            {'t': 'click', 'p': (716, 378), "desc": "1 upper right"},
            {'t': 'end-turn', 'desc': 'round-over'},
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
            {'t': 'click', 'p': (667, 384), "desc": "1 left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (596, 382), "desc": "2 lower right"},
            {'t': 'move', 'ec': True, 'wait-over': True, "desc": "teleport"},
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (451, 494), "wait-over": True, "desc": "2 left"},
            {'t': 'click', 'p': (841, 294), "desc": "1 right"},
        ]
    },
}
