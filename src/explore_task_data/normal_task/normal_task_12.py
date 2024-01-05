stage_data = {
    '12': {
        'SUB': "burst1"
    },
    '12-1': {
        'start': {
            '1': (370, 428),
            '2': (566, 328)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (640, 560), "desc": "1 lower right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (704, 320), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (71, 561), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (778, 373), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (778, 373), "desc": "choose 2"},
            {'t': 'click', 'p': (679, 369), "desc": "change 1 2"},
            {'t': 'click', 'p': (901, 374), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (71, 561), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (547, 556), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (772, 384), "desc": "1 lower right"},
        ]
    },
    '12-2': {
        'start': {
            '1': (733, 387),
            '2': (574, 474)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (581, 309), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (581, 309), "desc": "choose 1"},
            {'t': 'click', 'p': (481, 303), "desc": "change 1 2"},
            {'t': 'click', 'p': (464, 306), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (526, 453), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (767, 401), "wait-over": True, "desc": "1 right"},

            {'t': 'click', 'p': (845, 490), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (617, 383), "desc": "2 right"},
        ]
    },
    '12-3': {
        'start': {
            '1': (763, 558),
            '2': (586, 147)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (615, 413), 'ec': True},  # 主队↖️
            {'t': 'click', 'p': (724, 273), 'wait-over': True},  # 副队➡️

            {'t': 'exchange', 'ec': True},  # 切换部队
            {'t': 'click', 'p': (642, 271)},  # 副队原地点击
            {'t': 'move', "wait-over": True},  # 副队传送
            {'t': 'click', 'p': (614, 350), 'ec': True},  # 副队↗️
            {'t': 'click', 'p': (586, 371)},  # 主队点击副队
            {'t': 'click', 'p': (483, 355)},  # 更换部队
            {'t': 'click', 'p': (471, 360), "wait-over": True},  # 主队⬅️

            {'t': 'click', 'p': (440, 286), 'ec': True},  # 主队↖️
            {'t': 'end-turn'},  # 结束回合
        ]
    },
    '12-4': {
        'start': {
            '1': (342, 386),
            '2': (619, 223)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (622, 424), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (746, 264), "desc": "2 right"},
            {'t': 'move', 'ec': True, "wait-over": True, "desc": "teleport"},

            {'t': 'click', 'p': (657, 523), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (654, 501), "desc": "choose 1"},
            {'t': 'click', 'p': (550, 496), "desc": "change 1 2"},
            {'t': 'click', 'p': (717, 588), "ec": True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (808, 496), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (579, 397), "desc": "choose 1"},
            {'t': 'move', "desc": "teleport"},
            {'t': 'click', 'p': (700, 240), "desc": "1 right", "wait-over": True},

            {'t': 'click', 'p': (824, 291), "desc": "1 right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (740, 513), "desc": "2 right"},

        ]
    },
    '12-5': {
        'start': {
            '1': (549, 556),
            '2': (835, 478)
        },
        'attr': {
            '1': 'mystic1',
            '2': 'burst1'
        },
        'action': [
            {'t': 'click', 'p': (582, 359), "desc": "1 upper right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (781, 353), "desc": "choose 1"},
            {'t': 'click', 'p': (678, 348), "desc": "change 1 2"},
            {'t': 'click', 'p': (842, 272), "desc": "2 upper right"},
            {'t': 'click', 'p': (518, 501), 'ec': True, "wait-over": True, "desc": "close teleport notice"},

            {'t': 'click', 'p': (665, 397), "desc": "1 upper right"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (756, 317), "desc": "choose 2"},
            {'t': 'move', "desc": "teleport", 'after': 2},
            {'t': 'click', 'p': (637, 327), 'ec': True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'click', 'p': (631, 386), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (701, 248), "desc": "2 upper left"},
            {'t': 'move', 'ec': True, "desc": "teleport", },

            {'t': 'click', 'p': (377, 392), 'ec': True, "desc": "1 left left"},
            {'t': 'click', 'p': (845, 309), 'ec': True, "desc": "2 upper right", "wait-over": True},

            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (731, 299), 'ec': True, "desc": "2 upper left"},
            {'t': 'click', 'p': (385, 422), "desc": "1 left"},

        ]
    },
}
