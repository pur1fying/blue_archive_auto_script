import module.activities as activity

func_names = {
    "no_227_kinosaki_spa": activity.no_227_kinosaki_spa.implement,
    "no_68_spring_wild_dream": activity.no_68_spring_wild_dream.implement,
    "pleasant_Valentines_Day_in_schale": activity.pleasant_Valentines_Day_in_schale.implement,
    "sakura_flowing_chaos_in_the_gala": activity.sakura_flowing_chaos_in_the_gala.implement,
}


def implement(self):
    current_game_activity = self.static_config['current_game_activity'][self.server]
    if current_game_activity is None or current_game_activity not in func_names:
        self.logger.warning("Current activity is not supported")
        return True
    return func_names[current_game_activity](self)
