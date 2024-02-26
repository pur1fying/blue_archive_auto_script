stage_data = {
    '25-1-sss-present-task': {
        'start': {
            'shock1': (670, 470),
            'pierce1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (605, 475), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (590, 385), 'ec': True, 'wait-over': True, 'desc': "2 upper right"},

            {'t': 'click', 'p': (565, 500), 'ec': True, 'desc': "1 lower left"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (515, 410), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (508, 580), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (630, 410), 'ec': True, 'wait-over': True, 'desc': "2 upper left"},

            {'t': 'click', 'p': (395, 450), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (900, 365), 'ec': True, 'wait-over': True, 'desc': "2 left"},

            {'t': 'exchange_and_click', 'p': (725, 450), 'wait-over': True, 'desc': "2 lower left"},
            {'t': 'click', 'p': (445, 330), 'desc': "1 upper right"}
        ]
    },
    '25-2-sss-present-task': {
        'start': {
            'shock1': (670, 470),
            'pierce1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (565, 325), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (505, 410), 'ec': True, 'wait-over': True, 'desc': "2 right"},

            {'t': 'click', 'p': (455, 330), 'ec': True, 'desc': "1 upper right"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (395, 340), 'wait-over': True, 'ec': True, 'desc': "1 right"},

            {'t': 'exchange_and_click', 'p': (676, 388), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (461, 373), "wait-over": True, "desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (676, 388), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (461, 373), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (728, 468), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (555, 475), 'desc': "1 upper right"},
        ]
    },
    '25-3-sss-present-task': {
        'start': {
            'shock1': (670, 470),
            'pierce1': (370, 215),
            'shock2': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (665, 415), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (550, 315), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (640, 320), 'ec': True, 'wait-over': True, 'desc': "3 lower left"},

            {'t': 'click', 'p': (720, 280), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (565, 265), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (760, 315), 'ec': True, 'wait-over': True, 'desc': "3 lower left"},

            {'t': 'click', 'p': (665, 415), 'ec': True, 'desc': "1 left"},
            {'t': 'click', 'p': (550, 315), 'ec': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (640, 320), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'click', 'p': (665, 415), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (550, 315), 'ec': True, 'desc': "2 left"},
            {'t': 'click', 'p': (640, 320), 'ec': True, 'wait-over': True, 'desc': "3 upper left"},

            {'t': 'exchange_twice_and_click', 'p': (845, 325), 'ec': True, 'desc': "3 upper left"},
            {'t': 'exchange_and_click', 'p': (555, 475), 'desc': "2 left"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 3"},
            {'t': 'choose_and_change', 'p': (510, 345), 'desc': "swap 1 2"},
            {'t': 'click', 'p': (435, 490), 'desc': "1 upper left"},
        ]
    },
}
