stage_data = {
    '24': {
        'SUB': "shock1"
    },
    '24-1': {
        'start': {
            'shock1': (670, 470),
            'burst1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (468, 397), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (637, 461), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (433, 463), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (630, 443), "wait-over": True,'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (453, 525), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (596, 390), "wait-over": True, 'ec': True,"desc": "2 left"},

            {'t': 'click', 'p': (421, 480), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (776, 214),  "desc": "2 upper right"},
        ]
    },
    '24-2': {
        'start': {
            'shock1': (670, 470),
            'burst1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (752, 492), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (637, 318), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (560, 338), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (637, 330), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (775, 361), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (657, 357), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'exchange_and_click', 'p': (439, 505), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (890, 348), "desc": "1 right"},
        ]
    },
    '24-3': {
        'start': {
            'shock1': (670, 470),
            'burst1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (619, 357), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (660, 432), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (624, 336), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (702, 373), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (653, 304), 'ec': True, "desc": "2 lower left"},
            {'t': 'choose_and_change', 'p': (653, 304), "desc": "swap 1 2"},
            {'t': 'click', 'p': (718, 223),"wait-over": True, "desc": "1 upper right"},

            {'t': 'exchange_and_click', 'p': (433, 487), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (893, 357), "wait-over": True,"desc": "1 right"},

            {'t': 'exchange_and_click', 'p': (439, 321), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (839, 303), "desc": "1 upper right"},
        ]
    },
    '24-4': {
        'start': {
            'shock1': (670, 470),
            'burst1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (553, 300), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (697, 365), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            {'t': 'exchange_and_click', 'p': (660, 292), 'ec': True, "desc": "2 upper left"},
            {'t': 'choose_and_change', 'p': (660, 292), "desc": "swap 1 2"},
            {'t': 'click', 'p': (715, 223), "wait-over": True, "desc": "1 upper right"},

            {'t': 'click', 'p': (831, 293), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (450, 534), "desc": "2 lower right"},

        ]
    },
    '24-5': {
        'start': {
            'shock1': (670, 470),
            'burst1': (370, 215),
        },
        'action': [
            {'t': 'click', 'p': (566, 530), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (640, 320), "wait-over": True, 'ec': True, "desc": "2 left"},

            {'t': 'click', 'p': (662, 481), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (634, 367), "wait-over": True, 'ec': True, "desc": "2 lower left"},

            {'t': 'exchange_and_click', 'p': (694, 425), 'ec': True, "desc": "2 lower right"},
            {'t': 'choose_and_change', 'p': (694, 425), "desc": "swap 1 2"},
            {'t': 'click', 'p': (813, 425), "wait-over": True,"desc": "1 right"},

            {'t': 'click', 'p': (897, 373), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (378, 385), "wait-over": True, 'ec': True,"desc": "2 left"},

            {'t': 'click', 'p': (847, 472), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (560, 301),  "desc": "2 upper left"},
        ]
    },
}
