import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
lock = threading.Lock()


class Scheduler:
    def __init__(self, update_signal, path):
        super().__init__()
        self.event_config_path = "./config/" + path + "/event.json"
        self.update_signal = update_signal
        self._event_config = []
        self._display_config = {
            'running': "Empty",
            'queue': []
        }
        self._read_config()
        self._display_config_path = "./config/" + path + "/display.json"

    def _read_config(self):
        with lock:
            with open(self.event_config_path, 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)

    def _commit_change(self):
        """event_config只能被switch修改,调度时在内存中操作"""
        with open(self.event_config_path, 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)
        with open(self._display_config_path, 'w', encoding='utf-8') as f:
            json.dump(self._display_config, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_next_hour(cls, hour):
        t = datetime.now(timezone.utc)
        td = timedelta(int(t.hour >= hour))
        return (t.replace(hour=hour, minute=0, second=0, microsecond=0) + td).timestamp()

    def systole(self, task_name: str, next_time=0, server=None):
        res = None
        daily_reset = 20 - int(server == "Global" or server == "JP")
        for event in self._event_config:
            if event['func_name'] == task_name:
                if next_time != 0:
                    event['next_tick'] = time.time() + next_time
                else:
                    if event['interval'] == 0:
                        hour = {
                            "arena": 6 - int(server == "Global" or server == "JP"),
                            "collect_daily_power": 10 - int(server == "Global" or server == "JP"),
                        }.get(task_name, daily_reset)
                        if hour < datetime.now(timezone.utc).hour < daily_reset:
                            hour = daily_reset
                        event['next_tick'] = self.get_next_hour(hour)
                    else:
                        event['next_tick'] = time.time() + event['interval']
                res = datetime.fromtimestamp(event['next_tick'])
                break
        self._commit_change()
        self.update_signal.emit()
        return res

    def heartbeat(self) -> Optional[str]:
        # self._read_config()
        self._read_config()
        self.update_signal.emit()
        # self._event_config = sorted(self._event_config, key=lambda x: x['next_tick'])
        _valid_event = [x for x in self._event_config if x['enabled']]
        _valid_event = [x for x in self._event_config if x['enabled'] and x['next_tick'] <= time.time()]
        _valid_event = sorted(_valid_event, key=lambda x: x['priority'])
        if len(_valid_event) != 0:
            self._display_config['running'] = _valid_event[0]['event_name']
            self.change_display(_valid_event[0]['event_name'])
            return _valid_event[0]['func_name']
        else:
            self._display_config['running'] = "Waiting"
            self.change_display('Waiting')
            return None

    def get_next_execute_time(self):
        _valid_event = [x for x in self._event_config if x['enabled']]
        _valid_event.sort(key=lambda x: x['next_tick'])
        return _valid_event[0]['next_tick'] - time.time()

    def change_display(self, task_name):
        self._display_config['running'] = task_name
        self._commit_change()
        self.update_signal.emit()
