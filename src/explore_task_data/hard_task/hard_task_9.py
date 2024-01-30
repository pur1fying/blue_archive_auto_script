stage_data = {
    '9-1-sss-present-task': {
        'start': {
            'burst1': (493, 301),
            'pierce1': (573, 576),
        },
        'action': [
            {'t': 'click', 'p': (688, 278), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (689, 413), 'ec': True, 'wait-over': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (743, 352), "ec": True, "desc": "2 upper right"},
            {'t': 'choose_and_change', 'p': (743, 352), "desc": "swap 1 2"},
            {'t': 'click', 'p': (861, 356), 'wait-over': True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (404, 319), "wait-over": True, "desc": "2 left"},
            {'t': 'click', 'p': (903, 416), "desc": "1 right"},

        ]
    },
    '9-2-sss-present': {
        'start': {
            'burst1': (438, 222),
            'pierce1': (532, 641),
        },
        'action': [
            {'t': 'click', 'p': (674, 350), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (688, 420), 'wait-over': True, 'ec': True, "desc": "2 upper right"},

            {'t': 'exchange_and_click', 'p': (744, 356), 'ec': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (798, 275), 'wait-over': True, "desc": "2 right"},

            {'t': 'click', 'p': (798, 225), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (726, 459), 'wait-over': True, 'ec': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (789, 541), "wait-over": True, "desc": "2 lower right"},
            {'t': 'click', 'p': (720, 358), "desc": "1 lower right"},
        ]
    },
    '9-2-task': {
        'start': {
            'burst1': (438, 222),
        },
        'action': [
            {'t': 'click', 'p': (584, 381), 'wait-over': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (707, 381), 'wait-over': True, "desc": "1 right"},
            {'t': 'click', 'p': (844, 284), "desc": "1 right"},
        ]
    },

    '9-3-sss-present-task': {
        'start': {
            'burst1': (761, 465),
            'pierce1': (729, 283),
        },
        'action': [
            {'t': 'exchange_and_click', 'p': (579, 422), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (579, 422), "desc": "swap 1 2"},
            {'t': 'click', 'p': (460, 422), 'wait-over': True, "desc": "1 left"},

            {'t': 'click', 'p': (440, 502), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (873, 467), 'wait-over': True, "desc": "2 right"},

            {'t': 'exchange_and_click', 'p': (846, 290), 'wait-over': True, "desc": "2 upper right"},
            {'t': 'click', 'p': (378, 392), "desc": "1 left"},
        ]
    },
}
