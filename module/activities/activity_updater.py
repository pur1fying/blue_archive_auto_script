import copy
import json
import os
import re
import sys
import time
from collections import OrderedDict
from contextlib import redirect_stdout, redirect_stderr
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

BASIC_RESULT_FORMAT = {
    "Events": [],
    "Raids": {
        "total_assault": None,
        "grand_assault": None,
        "limit_break_assault": None,
        "joint_firing_drill": None,
    },
    "Rewards": {
        "commissions_rewards": 1,
        "scrimmage_rewards": 1,
        "bounty_hunts_rewards": 1,
        "schedule_rewards": 1,
        "normal_mission_rewards": 1,
        "hard_mission_rewards": 1,
        "level_exp_rewards": 1
    }
}

FULL_RESULT_FORMAT = {
    "JP": copy.deepcopy(BASIC_RESULT_FORMAT),
    "Global": copy.deepcopy(BASIC_RESULT_FORMAT),
    "CN": copy.deepcopy(BASIC_RESULT_FORMAT)
}


def _fetch_activity_table(html, xpath: str):
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
            start_date = _to_epoch_time(values[start_date_index])
            end_date = _to_epoch_time(values[end_date_index])
            values[start_date_index] = str(start_date)
            values[end_date_index] = str(end_date)
            current_time = int(time.time())
            if current_time < start_date or current_time > end_date:
                # Skip events that are not active
                continue
        if period_index != -1:
            dates = values[period_index].split(' ~ ')
            start_date = _to_epoch_time(dates[0])
            end_date = _to_epoch_time(dates[1])
            current_time = int(time.time())
            if current_time < start_date or current_time > end_date:
                # Skip events that are not active
                continue
            keys.pop(period_index)
            keys.append("Start date")
            keys.append("End date")
            values.pop(period_index)
            values.append(str(start_date))
            values.append(str(end_date))
        if empty_index != -1:
            keys.pop(empty_index)
            values.pop(empty_index)
        activities.append(dict(zip(keys, values)))

    # Sort activities by end date
    activities.sort(key=lambda x: x[keys[2]], reverse=True)
    return activities


def _table_transform(table: list, key_map: dict):
    for row in table:
        for old_key, new_key in key_map.items():
            if old_key in row:
                if new_key is None:
                    row.pop(old_key)
                else:
                    row[new_key] = row.pop(old_key)
    if len(table) == 0:
        return None
    elif len(table) == 1:
        return table[0]
    return table


def _to_epoch_time(s: str) -> int:
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


def _download_json(url):
    response = requests.get(
        url=url,
        headers=HEADERS,
    )
    if response.status_code != 200:
        print(f"Failed to fetch data from {url}, error code: {response.status_code}")
        return None
    return response.json()


def _unify_table(table_high_prio: dict, table_low_prio: dict, template_table: dict):
    result = {}
    for key in template_table.keys():
        if key in table_high_prio:
            if key in table_low_prio:
                if table_high_prio[key] is None and table_low_prio[key] is not None:
                    result[key] = table_low_prio[key]
                elif type(template_table[key]) == dict:
                    result[key] = _unify_table(table_high_prio[key], table_low_prio[key], template_table[key])
                else:
                    result[key] = table_high_prio[key]
            else:
                result[key] = table_high_prio[key]
        else:
            if key in table_low_prio:
                result[key] = table_low_prio[key]
    return result


def update_activity_gamekee_api():
    api_url = "https://www.gamekee.com/v1/activity/query"
    Params = {
        "active_at": int(time.time())
    }
    response = requests.get(
        url=api_url,
        headers=HEADERS,
        params=Params
    )
    if response.status_code != 200 or response.json()["code"] != 0:
        print(f"Failed to fetch activity data, error code: {response.status_code} | {response.json()['code']}")
        return

    pub_area_translator = {"日服": "JP", "国际服": "Global", "国服": "CN"}
    result = copy.deepcopy(FULL_RESULT_FORMAT)

    activity_data = response.json()["data"]
    for activity in activity_data:
        current_time = int(time.time())
        if current_time < activity["begin_at"] or current_time > activity["end_at"]:
            # Skip events that are not active
            continue
        pub_area = pub_area_translator[activity["pub_area"]]
        title = activity["title"]
        if title.startswith("[活动]"):
            result[pub_area]["Events"].append({
                "name": title.replace("[活动]", "").strip(),
                "begin_time": str(activity["begin_at"]),
                "end_time": str(activity["end_at"])
            })
        elif title.startswith("总力战"):
            result[pub_area]["Raids"]["total_assault"] = {
                "name": title,
                "begin_time": str(activity["begin_at"]),
                "end_time": str(activity["end_at"])
            }
        elif title.startswith("大决战"):
            result[pub_area]["Raids"]["grand_assault"] = {
                "name": title,
                "begin_time": str(activity["begin_at"]),
                "end_time": str(activity["end_at"])
            }
        elif title.startswith("制约解除决战"):
            result[pub_area]["Raids"]["limit_break_assault"] = {
                "name": title,
                "begin_time": str(activity["begin_at"]),
                "end_time": str(activity["end_at"])
            }
        elif "演习" in title or "战术" in title or "考试" in title:
            result[pub_area]["Raids"]["joint_firing_drill"] = {
                "name": title,
                "begin_time": str(activity["begin_at"]),
                "end_time": str(activity["end_at"])
            }
        else:
            if "特别依赖" in title or "特殊任务" in title or "特别委托" in title:
                result[pub_area]["Rewards"]["commissions_rewards"] = int(title[-2])
            if "学园交流会" in title:
                result[pub_area]["Rewards"]["scrimmage_rewards"] = int(title[-2])
            if "指名手配" in title or "悬赏通缉" in title:
                result[pub_area]["Rewards"]["bounty_hunts_rewards"] = int(title[-2])
            if "日程" in title or "课程表" in title:
                result[pub_area]["Rewards"]["schedule_rewards"] = int(title[-2])
            if "任务(Normal)" in title or "任务（普通难度）" in title:
                result[pub_area]["Rewards"]["normal_mission_rewards"] = int(title[-2])
            if "任务(Hard)" in title or "任务（困难难度）" in title:
                result[pub_area]["Rewards"]["hard_mission_rewards"] = int(title[-2])
            if "老师等级经验值" in title or "帐号经验值" in title:
                result[pub_area]["Rewards"]["level_exp_rewards"] = int(title[-2])
    return result


def update_activity_bawiki():
    events_url = "https://bluearchive.wiki/wiki/Events"
    total_assault_url = "https://bluearchive.wiki/wiki/Total_Assault"
    grand_assault_url = "https://bluearchive.wiki/wiki/Grand_Assault"
    limit_break_assault_url = "https://bluearchive.wiki/wiki/Limit_Break_Assault"
    joint_firing_drill_url = "https://bluearchive.wiki/wiki/Joint_Firing_Drill"

    # ------------------------------------------------------------------------
    # Fetch event schedules and reward campaigns from Events page
    # ------------------------------------------------------------------------
    events_response = requests.get(
        url=events_url,
        headers=HEADERS,
    )
    events_html = etree.HTML(events_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_event_schedules = _table_transform(
        _fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version"]/table'),
        {
            "Name (EN)": "name",
            "Name (JP)": None,
            "Start date": "begin_time",
            "End date": "end_time",
            "Notes": None
        })
    Global_event_schedules = _table_transform(
        _fetch_activity_table(events_html, '//*[@id="tabber-Global_version"]/table'),
        {
            "Name (EN)": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Notes": None
        })
    # JP_mini_events = _fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version_2"]/table')
    # Global_mini_events = _fetch_activity_table(events_html, '//*[@id="tabber-Global_version_2"]/table')
    reward_campaigns = _fetch_activity_table(events_html, '//h1[@id="Reward_campaigns"]/following::table[1]')

    # ------------------------------------------------------------------------
    # Fetch total assaults from its page
    # ------------------------------------------------------------------------
    total_assault_response = requests.get(
        url=total_assault_url,
        headers=HEADERS,
    )
    total_assault_html = etree.HTML(total_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_total_assault = _table_transform(
        _fetch_activity_table(total_assault_html, '//*[@id="tabber-JP"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Season": None,
            "Notes": None
        })
    Global_total_assault = _table_transform(
        _fetch_activity_table(total_assault_html, '//*[@id="tabber-Global"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Season": None,
            "Notes": None
        })

    # ------------------------------------------------------------------------
    # Fetch grand assaults from its page
    # ------------------------------------------------------------------------
    grand_assault_response = requests.get(
        url=grand_assault_url,
        headers=HEADERS,
    )
    grand_assault_html = etree.HTML(grand_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_grand_assault = _table_transform(
        _fetch_activity_table(grand_assault_html, '//*[@id="tabber-JP"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Season": None,
            "Notes": None
        })
    Global_grand_assault = _table_transform(
        _fetch_activity_table(grand_assault_html, '//*[@id="tabber-Global"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Season": None,
            "Notes": None
        })

    # ------------------------------------------------------------------------
    # Fetch limit break assaults from its page
    # ------------------------------------------------------------------------
    limit_break_assault_response = requests.get(
        url=limit_break_assault_url,
        headers=HEADERS,
    )
    limit_break_assault_html = etree.HTML(limit_break_assault_response.content.decode('utf-8'),
                                          parser=etree.HTMLParser(encoding='utf-8'))
    JP_limit_break_assault = _table_transform(
        _fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-JP"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Challenge": None,
            "Season": None,
            "Notes": None
        })
    Global_limit_break_assault = _table_transform(
        _fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-Global"]/table'),
        {
            "Raid name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Challenge": None,
            "Season": None,
            "Notes": None
        })

    # ------------------------------------------------------------------------
    # Fetch joint firing drills from its page
    # ------------------------------------------------------------------------
    joint_firing_drill_response = requests.get(
        url=joint_firing_drill_url,
        headers=HEADERS,
    )
    joint_firing_drill_html = etree.HTML(joint_firing_drill_response.content.decode('utf-8'),
                                         parser=etree.HTMLParser(encoding='utf-8'))
    JP_joint_firing_drill = _table_transform(
        _fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Japanese_version"]/table'),
        {
            "Name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Special Rules": None
        })

    Global_joint_firing_drill = _table_transform(
        _fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Global_version"]/table'),
        {
            "Name": "name",
            "Start date": "begin_time",
            "End date": "end_time",
            "Special Rules": None
        })

    result = copy.deepcopy(FULL_RESULT_FORMAT)
    result.pop("CN")  # BAWiki does not offer CN server's activity data
    result["Global"].pop("Rewards")  # BAWiki does not offer Global server's reward campaigns data
    for item in reward_campaigns:
        name = item["Name"]
        if "Commissions rewards" in name:
            result["JP"]["Rewards"]["commissions_rewards"] = 2 if "Double" in name else 3
        elif "Scrimmage rewards" in name:
            result["JP"]["Rewards"]["scrimmage_rewards"] = 2 if "Double" in name else 3
        elif "Bounty Hunts rewards" in name:
            result["JP"]["Rewards"]["bounty_hunts_rewards"] = 2 if "Double" in name else 3
        elif "Schedule rewards" in name:
            result["JP"]["Rewards"]["schedule_rewards"] = 2 if "Double" in name else 3
        elif "Normal Missions rewards" in name:
            result["JP"]["Rewards"]["normal_mission_rewards"] = 2 if "Double" in name else 3
        elif "Hard Missions rewards" in name:
            result["JP"]["Rewards"]["hard_mission_rewards"] = 2 if "Double" in name else 3
        elif "level EXP" in name:
            result["JP"]["Rewards"]["level_exp_rewards"] = 2 if "Double" in name else 3
    result["JP"]["Events"], result["JP"]["Raids"]["total_assault"], result["JP"]["Raids"]["grand_assault"], \
        result["JP"]["Raids"]["limit_break_assault"], result["JP"]["Raids"]["joint_firing_drill"] = \
        JP_event_schedules, JP_total_assault, JP_grand_assault, JP_limit_break_assault, JP_joint_firing_drill
    result["Global"]["Events"], result["Global"]["Raids"]["total_assault"], result["Global"]["Raids"]["grand_assault"], \
        result["Global"]["Raids"]["limit_break_assault"], result["Global"]["Raids"]["joint_firing_drill"] = \
        Global_event_schedules, Global_total_assault, Global_grand_assault, Global_limit_break_assault, \
            Global_joint_firing_drill
    return result


def update_activity_schaledb(localization="en"):
    events_json = _download_json(f"https://schaledb.com/data/{localization}/events.min.json")
    raids_json = _download_json(f"https://schaledb.com/data/{localization}/raids.min.json")
    localization_json = _download_json(f"https://schaledb.com/data/{localization}/localization.min.json")
    config_json = _download_json("https://schaledb.com/data/config.min.json")

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

    result = copy.deepcopy(FULL_RESULT_FORMAT)
    # SchaleDB does not offer reward campaigns data
    result["JP"].pop("Rewards")
    result["Global"].pop("Rewards")
    result["CN"].pop("Rewards")

    pub_area_translator = {"Jp": "JP", "Global": "Global", "Cn": "CN"}
    for server_config in config_json["Regions"]:
        server = pub_area_translator[server_config["Name"]]
        for event in server_config["CurrentEvents"]:
            id = str(event["event"])
            if len(id) > 3:
                id = id[-3:]
            start = event["start"]
            end = event["end"]
            if start <= time.time() <= end:
                name = event_localization_dict[id]
                result[server]["Events"].append({
                    "name": name,
                    "begin_time": str(start),
                    "end_time": str(end)
                })
        for raid in server_config["CurrentRaid"]:
            raid_type = raid["type"]
            id = raid["raid"]
            start_time = raid["start"]
            end_time = raid["end"]
            current_time = time.time()
            if current_time < start_time or current_time > end_time:
                continue
            if raid_type == "Raid":
                result[server]["Raids"]["total_assault"] = {
                    "name": raid_names_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                }
            elif raid_type == "EliminateRaid":
                result[server]["Raids"]["grand_assault"] = {
                    "name": raid_names_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                }
            elif raid_type == "MultiFloorRaid":
                result[server]["Raids"]["limit_break_assault"] = {
                    "name": limit_time_assault_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                }
            elif raid_type == "TimeAttack":
                result[server]["Raids"]["joint_firing_drill"] = {
                    "name": joint_firing_drill_dict[id],
                    "begin_time": str(start_time),
                    "end_time": str(end_time)
                }

    return result


def update_activity():
    print("> Updating activity...")
    gamekee_response = update_activity_gamekee_api()
    print("### [Gamekee API](https://www.gamekee.com/v1/activity/query) Response: \n```json\n" + json.dumps(
        gamekee_response, ensure_ascii=False) + "\n```")
    bawiki_response = update_activity_bawiki()
    print("### [Blue Archive Wiki](https://bluearchive.wiki/wiki/Main_Page) Response: \n```json\n" + json.dumps(
        bawiki_response, ensure_ascii=False) + "\n```")
    schaledb_response = update_activity_schaledb()
    print("### [SchaleDB](https://schaledb.com/home) Response: \n```json\n" + json.dumps(
        schaledb_response, ensure_ascii=False) + "\n```")

    # For final result, we prefer BAWiki > SchaleDB > Gamekee API
    final_result = _unify_table(bawiki_response, schaledb_response, FULL_RESULT_FORMAT)
    final_result = _unify_table(final_result, gamekee_response, FULL_RESULT_FORMAT)

    print("### Final Merged Result: \n```json\n" + json.dumps(final_result, ensure_ascii=False, indent=4) + "\n```\n")
    return final_result


if __name__ == "__main__":
    log_path = os.path.join(os.path.dirname(__file__), "activity_update_log.md")
    activity_json_path = os.path.join(os.path.dirname(__file__), "activity.json")
    tmp_json_path = os.path.join(os.path.dirname(__file__), "tmp_activity.json")

    with open(log_path, "w", encoding="utf-8") as output:
        with redirect_stdout(output), redirect_stderr(output):
            final_result = update_activity()

            # determine if any data is updated
            if os.path.exists(activity_json_path):
                with open(os.path.abspath(activity_json_path), "r", encoding="utf-8") as f:
                    original_data = json.load(f)
                    original_data.pop("last_update_time")  # remove last_update_time for comparison
                    if original_data == final_result:
                        print("> No changes detected in activity data. Exiting without updating the file.")
                        sys.exit(0)

            final_result["last_update_time"] = int(time.time())
            ordered_keys = ["last_update_time", "JP", "Global", "CN"]
            ordered_result = OrderedDict((k, final_result[k]) for k in ordered_keys if k in final_result)
            with open(tmp_json_path, "w", encoding="utf-8") as f:
                json.dump(ordered_result, f, ensure_ascii=False, indent=4)
            print("> Activity data has been updated and saved.")
