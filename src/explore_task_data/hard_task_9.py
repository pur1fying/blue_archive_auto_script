stage_data = {
    '9-1-sss-box-task': {
        'start': {
            '1': (493, 301),
            '2': (573, 576)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (688, 278), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (689, 413), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (743, 352), "ec": True, "desc": "2 upper right"},
            {'t': 'click', 'p': (743, 352), "desc": "choose 2"},
            {'t': 'click', 'p': (641, 344), "desc": "change 1 2"},
            {'t': 'click', 'p': (861, 356), 'wait-over': True, "desc": "1 right"},

            {'t': 'exchange', "ec": True, "desc": "change to 2"},
            {'t': 'click', 'p': (404, 319), "wait-over": True, "desc": "2 left"},
            {'t': 'click', 'p': (903, 416), "desc": "1 right"},

        ]
    },
    '9-2-sss-present': {
        'start': {
            '1': (438, 222),
            '2': (532, 641)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'click', 'p': (674, 350), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (688, 420), 'wait-over': True, 'ec': True, "desc": "2 upper right"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (744, 356), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (798, 275), 'wait-over': True, "desc": "2 right"},

            {'t': 'click', 'p': (798, 225), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (726, 459), 'wait-over': True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (789, 541), "wait-over": True, "desc": "2 lower right"},
            {'t': 'click', 'p': (720, 358), "desc": "1 lower right"},
        ]
    },
    '9-2-task': {
        'start': {
            '1': (438, 222),
        },
        'attr': {
            '1': 'burst1',
        },
        'action': [
            {'t': 'click', 'p': (584, 381), 'wait-over': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (707, 381), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (844, 284), "desc": "1 right"},
        ]
    },

    '9-3-sss-present-task': {
        'start': {
            '1': (761, 465),
            '2': (729, 283)
        },
        'attr': {
            '1': 'burst1',
            '2': 'pierce1'
        },
        'action': [
            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (579, 422), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (579, 422), "desc": "choose 2"},
            {'t': 'click', 'p': (478, 419), "desc": "change"},
            {'t': 'click', 'p': (460, 422), 'wait-over': True, "desc": "1 left"},

            {'t': 'click', 'p': (440, 502), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (873, 467), 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange', 'ec': True},
            {'t': 'click', 'p': (846, 290), 'wait-over': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (378, 392), "desc": "1 left"},
        ]
    },
}
