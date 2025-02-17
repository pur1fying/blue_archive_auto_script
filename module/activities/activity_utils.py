import json
import time
from core import color, picture

def get_stage_data(self):
    json_path = 'src/explore_task_data/activities/' + self.current_game_activity + '.json'
    with open(json_path, 'r') as f:
        stage_data = json.load(f)
    return stage_data


def to_activity(self, region, skip_first_screenshot=False, need_swipe=False):
    img_possibles = {
        "main_page_get-character": (640, 360),
        "activity_enter1": (1196, 195),
        "activity_enter2": (100, 149),
        "activity_enter3": (218, 530),
        'activity_fight-success-confirm': (640, 663),
        "plot_menu": (1205, 34),
        "plot_skip-plot-button": (1213, 116),
        "purchase_ap_notice": (919, 168),
        'purchase_ap_notice-localized': (919, 168),
        "plot_skip-plot-notice": (766, 520),
        "activity_get-collectable-item1": (508, 505),
        "activity_get-collectable-item2": (505, 537),
        "normal_task_help": (1017, 131),
        "activity_task-info": (1128, 141),
        "normal_task_task-info": (1126, 115),
        "activity_play-guide": (1184, 152),
        'main_story_fight-confirm': (1168, 659),
        "main_story_episode-info": (917, 161),
        'normal_task_prize-confirm': (776, 655),
        'normal_task_fail-confirm': (643, 658),
        'normal_task_task-finish': (1038, 662),
        'normal_task_fight-confirm': (1168, 659),
        "normal_task_sweep-complete": (643, 585),
        "normal_task_start-sweep-notice": (887, 164),
        'normal_task_skip-sweep-complete': (643, 506),
        'normal_task_fight-complete-confirm': (1160, 666),
        'normal_task_reward-acquired-confirm': (800, 660),
        'normal_task_mission-conclude-confirm': (1042, 671),
        "activity_exchange-confirm": (673, 603),
    }
    img_ends = "activity_menu"
    picture.co_detect(self, None, None, img_ends, img_possibles, skip_first_screenshot=skip_first_screenshot)
    if region is None:
        return True
    rgb_lo = {
        "mission": 863,
        "story": 688,
        "challenge": 1046,
    }
    click_lo = {
        "mission": 1027,
        "story": 848,
        "challenge": 1196,
    }
    while self.flag_run:
        if not color.judge_rgb_range(self, rgb_lo[region], 114, 20, 60, 40, 80, 70, 116):
            self.click(click_lo[region], 87)
            time.sleep(self.screenshot_interval)
            self.latest_img_array = self.get_screenshot_array()
        else:
            if need_swipe:
                if region == "mission":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
                elif region == "story":
                    self.swipe(919, 155, 943, 720, duration=0.05, post_sleep_time=1)
            return True
