import module.activities as activity

func_names = {
    "sakura_flowing_chaos_in_the_gala": activity.sakura_flowing_chaos_in_the_gala.explore_story,
    "reckless_nun_and_the_witch_in_the_old_library": activity.reckless_nun_and_the_witch_in_the_old_library.explore_story,
}


def implement(self):
    current_game_activity = self.static_config['current_game_activity'][self.server]
    if current_game_activity is None:
        self.logger.warning("Current activity is not supported")
        return True
    if current_game_activity not in func_names:
        self.logger.warning("Current activity is not supported")
        return True
    return func_names[self.static_config['current_game_activity'][self.server]](self)
