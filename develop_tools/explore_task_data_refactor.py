import json
import os
import shutil

task_data_folders = [
    "../src/explore_task_data/hard_task",
    "../src/explore_task_data/normal_task",

]


def main():
    for folder in task_data_folders:
        if os.path.exists(folder + "_update"):
            shutil.rmtree(folder + "_update")
        os.mkdir(folder + "_update")
        for file in os.listdir(folder):
            if file.endswith(".json"):
                with open(os.path.join(folder, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for task in data:
                    if "start" not in data[task] or "action" not in data[task]:
                        print(f"Task {task} in file {file} is missing 'start' or 'action' key.")
                        continue
                    current_team = 0
                    total_team = len(data[task]["start"])
                    for action in data[task]["action"]:
                        # rename "t" to action_type
                        if "t" in action:
                            action["action_type"] = action.pop("t")

                        # rename "p" to arg_position
                        if "p" in action:
                            action["arg_position"] = action.pop("p")

                        # rename "ec" to expect_team_change
                        if "ec" in action:
                            action["arg_expect_team_change"] = action.pop("ec")

                        # rename "desc" to description
                        if "desc" in action:
                            action["arg_description"] = action.pop("desc")

                        if "wait-over" in action:
                            action["arg_wait_loading"] = action.pop("wait-over")

                        if "end-turn-wait-over" in action:
                            action["arg_end_turn_wait_loading"] = action.pop("end-turn-wait-over")

                        if "pre-wait" in action:
                            action["pre_delay"] = action.pop("pre-wait")

                        if "post-wait" in action:
                            action["post_delay"] = action.pop("post-wait")

                        # add team index
                        action["team_index"] = current_team

                        if "exchange" in action["action_type"]:
                            current_team = (current_team + 1) % total_team
                            if "twice" in action["action_type"]:
                                current_team = (current_team + 1) % total_team
                        elif "click" in action["action_type"]:
                            current_team = (current_team + 1) % total_team

            with open(os.path.join(folder + "_update", file), 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
    pass


if __name__ == "__main__":
    main()
