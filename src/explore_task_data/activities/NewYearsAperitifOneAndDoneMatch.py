stage_data = {
    "mission": [
        'pierce1',
        'pierce1',
        'burst1',
        'burst1',
        'pierce1',
        'pierce1',
        'burst1',
        'burst1',
        'pierce1',
        'pierce1',
        'burst1',
        'burst1',
    ],
    "challenge2_sss": {
        "start": [
          ["burst1",    [730,     305]],
          ["pierce1",    [637,    226]]
        ],
        "action": [
          {"t": "click",    "p": [520,    441],    "ec": True,    "desc": "1 left"},
          {"t": "click",    "p": [522,    274],    "ec": True,    "wait-over": True,    "desc": "2 left"},

          {"t": "exchange_and_click",    "p": [480,    398],    "ec": True,    "desc": "2 lower left"},
          {"t": "choose_and_change",    "p": [495,    395],    "desc": "12 change"},
          {"t": "click",    "p": [374,    396],    "wait-over": True,    "desc": "1 left"},

          {"t": "click",    "p": [430,    474],    "ec": True,    "desc": "1 lower left"},
          {"t": "click",    "p": [883,    405],    "ec": True,    "wait-over": True,    "desc": "2 right"},

          {"t": "click",    "p": [550,    486],    "ec": True,    "desc": "1 lower right"},
          {"t": "click",    "p": [840,    477],    "ec": True,    "wait-over": True,    "desc": "2 lower right"},

          {"t": "exchange_and_click",    "p": [727,    460],    "ec": True,    "desc": "2 lower left"},
          {"t": "click",    "p": [555,    469],    "ec": True,    "wait-over": True,    "desc": "1 lower right"}
        ]
      },
    "challenge2_task": {
        "start": [
            ["burst1",   [730,   305]],
            ["pierce1",   [637,   226]]
        ],
        "action": [
            {"t": "click",   "p": [520,    441],   "ec": True,   "desc": "1 left"},
            {"t": "click",   "p": [522,    274],   "ec": True,   "wait-over": True,   "desc": "2 left"},

            {"t": "exchange_and_click",   "p": [480,    398],   "ec": True,   "desc": "2 lower left"},
            {"t": "choose_and_change",   "p": [495,    395],   "desc": "12 change"},
            {"t": "click",   "p": [374,    396],   "wait-over": True,   "desc": "1 left"},

            {"t": "click",   "p": [430,    474],   "ec": True,   "desc": "1 lower left"},
            {"t": "end-turn",   "p": []},

            {"t": "click",   "p": [550,    486],   "ec": True,   "desc": "1 lower left"},
            {"t": "end-turn",   "p": []},

            {"t": "click",   "p": [652,    473], "desc": "1 lower right"}
        ]
    },

    "challenge4_sss": {
        "start": [
            ["burst1",  [520,  428]],
            ["burst2",  [710,  176]],
            ["pierce1",  [984,  702]]
        ],
        "action": [
            {"t": "click_and_teleport",  "p": [440,  440],  "ec": True,  "wait-over": True,  "desc": "1 lower left teleport"},
            {"t": "choose_and_change",  "p": [718,  358],  "desc": "12 change"},
            {"t": "click",  "p": [837,  360],  "ec": True,  "desc": "2 right"},
            {"t": "click",  "p": [607,  492],  "ec": True,  "wait-over": True,  "desc": "3 left"},

            {"t": "exchange",  "p": [],  "desc": "exchange"},
            {"t": "click_and_teleport",  "p": [695,  412],  "desc": "2 teleport"},
            {"t": "click",  "p": [710,  459],  "ec": True,  "desc": "2 right"},
            {"t": "exchange_twice",  "p": [],  "desc": "exchange twice"},
            {"t": "choose_and_change",  "p": [637,  411],  "desc": "23 change"},
            {"t": "click",  "p": [701,  338],  "ec": True,  "desc": "3 upper right"},
            {"t": "click",  "p": [485,  280],  "ec": True,  "wait-over": True,  "desc": "1 left"},

            {"t": "exchange",  "p": [],  "desc": "exchange"},
            {"t": "click_and_teleport",  "p": [792,  400],  "ec": True,  "wait-over": True,  "desc": "2 upper right teleport"},
            {"t": "choose_and_change",  "p": [527,  267],  "desc": "12 change"},
            {"t": "click",  "p": [490,  380],  "ec": True,  "desc": "1 lower left"},
            {"t": "click",  "p": [827,  366],  "ec": True,  "wait-over": True,  "desc": "3 upper right"},

            {"t": "click",  "p": [502,  517],  "ec": True,  "desc": "1 lower left"},
            {"t": "exchange_and_click",  "p": [708,  260],  "ec": True,  "desc": "3 upper left"},
            {"t": "choose_and_change",  "p": [683,  276],  "desc": "23 change"},
            {"t": "click",  "p": [750,  202],  "ec": True,  "wait-over": True,  "desc": "2 upper right"},

            {"t": "exchange_twice_and_click",  "p": [553,  549],  "ec": True,  "desc": "3 lower left"},
            {"t": "exchange",  "p": [],  "desc": "exchange"},
            {"t": "click_and_teleport",  "p": [732,  300],  "wait-over": True,  "desc": "2 teleport"},
            {"t": "click",  "p": [511,  367],  "ec": True,  "desc": "2 upper left"},
            {"t": "click",  "p": [521,  274],  "desc": "1 left"}
        ]
    },

    "challenge4_task": {
        "start": [
            ["burst1", [698, 186]],
            ["pierce1", [983, 707]]
        ],
        "action": [
            {"t": "exchange_and_click", "p": [597, 491], "ec": True, "desc": "2 left"},
            {"t": "end-turn", "p": []},

            {"t": "exchange_and_click", "p": [631, 417], "ec": True, "desc": "2 upper left"},
            {"t": "click", "p": [475, 284], "wait-over": True, "desc": "1 left"},

            {"t": "click",  "p": [407, 321], "ec": True, "desc": "1 left"},
            {"t": "click", "p": [772, 420], "ec": True, "wait-over": True, "desc": "2 upper right"},

            {"t": "click", "p": [577, 406], "ec": True, "desc": "1 lower left"},
            {"t": "end-turn", "p": []},

            {"t": "click", "p": [441, 434], "ec": True, "desc": "1 lower left"},
            {"t": "end-turn", "p": []},

            {"t": "click", "p": [380, 378], "desc": "1 left"}
        ]
    }
}
