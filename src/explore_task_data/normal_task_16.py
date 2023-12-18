stage_data = {
    '16': {
        'SUB': "pierce1"
    },
    '16-1': {
        'start': {
            '1': (728, 303),
            '2': (882, 562)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (468, 397), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (637, 461), "wait-over": True, 'ec': True, "desc": "2 left"},
            # 第二回合
            {'t': 'click', 'p': (433, 463), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (630, 443), "wait-over": True,'ec': True, "desc": "2 left"},

            # 第三回合
            {'t': 'click', 'p': (453, 525), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (596, 390), "wait-over": True, 'ec': True,"desc": "2 left"},

            # 第四回合
            {'t': 'click', 'p': (421, 480), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (776, 214),  "desc": "2 upper right"},
        ]
    },
    '16-2': {
        'start': {
            '1': (428, 472),
            '2': (409, 269)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (752, 492), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (637, 318), 'ec': True, "wait-over": True, "desc": "2 right"},

            # 第二回合
            {'t': 'click', 'p': (560, 338), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (637, 330), 'ec': True, "wait-over": True, "desc": "2 right"},

            # 第三回合
            {'t': 'click', 'p': (775, 361), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (657, 357), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            # 第四回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (439, 505), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (890, 348), "desc": "1 right"},
        ]
    },
    '16-3': {
        'start': {
            '1': (370, 388),
            '2': (1102, 562)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (619, 357), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (660, 432), "wait-over": True, 'ec': True, "desc": "2 left"},

            # 第二回合
            {'t': 'click', 'p': (624, 336), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (702, 373), "wait-over": True, 'ec': True, "desc": "2 upper left"},

            # 第三回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (653, 304), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (653, 304), "desc": "choose 2"},
            {'t': 'click', 'p': (553, 304), "desc": "change 1 2"},
            {'t': 'click', 'p': (718, 223),"wait-over": True, "desc": "1 upper right"},

            # 第四回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (433, 487), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (893, 357), "wait-over": True, 'ec': True,"desc": "1 right"},

            # 第五回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (439, 321), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (839, 303), "desc": "1 upper right"},
        ]
    },
    '16-4': {
        'start': {
            '1': (343, 473),
            '2': (812, 510)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (553, 300), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (697, 365), 'ec': True, "wait-over": True, "desc": "2 upper left"},

            # 第二回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (660, 292), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (660, 292), "desc": "choose 2"},
            {'t': 'click', 'p': (560, 292), "desc": "change 1 2"},
            {'t': 'click', 'p': (715, 223), "wait-over": True, "desc": "1 upper right"},

            # 第三回合
            {'t': 'click', 'p': (831, 293), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (450, 534), "desc": "2 lower right"},

        ]
    },
    '16-5': {
        'start': {
            '1': (307, 403),
            '2': (854, 238)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            # 第一回合
            {'t': 'click', 'p': (566, 530), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (518, 397), "wait-over": True, 'ec': True, "desc": "2 left"},

            # 第二回合
            {'t': 'click', 'p': (662, 481), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (634, 367), "wait-over": True, 'ec': True, "desc": "2 lower left"},

            # 第三回合
            {'t': 'exchange', 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (694, 425), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (694, 425), "desc": "choose 2"},
            {'t': 'click', 'p': (593, 420), "desc": "change 1 2"},
            {'t': 'click', 'p': (813, 425), "wait-over": True,"desc": "1 right"},

            # 第四回合
            {'t': 'click', 'p': (897, 373), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (378, 385), "wait-over": True, 'ec': True,"desc": "2 left"},

            # 第五回合
            {'t': 'click', 'p': (847, 472), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (560, 301),  "desc": "2 upper left"},
        ]
    },
}
