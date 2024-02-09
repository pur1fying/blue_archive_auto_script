def preprocessing_name(simulator_type,multi_instance):
    if simulator_type == "bluestacks_nxt":
        if multi_instance is None:
            multi_instance = "BlueStacks App Player"
    elif simulator_type == "bluestacks_nxt_cn":
        if multi_instance is None:
            multi_instance = "BlueStacks"
    elif simulator_type == "mumu":
        if multi_instance is None:
            multi_instance = 1
    elif simulator_type == "yeshen":
        if multi_instance is None:
            multi_instance = 0
    elif simulator_type == "mumu_classic":
        multi_instance = None
    elif simulator_type == "xiaoyao_nat":
        if multi_instance is None:
            multi_instance = 0
    elif simulator_type == "leidian":
        if multi_instance is None:
            multi_instance = 0
    elif simulator_type == "wsa":
        if multi_instance is None:
            multi_instance = "localhost"
    return multi_instance
