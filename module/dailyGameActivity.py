import importlib


def implement(self):
    self.daily_game_activity = self.static_config["dailyGameActivity"][self.server]
    if self.daily_game_activity is None:
        self.logger.warning("Current activity is not supported")
        return True
    self.logger.info("Current daily game activity: " + self.daily_game_activity)
    module_name = "module.dailyGameActivities." + self.daily_game_activity
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        self.logger.warning("Module [ " + module_name + " ] not found")
        return True
    try:
        func = getattr(mod, "implement")
    except AttributeError:
        self.logger.warning("1. The function is not implemented, please contact the developer")
        return True
    return func(self)
