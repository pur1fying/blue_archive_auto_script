import importlib


def implement(self):
    if self.current_game_activity is None:
        self.logger.warning("Current activity is not supported")
        return True
    self.logger.info("Current activity: " + self.current_game_activity)
    module_name = "module.activities." + self.current_game_activity
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        self.logger.warning("Module [ " + module_name + " ] not found")
        return True
    try:
        func = getattr(mod, "sweep")
    except AttributeError:
        self.logger.warning("Function [ implement ] not found in module , possible reason : ")
        self.logger.warning("1. Challenge Task is not open or exist in this activity")
        self.logger.warning("2. The function is not implemented, please contact the developer")
        return True
    return func(self)
