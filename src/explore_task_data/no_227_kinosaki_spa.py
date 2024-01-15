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
        'start': {
            '1': (789, 432),
        },
        'attr': {
            '1': 'burst1'
        },
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
        'start': {
            '1': (876, 224),
            '2': (280, 482)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (659, 333), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (626, 439), 'ec': True, 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (563, 349), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (670, 235), 'wait-over': True, "desc": "1 upper left"},

            {'t': 'exchange_and_click', 'p': (674, 441), 'ec': True, "desc": "2 right"},
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
        'start': {
            '1': (583, 429),
            '2': (584, 148)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (728, 427), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (674, 358), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (762, 441), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (645, 442), 'ec': True, 'wait-over': True, "desc": "2 lower right"},

            {'t': 'click', 'p': (786, 268),'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (407, 460), "desc": "2 left"},

        ]
    }

}
