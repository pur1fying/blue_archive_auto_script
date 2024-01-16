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

            {'t': 'click', 'p': (786, 268), 'ec': True, "desc": "1 upper right"},
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
        'start': {
            '1': (847, 219),
            '2': (695, 556)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (592, 278), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (527, 501), 'ec': True, 'wait-over': True, "desc": "2 left"},

            {'t': 'click', 'p': (622, 385), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (565, 423), 'ec': True, 'wait-over': True, "desc": "2 upper left"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (508, 345), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (508, 345), "desc": "choose 2"},
            {'t': 'click', 'p': (409, 333), "desc": "change 1 2"},
            {'t': 'click', 'wait-over': True, 'p': (397, 339), "desc": "1 left"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (836, 432), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (436, 492), "desc": "1 lower left"},
        ]
    },
    "challenge_03": {
        'attr': 'burst1'
    },
    "challenge_04": {
        'start': {
            '1': (287, 225),
            '2': (1091, 168),
            '3': (36, 673)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1',
            '3': 'pierce2'
        },
        'action': [
            {'t': 'click', 'p': (694, 369), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (712, 418), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (616, 384), 'ec': True, 'wait-over': True, "desc": "3 right"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (883, 332), "desc": "2 right"},
            {'t': 'move', 'desc': 'teleport', 'wait-over': True},
            {'t': 'exchange', 'ec': True},
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (628, 432), 'ec': True, "desc": "3 left"},
            {'t': 'click', 'p': (556, 476), "desc": "choose 3"},
            {'t': 'click', 'p': (454, 474), "desc": "change 1 3"},
            {'t': 'click', 'p': (611, 564), 'wait-over': True, "desc": "1 lower right"},

            {'t': 'click', 'p': (803, 506), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (758, 463), "desc": "choose 1"},
            {'t': 'click', 'p': (658, 459), "desc": "change 1 2"},
            {'t': 'click', 'p': (821, 546), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (487, 221), 'wait-over': True, "desc": "3 lower right"},

            {'t': 'click', 'p': (751, 466), 'desc': 'choose self', 'ensure-ui': False},
            {'t': 'move', 'desc': 'teleport', 'wait-over': True},
            {'t': 'click', 'p': (841, 398), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (697, 501), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (524, 311), 'desc': 'choose self', 'ensure-ui': False},
            {'t': 'move', 'desc': 'teleport', 'wait-over': True},
            {'t': 'click', 'p': (878, 318), 'wait-over':True, "desc": "3 right"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (671, 425),'ec':True, "desc": "2 upper right"},
            {'t': 'exchange', 'ec': True},
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (532, 306), 'desc': 'choose self', 'ensure-ui': False},
            {'t': 'move', 'desc': 'teleport', 'wait-over': True},
            {'t': 'click', 'p': (839, 468), 'ec': True, "desc": "3 lower right"},
            {'t': 'click', 'p': (722, 441), "desc": "choose 3"},
            {'t': 'click', 'p': (622, 449), "desc": "change 1 3"},
            {'t': 'click', 'p': (785, 537), "desc": "1 lower right"},

        ]
    },
    "challenge_05": {
        'attr': 'burst1'
    },
}
