stage_data = {
    '11': {
        'SUB': "pierce1"
    },
    '11-1': {
        'start': {
            '1': (496, 525),
            '2': (794, 130)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (499, 412), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (775, 368), "desc": "2 lower right"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'click', 'p': (556, 317), 'ec': True, "desc": "1 upper right"},
            {'t': 'click', 'p': (684, 388), 'after': 5, "wait-over": True, "desc": "2 upper left"},

            {'t': 'click', 'p': (469, 245), "desc": "1 upper left"},
        ]
    },
    '11-2': {
        'start': {
            '1': (281, 347),
            '2': (791, 287)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (553, 478), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (823, 406), "desc": "2 lower right"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'click', 'p': (616, 371), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (904, 412), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (553, 469), 'ec': True, "desc": "1 lower right"},
            {'t': 'click', 'p': (662, 419), "desc": "2 left"},
            {'t': 'move', "wait-over": True, 'ec': True, "desc": "teleport"},

            {'t': 'click', 'p': (71, 559), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (715, 270), 'ec': True, "desc": "2 right"},
            {'t': 'click', 'p': (624, 451), "desc": "1 right"},
        ]
    },
    '11-3': {
        'start': {
            '1': (315, 466),
            '2': (919, 178)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (635, 461), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (693, 397), "desc": "2 lower left"},
            {'t': 'move', 'ec': True, "wait-over": True, "desc": "teleport"},

            {'t': 'click', 'p': (613, 422), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (672, 365), "ec": True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (74, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (716, 427), 'ec': True, "desc": "2 lower left"},
            {'t': 'click', 'p': (555, 511), "desc": "1 lower right"},
        ]
    },
    '11-4': {
        'start': {
            '1': (940, 350),
            '2': (841, 285)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [

            {'t': 'click', 'p': (647, 323), 'ec': True, "desc": "1 upper left"},
            {'t': 'click', 'p': (648, 318), "desc": "choose 1"},
            {'t': 'click', 'p': (543, 318), "desc": "change 1 2"},
            {'t': 'click', 'p': (530, 321), "desc": "2 left"},
            {'t': 'move', 'ec': True, "wait-over": True, "desc": "teleport"},

            {'t': 'click', 'p': (642, 330), 'ec': True, "desc": "1 left"},
            {'t': 'click', 'p': (558, 446), "ec": True, "wait-over": True, "desc": "2 lower right"},

            {'t': 'click', 'p': (634, 318), "desc": "1 left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (434, 422), 'ec': True, "wait-over": True, "desc": "2 left"},

            {'t': 'click', 'p': (494, 404), "desc": "choose 2"},
            {'t': 'click', 'p': (393, 403), "desc": "change 1 2"},
            {'t': 'click', 'p': (433, 489), 'ec': True, "desc": "1 lower left"},
            {'t': 'click', 'p': (525, 249), "desc": "2 left"},

        ]
    },
    '11-5': {
        'start': {
            '1': (374, 429),
            '2': (1114, 591)
        },
        'attr': {
            '1': 'pierce1',
            '2': 'mystic1'
        },
        'action': [
            {'t': 'click', 'p': (80, 558), 'ec': True, "desc": "change to 2"},
            {'t': 'click', 'p': (719, 351), "desc": "2 upper left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (613, 371), "desc": "1 right", "wait-over": True},

            {'t': 'click', 'p': (729, 377), "ec": True, "desc": "1 right"},
            {'t': 'click', 'p': (616, 216), 'ec': True, "wait-over": True, "desc": "2 upper right"},

            {'t': 'click', 'p': (868, 437), 'ec': True, "desc": "1 right"},
            {'t': 'click', 'p': (683, 290), "wait-over": True, 'ec': True, "desc": "2 right"},

            {'t': 'click', 'p': (715, 523), "desc": "1 lower left"},
            {'t': 'move', 'ec': True, "desc": "teleport"},
            {'t': 'click', 'p': (835, 288), 'ec': True, "wait-over": True, "desc": "2 right"},

            {'t': 'click', 'p': (586, 549), 'ec': True, "desc": "2 lower right"},
            {'t': 'click', 'p': (662, 306), "desc": "1 right"},

        ]
    },
}
