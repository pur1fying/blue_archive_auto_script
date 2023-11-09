import json
import threading

import time
from typing import Optional

from core import EVENT_CONFIG_PATH, DISPLAY_CONFIG_PATH

lock = threading.Lock()


class Scheduler:
    def __init__(self, update_signal):
        super().__init__()
        self.update_signal = update_signal
        self._event_config = []
        self._display_config = {
            'running': "Empty",
            'queue': []
        }
        self._read_config()

    def _read_config(self):
        with lock:
            with open(EVENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)

    def _commit_change(self):
        """event_config只能被switch修改,调度时在内存中操作"""
        # with open(EVENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
        #     json.dump(self._event_config, f, ensure_ascii=False, indent=2)
        with open(DISPLAY_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._display_config, f, ensure_ascii=False, indent=2)

    def systole(self, task_name: str) -> None:
        for event in self._event_config:
            if event['func_name'] == task_name:
                event['enabled'] = False
        self.update_signal.emit()

    def heartbeat(self) -> Optional[str]:
        # self._read_config()
        self.update_signal.emit()
        # self._event_config = sorted(self._event_config, key=lambda x: x['next_tick'])
        _valid_event = [x for x in self._event_config if x['enabled']]
        if len(_valid_event) != 0:
            self._display_config['running'] = _valid_event[0]['event_name']
            self._display_config['queue'] = [x['event_name'] for x in _valid_event[1:]]
            self._commit_change()
            return _valid_event[0]['func_name']
        else:
            self._display_config['running'] = "Empty"
            self._display_config['queue'] = [x['event_name'] for x in _valid_event]
            self._commit_change()
            return None
