import module.activities as activity

func_names = {
    "sakura_flowing_chaos_in_the_gala": activity.sakura_flowing_chaos_in_the_gala.explore_story,
    "reckless_nun_and_the_witch_in_the_old_library": activity.reckless_nun_and_the_witch_in_the_old_library.explore_story,
    "Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory": activity.Battle_Before_the_New_Years_Dinner_Let_Us_Play_For_The_Victory.explore_story,
    "revolutionKupalaNight": activity.revolutionKupalaNight.explore_story,
    "bunnyChaserOnTheShip": activity.bunnyChaserOnTheShip.explore_story,
    "livelyAndJoyfulWalkingTour": activity.livelyAndJoyfulWalkingTour.explore_story,
    "anUnconcealedHeart": activity.anUnconcealedHeart.explore_story,
    "iveAlive": activity.iveAlive.explore_story,
    "AbydosResortRestorationCommittee": activity.AbydosResortRestorationCommittee.explore_story,
}


def implement(self):
    if self.current_game_activity is None or self.current_game_activity not in func_names:
        self.logger.warning("Current activity is not supported")
        return True
    return func_names[self.current_game_activity](self)
