import json
import threading
import time
from datetime import datetime, timedelta, timezone

lock = threading.Lock()


class Scheduler:

    def __init__(self, update_signal, path):
        super().__init__()
        self.event_map = {}
        self.first_waiting = None
        self.event_config_path = "./config/" + path + "/event.json"
        self.update_signal = update_signal
        self._event_config = []
        self._current_task = None
        self._valid_task_queue = []
        self._currentTaskDisplay = None
        self._waitingTaskDisplayQueue = []
        self.funcs = []
        self._read_config()

    def _read_config(self):
        with lock:
            with open(self.event_config_path, 'r', encoding='utf-8') as f:
                self._event_config = json.load(f)
                if self.event_map == {}:
                    for item in self._event_config:
                        self.funcs.append(item['func_name'])
                        self.event_map[item['func_name']] = item['event_name']

    def _commit_change(self):
        """event_config只能被switch修改,调度时在内存中操作"""
        with open(self.event_config_path, 'w', encoding='utf-8') as f:
            json.dump(self._event_config, f, ensure_ascii=False, indent=2)
        # with open(self._display_config_path, 'w', encoding='utf-8') as f:
        #     json.dump(self._display_config, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_next_time(cls, hour, minute, second):
        t = datetime.now(timezone.utc)
        deltaDay = 0
        if t.hour > hour or (t.hour == hour and t.minute > minute) or (t.hour == hour and t.minute == minute and t.second > second):
            deltaDay = 1
        td = timedelta(days=deltaDay)
        return (t.replace(hour=hour, minute=minute, second=second, microsecond=0) + td).timestamp()

    def systole(self, task_name: str, next_time=0):
        if task_name == self._current_task['current_task']:
            for event in self._event_config:
                if event['func_name'] == task_name:
                    if next_time > 0:
                        event['next_tick'] = time.time() + next_time
                    else:
                        interval = event['interval']
                        if event['interval'] <= 0:
                            interval = 86400
                        daily_reset = event['daily_reset']                          # daily_reset is a list with items like : [hour, minute, second]
                        sorted(daily_reset, key=lambda x: x[0] * 3600 + x[1] * 60 + x[2])
                        current = datetime.now(timezone.utc).timestamp()
                        temp = None
                        for i in range(0, len(daily_reset)):
                            temp = self.get_next_time(daily_reset[i][0], daily_reset[i][1], daily_reset[i][2])
                            if current + interval >= temp:
                                event['next_tick'] = temp
                                break
                        else:
                            if event['interval'] > 0:
                                event['next_tick'] = time.time() + event['interval']
                            else:
                                event['next_tick'] = time.time() + 86400
                    event['next_tick'] = int(event['next_tick'])
                    self._commit_change()
                    return datetime.fromtimestamp(event['next_tick'])

    def heartbeat(self):
        self.update_valid_task_queue()
        if len(self._valid_task_queue) != 0:
            self.first_waiting = True
            self._current_task = self._valid_task_queue[0]
            self._currentTaskDisplay = self.event_map[self._current_task['current_task']]
            self._valid_task_queue.pop(0)
            self.update_signal.emit([self._currentTaskDisplay, *self._waitingTaskDisplayQueue])
            return self._current_task
        else:
            if self.first_waiting:
                self.first_waiting = False
                self.update_signal.emit(["暂无任务"])
            return None

    def update_valid_task_queue(self):
        self._read_config()
        _valid_event = [x for x in self._event_config if x['enabled']]                                      # filter out disabled event
        _valid_event = [x for x in self._event_config if x['enabled'] and x['next_tick'] <= time.time()]    # filter out event not ready
        _valid_event = sorted(_valid_event, key=lambda x: x['priority'])                                    # sort by priority
        current_time = datetime.now(timezone.utc).timestamp() % 86400
        self._valid_task_queue = []
        for i in range(0, len(_valid_event)):
            f = True
            for j in range(0, len(_valid_event[i]["disabled_time_range"])):  # current task not in disable time range
                start = _valid_event[i]["disabled_time_range"][j][0][0] * 3600 + _valid_event[i]["disabled_time_range"][j][0][1] * 60 + _valid_event[i]["disabled_time_range"][j][0][2]
                end = _valid_event[i]["disabled_time_range"][j][1][0] * 3600 + _valid_event[i]["disabled_time_range"][j][1][1] * 60 + _valid_event[i]["disabled_time_range"][j][1][2]
                if start <= current_time <= end:
                    f = False
                    break
            if not f:
                continue
            self._waitingTaskDisplayQueue.append(_valid_event[i]['event_name'])
            thisTask = {
                "pre_task": [],
                "current_task": _valid_event[i]["func_name"],
                "post_task": [],
            }
            temp = []
            for j in range(0, len(_valid_event[i]["pre_task"])):
                if self.event_map[_valid_event[i]['pre_task'][j]] not in self.funcs:
                    continue
                temp.append(_valid_event[i]['pre_task'][j])
            thisTask["pre_task"] = temp
            temp = []
            for j in range(0, len(_valid_event[i]["post_task"])):
                if self.event_map[_valid_event[i]["post_task"][j]] not in self.funcs:
                    continue
                temp.append(_valid_event[i]["post_task"][j])
            thisTask["post_task"] = temp
            self._valid_task_queue.append(thisTask)

    def getWaitingTaskList(self):
        return self._waitingTaskDisplayQueue

    def getCurrentTaskName(self):
        return self._currentTaskDisplay

