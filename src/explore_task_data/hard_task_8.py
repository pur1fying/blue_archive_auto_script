stage_data = {
    '8-1-sss-present': {
        'start': {
            '1': (613, 180),
            '2': (563, 684)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (712, 351), "desc": "1 lower right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (649, 410), 'desc': "2 upper left"},
            {'t': 'move', 'ec': True, 'wait-over': True, "desc": "teleport"},
            {'t': 'click', 'p': (613, 389), "ec": True, "desc": "1 right"},
            {'t': 'click', 'p': (850, 474), "ec": True, 'wait-over': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (556, 495), "ec": True, "desc": "1 lower right"},
            {'t': 'click', 'p': (896, 423), "wait-over": True, "desc": "2 right"},
            {'t': 'click', 'p': (614, 399), "desc": "1 right"},
            {'t': 'end-turn', 'desc': 'round-over', "wait-over": True},
            {'t': 'click', 'p': (614, 390), "desc": "1 right"},
        ]
    },
    '8-1-task': {
        'start': {
            '1': (613, 180),
            '2': (563, 684)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (712, 351), "desc": "1 lower right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (649, 410), 'desc': "2 upper left"},
            {'t': 'move', 'ec': True, 'wait-over': True, "desc": "teleport"},
            {'t': 'click', 'p': (613, 389), "ec": True, "desc": "1 right"},
            {'t': 'click', 'p': (850, 474), "ec": True, 'wait-over': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (556, 495), "ec": True, "desc": "1 lower right"},
            {'t': 'click', 'p': (722, 339), "desc": "2 upper left"},
            {'t': 'move', 'ec': True, 'wait-over': True, "desc": "teleport"},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (626, 345), "ec": True, "desc": "2 upper right"},
            {'t': 'click', 'p': (626, 345), "desc": "choose 2"},
            {'t': 'click', 'p': (520, 339), "desc": "change 1 2"},
            {'t': 'click', 'p': (743, 347), "desc": "1 right"},
        ]
    },
    '8-2-sss-present': {
        'start': {
            '1': (1000, 342),
            '2': (71, 373)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (728, 474), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (553, 477), 'wait-over': True, 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (664, 414), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (616, 395), 'ec': True, 'wait-over': True, "desc": "2 right"},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (560, 333), "ec": True, "desc": "2 upper right"},
            {'t': 'click', 'p': (668, 410), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (692, 553), "desc": "1 lower left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (592, 232), 'wait-over': True, 'ec': True, "desc": "2 upper right"},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (613, 236), "desc": "2 upper right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'end-turn', 'desc': 'round-over', "wait-over": True},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (433, 297), 'wait-over': True, "desc": "2 left"},
            {'t': 'click', 'p': (613, 490), "desc": "1 left"},
        ]
    },
    '8-2-task': {
        'start': {
            '1': (1000, 342),
            '2': (71, 373)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (728, 474), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (553, 477), 'wait-over': True, 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (664, 414), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (616, 395), 'ec': True, 'wait-over': True, "desc": "2 right"},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (560, 333), "ec": True, "desc": "2 upper right"},
            {'t': 'click', 'p': (668, 410), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (692, 553), "desc": "1 lower left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'end-turn', 'desc': 'round-over', "wait-over": True, 'ec': True},
            {'t': 'click', 'p': (641, 459), "desc": "1 left"},
        ]
    },
    '8-3-present': {
        'start': {
            '1': (793, 471),
            '2': (325, 359)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (557, 449), "desc": "2 lower right"},
            {'t': 'move', 'ec': True, 'desc': 'teleport'},
            {'t': 'click', 'p': (713, 336), "desc": "choose 2"},
            {'t': 'click', 'p': (616, 335), "desc": "change 1 2"},
            {'t': 'click', 'p': (779, 258), 'wait-over': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (722, 446), "desc": "1 lower left", 'after': 2},
            {'t': 'end-turn', 'desc': 'round-over', "wait-over": True, 'ec': True},
            {'t': 'click', 'p': (560, 398), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (754, 422), 'ec': True, 'wait-over': True, "desc": "2 right"},
            {'t': 'click', 'p': (445, 275), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (889, 435), 'wait-over': True, "desc": "2 right"},
            {'t': 'click', 'p': (460, 249), 'ec': True, "desc": "1 upper left"},
            {'t': 'end-turn', 'desc': 'round-over', "wait-over": True, 'ec': True},
            {'t': 'click', 'p': (394, 326), 'ec': True, "desc": "1 left"},
            {'t': 'end-turn', 'desc': 'round-over'},
        ]
    },
    '8-3-sss-task': {
        'start': {
            '1': (793, 471),
            '2': (325, 359)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'pierce2'
        },
        'action': [
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (557, 449), "desc": "2 lower right"},
            {'t': 'move', 'ec': True, 'desc': 'teleport'},
            {'t': 'click', 'p': (713, 336), "desc": "choose 2"},
            {'t': 'click', 'p': (616, 335), "desc": "change 1 2"},
            {'t': 'click', 'p': (604, 341), 'wait-over': True, "desc": "1 left"},
            {'t': 'click', 'p': (466, 249), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (823, 377), 'ec': True, 'wait-over': True, "desc": "2 upper right"},
            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (727, 318), "ec": True, "desc": "2 upper left"},
            {'t': 'click', 'p': (518, 283), 'wait-over': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (433, 300), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (724, 474), "desc": "2 lower left"},
            {'t': 'move', 'desc': 'teleport'},
        ]
    },
}
