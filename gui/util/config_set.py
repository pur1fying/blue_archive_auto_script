import json


class ConfigSet:
    def __init__(self):
        with open('./config/config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        with open('./config/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
