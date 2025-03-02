import json
import os


def main():
    targetDir = r"C:\Users\Nanboom233\Desktop\Code\blue_archive_auto_script\src\explore_task_data\main_story"

    for filename in os.listdir(targetDir):
        if filename.endswith('.json'):
            file_path = os.path.join(targetDir, filename)

            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for mission in data:
                    if (type(data[mission]) == dict or type(data[mission]) == list) and "start" in data[mission]:
                        for task in data[mission]["start"]:
                            if task[0].startswith("pierce"):
                                task[0] = "pierce"
                            if task[0].startswith("burst"):
                                task[0] = "burst"
                            if task[0].startswith("mystic"):
                                task[0] = "mystic"
                            if task[0].startswith("shock"):
                                task[0] = "shock"
                if "mission" in data:
                    for i in range(len(data["mission"])):
                        if data["mission"][i].startswith("pierce"):
                            data["mission"][i] = "pierce"
                        if data["mission"][i].startswith("burst"):
                            data["mission"][i] = "burst"
                        if data["mission"][i].startswith("mystic"):
                            data["mission"][i] = "mystic"
                        if data["mission"][i].startswith("shock"):
                            data["mission"][i] = "shock"
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

            print(f"Processed: {filename}")


if __name__ == '__main__':
    main()
