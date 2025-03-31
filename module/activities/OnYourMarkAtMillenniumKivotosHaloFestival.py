from module.activities.activity_utils import explore_activity_story, explore_activity_mission, activity_sweep, \
    explore_activity_challenge


def sweep(self):
    return activity_sweep(self)


def explore_story(self):
    explore_activity_story(self)


def explore_mission(self):
    explore_activity_mission(self)


def explore_challenge(self):
    explore_activity_challenge(self)
