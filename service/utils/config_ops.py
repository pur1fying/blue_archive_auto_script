import datetime
import json
import os

from core.config import default_config
from core.config.config_set import ConfigSet


def check_switch_config(dir_path='./default_config'):
    path = './config/' + dir_path + '/switch.json'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_config.SWITCH_DEFAULT_CONFIG)


def check_single_event(new_event, old_event):
    for key in new_event:
        if key not in old_event:
            old_event[key] = new_event[key]
    return old_event


def check_event_config(dir_path='./default_config', user_config=None):
    path = './config/' + dir_path + '/event.json'
    default_event_config = json.loads(default_config.EVENT_DEFAULT_CONFIG)
    server = user_config.server_mode
    enable_state = user_config.config.new_event_enable_state
    if server != "CN":
        for i in range(0, len(default_event_config)):
            for j in range(0, len(default_event_config[i]['daily_reset'])):
                default_event_config[i]['daily_reset'][j][0] = default_event_config[i]['daily_reset'][j][0] - 1
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            with open("error.log", 'w+', encoding='utf-8') as errorfile:
                errorfile.write("path not exist" + '\n' + dir_path + '\n' + datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S') + '\n')
            f.write(json.dumps(default_event_config, ensure_ascii=False, indent=2))
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:  # 检查是否有新的配置项
            data = json.load(f)
        for i in range(0, len(default_event_config)):
            exist = False
            for j in range(0, len(data)):
                if data[j]['func_name'] == default_event_config[i]['func_name']:
                    for k in range(0, len(data[i]['daily_reset'])):
                        if len(data[j]['daily_reset'][k]) != 3:
                            data[j]['daily_reset'][k] = [0, 0, 0]
                    data[j] = check_single_event(default_event_config[i], data[j])
                    exist = True
                    break
            if not exist:
                temp = default_event_config[i]
                if enable_state == "on":
                    temp['enabled'] = True
                elif enable_state == "off":
                    temp['enabled'] = False
                data.insert(i, temp)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        with open("error.log", 'w+', encoding='utf-8') as f:
            f.write(str(e) + '\n' + dir_path + '\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(default_event_config, ensure_ascii=False, indent=2))
        return


def delete_deprecated_config(file_name, config_name=None):
    # delete useless config file
    pre = 'config/'
    if config_name is not None:
        pre += config_name + '/'
    if type(file_name) is str:
        path = pre + file_name
        if os.path.exists(path):
            os.remove(path)
    elif type(file_name) is list:
        for name in file_name:
            path = pre + name
            if os.path.exists(path):
                os.remove(path)


def check_static_config():
    if not os.path.exists('./config/static.json'):
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
            return
    try:
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)
    except Exception:
        os.remove('./config/static.json')
        with open('./config/static.json', 'w', encoding='utf-8') as f:
            f.write(default_config.STATIC_DEFAULT_CONFIG)


def update_config_reserve_old(config_old, config_new):  # 保留旧配置原有的键，添加新配置中没有的，删除新配置中没有的键
    for key in config_new:
        if key not in config_old:
            config_old[key] = config_new[key]
    dels = []
    for key in config_old:
        if key not in config_new:
            dels.append(key)
    for key in dels:
        del config_old[key]
    return config_old


def check_and_update_user_config(dir_path='./default_config', server=None, name=None):
    path = './config/' + dir_path + '/config.json'
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = update_config_reserve_old(data, json.loads(default_config.DEFAULT_CONFIG))
        if name is not None:
            data['name'] = name
        if server is not None:
            data['server'] = server
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        os.remove(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(default_config.DEFAULT_CONFIG)


def check_config(dir_path, server=None, name=None):
    delete_deprecated_config("display.json", dir_path)
    if not os.path.exists('./config'):
        os.mkdir('./config')
    check_static_config()
    if type(dir_path) is not list:
        dir_path = [dir_path]
    for path in dir_path:
        if not os.path.exists('./config/' + path):
            os.mkdir('./config/' + path)
        check_and_update_user_config(path, server, name)
        config = ConfigSet(config_dir=path)
        config.update_create_quantity_entry()
        check_event_config(path, config)
        check_switch_config(path)
