stage_data = {
    "Operation-Recapture-Schale-2": {
        "will-fight": False,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (571, 370), 'wait-over': True, 'desc': "upper right"},
            {'t': 'click', 'p': (687, 373), 'wait-over': True, 'desc': "right"},

            {'t': 'click_and_teleport', 'p': (808, 374), 'wait-over': True, 'desc': "right and tp"},
            {'t': 'click', 'p': (781, 362), 'wait-over': True, 'desc': "right"},

            {'t': 'click', 'p': (753, 318), 'wait-over': True, 'desc': "upper right"},
            {'t': 'click', 'p': (880, 327), 'desc': "right"},
        ]
    },
    "The-Guide-of-Chroma": {
        "will-fight": True,
        "start": [
            (490, 385),
            (693, 305),
            (645, 564)
        ],
        "actions": [
            {'t': 'click', 'p': (378, 422), 'wait-over': True, 'desc': "1 left"},
            {'t': 'click', 'p': (698, 308), 'wait-over': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (701, 472), 'wait-over': True, 'desc': "3 lower right"},

            {'t': 'click', 'p': (583, 309), 'ec': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (713, 196), 'ec': True, 'desc': "2 upper right"},
            {'t': 'click', 'p': (564, 455), 'ec': True, 'desc': "3 lower right"},

            {'t': 'exchange_twice_and_click', 'p': (785, 510), 'desc': "3 right"}
        ]
    },
    "The-First-Sanctum-Abydos-Desert-District": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (576, 368), 'wait-over': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (698, 473), 'wait-over': True, 'desc': "2 lower right"},
            {'t': 'click', 'p': (758, 391), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (678, 454), 'desc': "2 right"},
        ]
    },
    "The-Second-Sanctum-Millennium-Ruins-District": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (574, 365), 'wait-over': True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (759, 388), 'wait-over': True, 'desc': "2 right"},

            {'t': 'exchange_and_click', 'p': (797, 510), 'ec': True, 'desc': "2 right"},
            {'t': 'click', 'p': (696, 364), 'wait-over': True, 'desc': "1 lower right"},

            {'t': 'click', 'p': (764, 391), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (699, 445), 'desc': "2 right"},
        ]
    },
    "The-Third-Sanctum-Abandoned-Amusement-Park": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (562, 534), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (845, 499), 'wait-over': True, 'desc': "2 lower right"},

            {'t': 'click', 'p': (555, 517), 'ec': True, 'desc': "2 lower right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (442, 516), 'ec': True, 'desc': "1 lower left"},
            {'t': 'click', 'p': (779, 376), 'desc': "2 lower right"},
        ]
    },
    "The-Forth-Sanctum-Basilica-in-the-Catacomb": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (570, 541), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (680, 302), 'wait-over': True, 'desc': "2 right"},

            {'t': 'click', 'p': (702, 476), 'ec': True, 'desc': "1 lower right"},
            {'t': 'click', 'p': (728, 281), 'desc': "2 right"},
        ]
    },
    "The-Fifth-Sanctum-Outskirts-of-the-City-of-Eridu": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (410, 483), 'wait-over': True, 'desc': "1 right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (659, 353), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (579, 449), 'desc': "2 lower right"},
        ]
    },
    "The-Final-Defense-Operation-Schale": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (641, 467), 'wait-over': True, 'desc': "1 right"},
            {'t': 'end-turn'},

            {'t': 'click', 'p': (833, 495), 'ec': True, 'desc': "1 right"},
            {'t': 'click', 'p': (666, 293), 'desc': "2 right"},
        ]
    },
    "Rush": {
        "will-fight": True,
        "start": [],
        "actions": [
            {'t': 'click', 'p': (637, 425), "ec": True, 'desc': "1 upper right"},
            {'t': 'click', 'p': (458, 341), 'wait-over': True, 'desc': "2 upper left"},
            {'t': 'click', 'p': (761, 391), 'wait-over': True, 'desc': "3 right"},

            {'t': 'exchange_and_click', 'p': (460, 246), 'ec': True, 'desc': "2 upper left"},
            {'t': 'exchange_twice_and_click', 'p': (877, 458), 'ec': True, 'desc': "3 right"},
            {'t': 'click', 'p': (615, 332), 'wait-over': True, 'desc': "1 upper right"},

            {'t': 'click', 'p': (662, 361), 'wait-over': True, 'desc': "1 upper right"},
            {'end-turn'},
        ]
    }
}
