import module.activities as activity

func_names = {
    "sakura_flowing_chaos_in_the_gala": activity.sakura_flowing_chaos_in_the_gala.explore_challenge,
    "reckless_nun_and_the_witch_in_the_old_library": activity.reckless_nun_and_the_witch_in_the_old_library.explore_challenge,
    "Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory": activity.Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory.explore_challenge,
    "revolutionKupalaNight": activity.revolutionKupalaNight.explore_challenge,
    "bunnyChaserOnTheShip": activity.bunnyChaserOnTheShip.explore_challenge,
    "livelyAndJoyfulWalkingTour": activity.livelyAndJoyfulWalkingTour.explore_challenge,
    "anUnconcealedHeart": activity.anUnconcealedHeart.explore_challenge,
    "iveAlive": activity.iveAlive.explore_challenge,
}


def implement(self):
    if self.current_game_activity is None or self.current_game_activity not in func_names:
        self.logger.warning("Current activity is not supported")
        return True
    return func_names[self.current_game_activity](self)
