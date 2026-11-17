import ast
TASK_LABELS = {
    "group": "Club rewards", "momo_talk": "MomoTalk", "common_shop": "Common shop",
    "cafe_reward": "Cafe", "no1_cafe_invite": "Cafe 1 invitation", "no2_cafe_invite": "Cafe 2 invitation",
    "lesson": "Lessons", "rewarded_task": "Bounties", "arena": "Tactical Challenge", "create": "Crafting",
    "explore_normal_task": "Clear normal missions", "explore_hard_task": "Clear hard missions",
    "mail": "Mailbox", "main_story": "Main story", "group_story": "Group stories", "mini_story": "Mini stories",
    "scrimmage": "Scrimmage", "collect_reward": "Daily AP rewards (collect_reward)",
    "normal_task": "Sweep normal missions", "hard_task": "Sweep hard missions",
    "clear_special_task_power": "Commissions", "de_clothes": "CN resource configuration switch",
    "tactical_challenge_shop": "Tactical Challenge shop", "collect_daily_power": "Daily AP rewards",
    "total_assault": "Total Assault", "restart": "Check and restart the game",
    "refresh_uiautomator2": "Refresh uiautomator2", "activity_sweep": "Sweep event missions",
    "explore_activity_story": "Event stories", "explore_activity_challenge": "Event challenges",
    "explore_activity_mission": "Clear event missions", "dailyGameActivity": "Daily minigame",
    "friend": "Friend requests", "joint_firing_drill": "Joint Firing Drill",
    "pass": "Pass rewards", "collect_daily_free_power": "Free AP rewards",
}


def catalog(root):
    """Read the actual registry without importing device/GUI engines."""
    tree = ast.parse((root / "core/Baas_thread.py").read_text(encoding="utf-8-sig"))
    registry = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "func_dict" for t in n.targets))
    return {ast.literal_eval(key): TASK_LABELS.get(ast.literal_eval(key), ast.literal_eval(key))
            for key in registry.keys}


def no_work_reason(task, messages):
    # A later "No Tickets" after completed lessons is not an unexecuted task.
    if task == "lesson" and not any("Complete one lesson." in m for m in messages):
        if any("No Lesson Tickets" in m or "INADEQUATE LESSON TICKET" in m for m in messages):
            return "Insufficient lesson tickets; no lesson completed"
    if task in {"scrimmage", "rewarded_task"}:
        prefix = "Scrimmage task status :" if task == "scrimmage" else "Rewarded Task Status :"
        finished = False
        for message in messages:
            if prefix in message:
                try:
                    statuses = ast.literal_eval(message.split(prefix, 1)[1].strip())
                    finished = finished or (isinstance(statuses, list) and any(x is True for x in statuses))
                except (ValueError, SyntaxError):
                    pass
        if not finished and any("INADEQUATE TICKET" in m or "INADEQUATE AP" in m for m in messages):
            return "Insufficient tickets or AP; no sweep completed"
    if task == "joint_firing_drill" and "No drill open." in messages:
        return "Joint Firing Drill is not open"
    if task in {"explore_activity_story", "explore_activity_mission", "explore_activity_challenge", "activity_sweep"}:
        if any("Current activity is not supported" in m for m in messages):
            return "The current event is unsupported or unavailable"
        if any(m.startswith("Function [") and "not found in module" in m for m in messages):
            return "The current event has no entry point for the selected task"
    # Unknown outcomes deliberately remain pending human review. Do not infer
    # success or inactivity from a generic warning or an ERROR-level log.
    return None


def settings_for(root, tasks, config):
    """Find referenced config fields in task modules, including legacy CamelCase keys."""
    tree = ast.parse((root / "core/Baas_thread.py").read_text(encoding="utf-8-sig"))
    registry = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "func_dict" for t in n.targets))
    paths = {}
    for key, value in zip(registry.keys, registry.values):
        parts = ast.unparse(value).split(".")
        paths[ast.literal_eval(key)] = root.joinpath(*parts[:-1]).with_suffix(".py")
    keys = set()
    for task in tasks:
        path = paths.get(task)
        if path and path.is_file():
            module = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(module):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute) and node.value.attr == "config":
                    keys.add(node.attr)
        keys.update(k for k in config if k.startswith(task + "_"))
    return {k: config[k] for k in sorted(keys) if k in config}
