stage_data = {
    '01': {
        'attr': 'burst1'
    },
    "02": {
        'attr': 'pierce1'
    },
    "03": {
        'attr': 'pierce1'
    },
    "04": {
        'start': [
            ['burst1', (789, 432)],
        ],
        'action': [
            {'t': 'click', 'p': (814, 377), "wait-over": True, 'desc': "upper right"},
            {'t': 'click', 'p': (725, 313), "wait-over": True, 'desc': "upper left"},
            {'t': 'click', 'p': (665, 376), "wait-over": True, 'desc': "left"},
            {'t': 'click', 'p': (647, 480), "wait-over": True, 'desc': "lower left"},
            {'t': 'click', 'p': (581, 564), 'desc': "lower left"},

        ]
    },
    "05": {
        'attr': 'burst1'
    },
    "06": {
        'attr': 'pierce1'
    },
    "07": {
        'attr': 'pierce1'
    },
    "08": {
        'start': [
            ['burst1', (876, 224)],
            ['pierce1', (280, 482)]
        ],
        'action': [
            {'t': 'click', 'p': (659, 333), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (626, 439), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (563, 349), 'ec': True, "desc": "change to 2 and upper right"},
            {'t': 'click', 'p': (670, 235), 'wait-over': True, "desc": "1 upper left"},

            {'t': 'exchange_and_click', 'p': (674, 441), 'ec': True, "desc": "change to 2 and right"},
            {'t': 'click', 'p': (556, 279), "desc": "1 left"},

        ]
    },
    "09": {
        'attr': 'burst1'
    },
    "10": {
        'attr': 'pierce1'
    },
    "11": {
        'attr': 'pierce1'
    },
    "12": {
        'start': [
            ['burst1', (583, 429)],
            ['pierce1', (584, 148)]
        ],
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268),'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    },
    "challenge_SUB": {
        'attr': 'burst1'
    },
    "challenge_01": {
        'attr': 'burst1'
    },
    "challenge_02": {
        'start': [
            ['burst1', (583, 429)],
            ['pierce1', (584, 148)]
        ],
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268),'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    },
    "challenge_03": {
        'attr': 'burst1'
    },
    "challenge_04": {
        'start': [
            ['burst1', (583, 429)],
            ['pierce1', (584, 148)],
            ['pierce2', (584, 148)]
        ],
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268),'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    },
    "challenge_05": {
        'attr': 'burst1'
    },
}
