import json
import threading

import time

EVENT_CONFIG_PATH = './core/event.json'
DISPLAY_CONFIG_PATH = './gui/config/display.json'

lock = threading.Lock()


class Scheduler:
    def __init__(self):
        super().__init__()
        self._event_config = []
        self._display_config = {
            'running': "Empty",
            'queue': []
        }
        self._read_config()

    def _read_config(self):
        with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            self._event_config = json.load(f)

    def _commit_change(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._event_config, f, ensure_ascii=False, indent=2)
            with open(DISPLAY_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._display_config, f, ensure_ascii=False, indent=2)

    def systole(self, task_name: str) -> None:
        cur_time = int(time.time())
        matching_events = [x for x in self._event_config if x['func_name'] == task_name]
        if matching_events:
            matching_events[0]['next_tick'] = cur_time + matching_events[0]['interval']
        self._commit_change()

    def heartbeat(self) -> str | None:
        self._read_config()
        cur_time = int(time.time())
        self._event_config = sorted(self._event_config, key=lambda x: x['next_tick'])
        _valid_event = [x for x in self._event_config
                        if x['enabled'] and (x['event_end'] == 0 or x['event_start'] <= cur_time <= x['event_end'])]
        if len(_valid_event) != 0 and cur_time > _valid_event[0]['next_tick']:
            self._display_config['running'] = _valid_event[0]['event_name']
            self._display_config['queue'] = [x['event_name'] for x in _valid_event[1:]]
            self._commit_change()
            return _valid_event[0]['func_name']
        else:
            self._display_config['running'] = "Empty"
            self._display_config['queue'] = [x['event_name'] for x in _valid_event]
            self._commit_change()
            return None
