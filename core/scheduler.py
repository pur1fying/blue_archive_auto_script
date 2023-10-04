import json

import time

EVENT_CONFIG_PATH = './core/event.json'
DISPLAY_CONFIG_PATH = './gui/config/running.json'


class Scheduler:
    def __init__(self):
        super().__init__()
        self._read_config()
        self._event_config = []
        self._display_config = {
            'running': "Empty",
            'queue': []
        }

    def _read_config(self):
        with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)

    def _commit_change(self):
        with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)
        with open(DISPLAY_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._display_config, f, ensure_ascii=False, indent=2)

    def log(self, msg: str):
        return self._event_config

    def finish(self) -> None:
        cur_time = int(time.time())
        self._event_config[0]['next_tick'] = cur_time + self._event_config[0]['interval']
        self._commit_change()

    def heartbeat(self) -> str | None:
        cur_time = int(time.time())
        self._event_config = sorted(self._event_config, key=lambda x: x['next_tick'])
        if cur_time > self._event_config[0]['next_tick']:
            return self._event_config[0]['func_name']

# if __name__ == '__main__':
#     Scheduler()
