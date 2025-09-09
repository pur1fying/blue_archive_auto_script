import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from lxml import etree

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 "
                  "Mobile Safari/537.36",
    "Content-Type": "text/html",
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'game-alias': 'ba'
}


def update_activity_gamekee_api():
    activities = {}
    api_url = "https://www.gamekee.com/v1/activity/query"
    Params = {
        # "active_at": int(time.time())
        "active_at":1755050400
    }
    response = requests.get(
        url=api_url,
        headers=HEADERS,
        params=Params
    )
    if response.status_code != 200 or response.json()["code"] != 0:
        print(f"Failed to fetch activity data, error code: {response.status_code} | {response.json()['code']}")
        return
    activity_data = response.json()["data"]
    for activity in activity_data:
        begin_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(activity["begin_at"]))
        end_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(activity["end_at"]))
        current_time = int(time.time())
        if current_time < activity["begin_at"] or current_time > activity["end_at"]:
            # Skip events that are not active
            continue
        pub_area = activity["pub_area"]
        activity_title = activity["title"]
        if pub_area not in activities:
            activities[pub_area] = []
        activities[pub_area].append({"title": activity_title, "begin_time": str(to_epoch_time(begin_time)),
                                     "end_time": str(to_epoch_time(end_time))})
    return activities


def fetch_activity_table(html, xpath: str):
    activities = []
    event_schedules = html.xpath(xpath)
    event_trs = event_schedules[0].xpath('.//tr')
    if len(event_trs) < 1:
        raise KeyError("No event data found.")
    keys = [''.join(th.itertext()).strip() for th in event_trs[0]]
    start_date_index = keys.index('Start date') if 'Start date' in keys else -1
    end_date_index = keys.index('End date') if 'End date' in keys else -1
    period_index = keys.index('Period') if 'Period' in keys else -1
    empty_index = keys.index('') if '' in keys else -1
    for event_tr in event_trs[1:]:
        values = [''.join(item.itertext()).strip() for item in event_tr]  # Remaining columns are the <th>
        if len(values) < 3:
            raise KeyError("Not enough columns in the event data.")
        if start_date_index != -1 and end_date_index != -1:
            # convert to epoch time
            start_date = to_epoch_time(values[start_date_index])
            end_date = to_epoch_time(values[end_date_index])
            values[start_date_index] = str(start_date)
            values[end_date_index] = str(end_date)
            current_time = int(time.time())
            if current_time < start_date or current_time > end_date:
                # Skip events that are not active
                continue
        if period_index != -1:
            dates = values[period_index].split(' ~ ')
            start_date = to_epoch_time(dates[0])
            end_date = to_epoch_time(dates[1])
            current_time = int(time.time())
            if current_time < start_date or current_time > end_date:
                # Skip events that are not active
                continue
        if empty_index != -1:
            keys.pop(empty_index)
            values.pop(empty_index)
        activities.append(dict(zip(keys, values)))

    # Sort activities by end date
    activities.sort(key=lambda x: x[keys[2]], reverse=True)
    return activities


def to_epoch_time(s: str) -> int:
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        dt = datetime.strptime(s + ' 10:00', '%Y-%m-%d %H:%M')
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        return int(dt.timestamp())

    if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}', s):
        dt = datetime.strptime(s, '%m/%d/%Y %H:%M')
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        return int(dt.timestamp())

    if re.fullmatch(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', s):
        dt = datetime.strptime(s, '%Y-%m-%d %H:%M')
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        return int(dt.timestamp())

    raise ValueError(f"Unrecognized time format: {s}")


def update_activity_bawiki():
    events_url = "https://bluearchive.wiki/wiki/Events"
    total_assault_url = "https://bluearchive.wiki/wiki/Total_Assault"
    grand_assault_url = "https://bluearchive.wiki/wiki/Grand_Assault"
    limit_break_assault_url = "https://bluearchive.wiki/wiki/Limit_Break_Assault"
    joint_firing_drill_url = "https://bluearchive.wiki/wiki/Joint_Firing_Drill"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 "
                      "Mobile Safari/537.36",
        "Content-Type": "text/html",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    events_response = requests.get(
        url=events_url,
        headers=HEADERS,
    )
    events_html = etree.HTML(events_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_event_schedules = fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version"]/table')
    Global_event_schedules = fetch_activity_table(events_html, '//*[@id="tabber-Global_version"]/table')
    JP_mini_events = fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version_2"]/table')
    Global_mini_events = fetch_activity_table(events_html, '//*[@id="tabber-Global_version_2"]/table')
    reward_campaigns = fetch_activity_table(events_html, '//h1[@id="Reward_campaigns"]/following::table[1]')

    total_assault_response = requests.get(
        url=total_assault_url,
        headers=HEADERS,
    )
    total_assault_html = etree.HTML(total_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_total_assault = fetch_activity_table(total_assault_html, '//*[@id="tabber-JP"]/table')
    Global_total_assault = fetch_activity_table(total_assault_html, '//*[@id="tabber-Global"]/table')

    grand_assault_response = requests.get(
        url=grand_assault_url,
        headers=HEADERS,
    )
    grand_assault_html = etree.HTML(grand_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_grand_assault = fetch_activity_table(grand_assault_html, '//*[@id="tabber-JP"]/table')
    Global_grand_assault = fetch_activity_table(grand_assault_html, '//*[@id="tabber-Global"]/table')

    limit_break_assault_response = requests.get(
        url=limit_break_assault_url,
        headers=HEADERS,
    )
    limit_break_assault_html = etree.HTML(limit_break_assault_response.content.decode('utf-8'),
                                          parser=etree.HTMLParser(encoding='utf-8'))
    JP_limit_break_assault = fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-JP"]/table')
    Global_limit_break_assault = fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-Global"]/table')

    joint_firing_drill_response = requests.get(
        url=joint_firing_drill_url,
        headers=HEADERS,
    )
    joint_firing_drill_html = etree.HTML(joint_firing_drill_response.content.decode('utf-8'),
                                         parser=etree.HTMLParser(encoding='utf-8'))
    JP_joint_firing_drill = fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Japanese_version"]/table')
    Global_joint_firing_drill = fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Global_version"]/table')

    activities = {
        "JP": {
            "event_schedules": JP_event_schedules,
            "mini_events": JP_mini_events,
            "reward_campaigns": reward_campaigns,
            "joint_firing_drill": JP_joint_firing_drill,
            "total_assault": JP_total_assault,
            "grand_assault": JP_grand_assault,
            "limit_break_assault": JP_limit_break_assault
        },
        "Global": {
            "event_schedules": Global_event_schedules,
            "mini_events": Global_mini_events,
            "reward_campaigns": reward_campaigns,
            "joint_firing_drill": Global_joint_firing_drill,
            "total_assault": Global_total_assault,
            "grand_assault": Global_grand_assault,
            "limit_break_assault": Global_limit_break_assault
        }
    }
    return activities


def download_json(url):
    response = requests.get(
        url=url,
        headers=HEADERS,
    )
    if response.status_code != 200:
        print(f"Failed to fetch data from {url}, error code: {response.status_code}")
        return None
    return response.json()


def check_event_active(server: str, event_info_dict: dict) -> bool:
    if f"EventOpen{server}" in event_info_dict:
        event_start = event_info_dict[f"EventOpen{server}"]
        event_end = event_info_dict[f"EventClose{server}"]
        return event_start <= time.time() <= event_end
    else:
        return False


def update_activity_schaledb():
    events_json = download_json("https://schaledb.com/data/zh/events.min.json")
    raids_json = download_json("https://schaledb.com/data/zh/raids.min.json")
    localization_json = download_json("https://schaledb.com/data/zh/localization.min.json")
    config_json = download_json("https://schaledb.com/data/config.min.json")

    # get event name from localization
    event_localization_dict = localization_json["EventName"]

    # total assault
    raid_names_dict = {}
    for raid in raids_json["Raid"]:
        raid_id = raid["Id"]
        raid_name = raid["Name"]
        raid_names_dict[raid_id] = raid_name

    # limit time assault
    limit_time_assault_dict = {}
    for limit_time_assault in raids_json["MultiFloorRaid"]:
        id = limit_time_assault["Id"]
        name = limit_time_assault["Name"]
        limit_time_assault_dict[id] = name

    # joint firing drill
    joint_firing_drill_dict = {}
    for joint_firing_drill in raids_json["TimeAttack"]:
        id = joint_firing_drill["Id"]
        joint_firing_drill_type = joint_firing_drill["DungeonType"]
        name = localization_json["TimeAttackStage"][joint_firing_drill_type]
        joint_firing_drill_dict[id] = name

    activities = {
    }
    for server_config in config_json["Regions"]:
        server = server_config["Name"]
        current_events = []
        for event in server_config["CurrentEvents"]:
            id = str(event["event"])
            if len(id) > 3:
                id = id[-3:]
            start = event["start"]
            end = event["end"]
            if start <= time.time() <= end:
                name = event_localization_dict[id]
                current_events.append({
                    "name": name,
                    "begin_time": str(start),
                    "end_time": str(end)
                })
        current_joint_firing_drill = []
        current_total_assault = []
        current_grand_assault = []
        current_limit_break_assault = []
        for raid in server_config["CurrentRaid"]:
            raid_type = raid["type"]
            id = raid["raid"]
            start_time = raid["start"]
            end_time = raid["end"]
            current_time =  time.time()
            if current_time < start_time or current_time > end_time:
                continue
            if raid_type == "Raid":
                current_total_assault.append({
                    "name": raid_names_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                })
            elif raid_type == "EliminateRaid":
                current_grand_assault.append({
                    "name": raid_names_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                })
            elif raid_type == "MultiFloorRaid":
                current_limit_break_assault.append({
                    "name": limit_time_assault_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                })
            elif raid_type == "TimeAttack":
                current_joint_firing_drill.append({
                    "name": joint_firing_drill_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                })
        activities[server] = {
            "event_schedules": current_events,
            "joint_firing_drill": current_joint_firing_drill,
            "total_assault": current_total_assault,
            "grand_assault": current_grand_assault,
            "limit_break_assault": current_limit_break_assault
        }
    return activities


def update_activity():
    print("Updating activity...")
    # activities = update_activity_gamekee_api()
    activities = update_activity_schaledb()
    print(json.dumps(activities, ensure_ascii=False))
    return True
