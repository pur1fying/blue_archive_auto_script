import json

from main import Main
import time

EVENT_CONFIG_PATH = './core/event.json'
DISPLAY_CONFIG_PATH = './gui/config/running.json'


class Scheduler(Main):
    def __init__(self):
        super().__init__()
        self._read_config()

    def _read_config(self):
        with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)
        with open(DISPLAY_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self._display_config = json.load(f)

    def _save_config(self):
        with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=4)
        with open(DISPLAY_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._display_config, f, ensure_ascii=False, indent=4)

    def start_schedule(self):
        cur_time = int(time.time())
        if self._event_config['running']['name'] != 'empty':
            self._event_config['running'] = cur_time

    def heartbeat(self):
        cur_time = int(time.time())
        if self._event_config['running']['name'] != 'empty':
            if cur_time - self._event_config['running']['time'] > 60:
                # self.status_board
                pass


if __name__ == '__main__':
    print(time.time())
