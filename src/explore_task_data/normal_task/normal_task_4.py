stage_data = {
    '4': {
        'SUB': 'pierce1'
    },
    '4-1': {
        'start': {
            '1': (370, 470),
        },
        'attr': {
            '1': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (632, 432), "desc": "right"},
            {'t': 'move', "wait-over": True, "desc": "teleport"},
            {'t': 'click', 'p': (831, 414), "wait-over": True, "desc": "right"},
            {'t': 'click', 'p': (842, 329), "desc": "upper right"},

        ]
    },
    '4-2': {
        'start': {
            '1': (434, 387),
        },
        'attr': {
            '1': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (565, 305), "desc": "upper right"},
            {'t': 'move', "wait-over": True, "desc": "teleport"},
            {'t': 'click', 'p': (794, 330), "wait-over": True, "desc": "upper right"},
            {'t': 'click', 'p': (838, 432), "desc": "lower right"},

        ]
    },
    '4-3': {
        'start': {
            '1': (400, 468),
        },
        'attr': {
            '1': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (581, 345), "desc": "upper right"},
            {'t': 'move', "wait-over": True, "desc": "teleport"},
            {'t': 'click', 'p': (656, 338), "desc": "choose self", 'ensure-ui': False},
            {'t': 'move', "wait-over": True, "desc": "teleport"},
            {'t': 'click', 'p': (626, 380), "desc": "lower right"},
        ]
    },
    '4-4': {
        'start': {
            '1': (460, 470),
        },
        'attr': {
            '1': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (652, 440), "wait-over": True, "desc": "right"},
            {'t': 'click', 'p': (773, 441), "desc": "right", 'after': 2},
            {'t': 'nothing'},

        ]
    },
    '4-5': {
        'start': {
            '1': (580, 511),
        },
        'attr': {
            '1': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (719, 474), "wait-over": True, 'desc': "right"},
            {'t': 'click', 'p': (634, 452), "desc": "choose self", 'ensure-ui': False},
            {'t': 'move', "wait-over": True, "desc": "teleport"},
            {'t': 'click', 'p': (524, 293), "wait-over": True, "desc": 'left'},
            {'t': 'click', 'p': (419, 305), "desc": "left"}

        ]
    }
}
