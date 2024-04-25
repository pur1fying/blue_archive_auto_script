import module.activities as activity

func_names = {
    "sakura_flowing_chaos_in_the_gala": activity.sakura_flowing_chaos_in_the_gala.explore_mission,
    "reckless_nun_and_the_witch_in_the_old_library": activity.reckless_nun_and_the_witch_in_the_old_library.explore_mission,
    "Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory": activity.Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory.explore_mission,
    "revolutionKupalaNight": activity.revolutionKupalaNight.explore_mission,
    "bunnyChaserOnTheShip": activity.bunnyChaserOnTheShip.explore_mission,
    "livelyAndJoyfulWalkingTour": activity.livelyAndJoyfulWalkingTour.explore_mission,
    "anUnconcealedHeart": activity.anUnconcealedHeart.explore_mission,
    "iveAlive": activity.iveAlive.explore_mission,
}


def implement(self):
    current_game_activity = self.static_config['current_game_activity'][self.server]
    if current_game_activity is None or current_game_activity not in func_names:
        self.logger.warning("Current activity is not supported")
        return True
    return func_names[self.static_config['current_game_activity'][self.server]](self)
