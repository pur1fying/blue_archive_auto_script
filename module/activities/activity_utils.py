import json


def get_stage_data(self):
    json_path = 'src/explore_task_data/activities/' + self.current_game_activity + '.json'
    with open(json_path, 'r') as f:
        stage_data = json.load(f)
    return stage_data
