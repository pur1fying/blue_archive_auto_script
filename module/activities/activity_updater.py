import copy
import difflib
import json
import logging
import os
import re
import sys
import time
from collections import OrderedDict
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

DEFAULT_HEADER_MAP = {
    "Name (EN)": "name",
    "Name (JP)": None,
    "Raid name": "name",
    "Start Date": "begin_time",
    "End Date": "end_time",
    "Period": None,
    "Notes": None,
    "Season": None,
    "Stages": None,
    "Challenge": None,
    "Special Rules": None,
    "": None,
}


def _fetch_activity_table(html, xpath: str, header_map: dict = None, force_list: bool = False):
    activities = []

    # Locate the table using the provided XPath
    try:
        event_schedules = html.xpath(xpath)[0]
    except IndexError:
        raise KeyError("No event table found with the provided XPath.")

    event_trs = event_schedules.xpath('.//tr')
    if len(event_trs) < 1:
        raise KeyError("No event data found.")

    # Extract table headers
    headers = [''.join(th.itertext()).strip() for th in event_trs[0]]

    start_date_index = headers.index('Start date') if 'Start date' in headers else -1
    end_date_index = headers.index('End date') if 'End date' in headers else -1
    period_index = headers.index('Period') if 'Period' in headers else -1
    for event_tr in event_trs[1:]:
        values = [''.join(item.itertext()).strip() for item in event_tr]

        # If there's a start and end date column, convert them to epoch time
        if start_date_index != -1 and end_date_index != -1:
            start_time, end_time = _to_epoch_time(values[start_date_index]), _to_epoch_time(values[end_date_index])

            # Skip events that are not active
            current_time = int(time.time())
            if current_time < start_time or current_time > end_time:
                continue

            values[start_date_index], values[end_date_index] = str(start_time), str(end_time)
        if period_index != -1:
            dates = values[period_index].split(' ~ ')
            if len(dates) != 2:
                raise KeyError("Period column does not contain valid start and end dates.")
            start_time, end_time = _to_epoch_time(dates[0]), _to_epoch_time(dates[1])

            # Skip events that are not active
            current_time = int(time.time())
            if current_time < start_time or current_time > end_time:
                continue

            # Manually add begin_time and end_time columns
            headers += ["begin_time", "end_time"]
            values += [str(start_time), str(end_time)]

        # update the table with key_map settings
        if header_map is None:
            header_map = {}
        header_map.update(DEFAULT_HEADER_MAP)
        pop_list = []
        for i in range(len(headers)):
            if headers[i] in header_map:
                if header_map[headers[i]] is not None:
                    headers[i] = header_map[headers[i]]
                else:
                    pop_list.insert(0, i)
        for idx in pop_list:
            headers.pop(idx)
            values.pop(idx)
        activities.append(dict(zip(headers, values)))
    # Sort activities by end date
    activities.sort(key=lambda x: x[headers[2]], reverse=True)
    if not force_list:
        if len(activities) == 0:
            return None
        elif len(activities) == 1:
            return activities[0]
    return activities


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
    logger = logging.getLogger("activity_updater")
    for i in range(4):
        response = requests.get(
            url=url,
            headers=HEADERS,
        )
        if response.status_code != 200:
            logger.error(f"Failed to fetch data from {url}, error code: {response.status_code},retry {i + 1}/3")
            continue
        return response.json()
    raise ValueError(f"Failed to fetch data from {url}")


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
    response = requests.get(
        url="https://www.gamekee.com/v1/activity/query",
        headers=HEADERS,
        params={
            "active_at": int(time.time())
        }
    )
    if response.status_code != 200 or response.json()["code"] != 0:
        print(f"Failed to fetch activity data, error code: {response.status_code} | {response.json()['code']}")
        return None

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

        activity_info = {
            "name": title,
            "begin_time": str(activity["begin_at"]),
            "end_time": str(activity["end_at"])
        }

        if title.startswith("[活动]"):
            result[pub_area]["Events"].append(activity_info)
        elif title.startswith("总力战"):
            result[pub_area]["Raids"]["total_assault"] = activity_info
        elif title.startswith("大决战"):
            result[pub_area]["Raids"]["grand_assault"] = activity_info
        elif title.startswith("制约解除决战"):
            result[pub_area]["Raids"]["limit_break_assault"] = activity_info
        elif "演习" in title or "战术" in title or "考试" in title:
            result[pub_area]["Raids"]["joint_firing_drill"] = activity_info
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
        headers=HEADERS
    )
    events_html = etree.HTML(events_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_event_schedules = _fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version"]/table',
                                               force_list=True)
    Global_event_schedules = _fetch_activity_table(events_html, '//*[@id="tabber-Global_version"]/table',
                                                   force_list=True)
    # JP_mini_events = _fetch_activity_table(events_html, '//*[@id="tabber-Japanese_version_2"]/table')
    # Global_mini_events = _fetch_activity_table(events_html, '//*[@id="tabber-Global_version_2"]/table')
    reward_campaigns = _fetch_activity_table(events_html, '//h1[@id="Reward_campaigns"]/following::table[1]',
                                             force_list=True)

    # ------------------------------------------------------------------------
    # Fetch total assaults from its page
    # ------------------------------------------------------------------------
    total_assault_response = requests.get(
        url=total_assault_url,
        headers=HEADERS
    )
    total_assault_html = etree.HTML(total_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_total_assault = _fetch_activity_table(total_assault_html, '//*[@id="tabber-JP"]/table')
    Global_total_assault = _fetch_activity_table(total_assault_html, '//*[@id="tabber-Global"]/table')

    # ------------------------------------------------------------------------
    # Fetch grand assaults from its page
    # ------------------------------------------------------------------------
    grand_assault_response = requests.get(
        url=grand_assault_url,
        headers=HEADERS
    )
    grand_assault_html = etree.HTML(grand_assault_response.content.decode('utf-8'),
                                    parser=etree.HTMLParser(encoding='utf-8'))
    JP_grand_assault = _fetch_activity_table(grand_assault_html, '//*[@id="tabber-JP"]/table')
    Global_grand_assault = _fetch_activity_table(grand_assault_html, '//*[@id="tabber-Global"]/table')

    # ------------------------------------------------------------------------
    # Fetch limit break assaults from its page
    # ------------------------------------------------------------------------
    limit_break_assault_response = requests.get(
        url=limit_break_assault_url,
        headers=HEADERS
    )
    limit_break_assault_html = etree.HTML(limit_break_assault_response.content.decode('utf-8'),
                                          parser=etree.HTMLParser(encoding='utf-8'))
    JP_limit_break_assault = _fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-JP"]/table')
    Global_limit_break_assault = _fetch_activity_table(limit_break_assault_html, '//*[@id="tabber-Global"]/table')

    # ------------------------------------------------------------------------
    # Fetch joint firing drills from its page
    # ------------------------------------------------------------------------
    joint_firing_drill_response = requests.get(
        url=joint_firing_drill_url,
        headers=HEADERS
    )
    joint_firing_drill_html = etree.HTML(joint_firing_drill_response.content.decode('utf-8'),
                                         parser=etree.HTMLParser(encoding='utf-8'))
    JP_joint_firing_drill = _fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Japanese_version"]/table')

    Global_joint_firing_drill = _fetch_activity_table(joint_firing_drill_html, '//*[@id="tabber-Global_version"]/table')

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

    localization_dict = {
        "Events": {},
        "Raid": {},
        "EliminateRaid": {},
        "MultiFloorRaid": {},
        "TimeAttack": {}
    }
    raid_type_translator = {
        "Raid": "total_assault",
        "EliminateRaid": "grand_assault",
        "MultiFloorRaid": "limit_break_assault",
        "TimeAttack": "joint_firing_drill"
    }
    pub_area_translator = {"Jp": "JP", "Global": "Global", "Cn": "CN"}

    ##########################################
    # prepare localization dict
    ##########################################

    # get event name from localization
    localization_dict["Events"] = localization_json["EventName"]

    # total assault, grand assault, limit break assault has the same structure
    # total assault and grand assault share the same data source
    for type in ["Raid", "MultiFloorRaid"]:
        for event in raids_json[type]:
            raid_id = event["Id"]
            raid_name = event["Name"]
            localization_dict[type][raid_id] = raid_name
    localization_dict["EliminateRaid"] = localization_dict["Raid"]

    for joint_firing_drill in raids_json["TimeAttack"]:
        id = joint_firing_drill["Id"]
        joint_firing_drill_type = joint_firing_drill["DungeonType"]
        name = localization_json["TimeAttackStage"][joint_firing_drill_type]
        localization_dict["TimeAttack"][id] = name

    ##########################################
    # generate result table
    ##########################################
    result = copy.deepcopy(FULL_RESULT_FORMAT)
    # SchaleDB does not offer reward campaigns data
    result["JP"].pop("Rewards")
    result["Global"].pop("Rewards")
    result["CN"].pop("Rewards")

    for server_config in config_json["Regions"]:
        server = pub_area_translator[server_config["Name"]]
        for event in server_config["CurrentEvents"]:
            id = str(event["event"])

            # often SchaleDB mark 10 prefix as a rerun event, we only keep the last 3 digits for localization
            if len(id) > 3:
                id = id[-3:]
            begin_time = event["start"]
            end_time = event["end"]
            if begin_time <= time.time() <= end_time:
                result[server]["Events"].append({
                    "name": localization_dict["Events"][id],
                    "begin_time": str(begin_time),
                    "end_time": str(end_time)
                })
        for event in server_config["CurrentRaid"]:
            raid_type = event["type"]
            id = event["raid"]
            start_time = event["start"]
            end_time = event["end"]
            current_time = time.time()
            if current_time < start_time or current_time > end_time:
                continue

            result[server]["Raids"][raid_type_translator[raid_type]] = {
                "name": localization_dict[raid_type][id],
                "begin_time": str(start_time),
                "end_time": str(end_time)
            }

    return result


def update_activity():
    logger = logging.getLogger("activity_updater")
    try:
        logger.info("Retrieving activity data from Gamekee API...")
        gamekee_response = update_activity_gamekee_api()
        logger.info("Gamekee API Response:\n%s", json.dumps(gamekee_response, ensure_ascii=False, indent=4))

        logger.info("Retrieving activity data from Blue Archive Wiki...")
        bawiki_response = update_activity_bawiki()
        logger.info("Blue Archive Wiki Response:\n%s", json.dumps(bawiki_response, ensure_ascii=False, indent=4))

        logger.info("Retrieving activity data from SchaleDB...")
        schaledb_response = update_activity_schaledb()
        logger.info("SchaleDB Response:\n%s", json.dumps(schaledb_response, ensure_ascii=False, indent=4))

        # For final result, we prefer BAWiki > SchaleDB > Gamekee API
        logger.info("Merging activity data...")
        final_result = _unify_table(bawiki_response, schaledb_response, FULL_RESULT_FORMAT)
        final_result = _unify_table(final_result, gamekee_response, FULL_RESULT_FORMAT)

        logger.info("Final Result:\n%s", json.dumps(final_result, ensure_ascii=False, indent=4))
        return final_result
    except Exception as e:
        logger.error(f"An error occurred during the activity update process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logger = logging.getLogger("activity_updater")
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter('<%(asctime)s> [%(levelname)s] <%(message)s>', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    activity_json_path = os.path.join(os.path.dirname(__file__), "activity.json")
    tmp_json_path = os.path.join(os.path.dirname(__file__), "tmp_activity.json")
    pr_body_md_path = os.path.join(os.path.dirname(__file__), "activity_update_log.md")

    logger.info("Starting activity information retrieval and merging process...")
    final_result = update_activity()
    logger.info("Activity information retrieval and merging process completed.")
    # determine if any data is updated
    if os.path.exists(activity_json_path):
        with open(activity_json_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)
            original_data.pop("last_update_time")  # remove last_update_time for comparison
            if original_data == final_result:
                logger.info("No updates in activity data, exiting...")
                sys.exit(0)
    logger.info("Changes detected in activity data, updating activity.json...")
    final_result["last_update_time"] = int(time.time())
    ordered_keys = ["last_update_time", "JP", "Global", "CN"]
    ordered_result = OrderedDict((k, final_result[k]) for k in ordered_keys if k in final_result)
    with open(tmp_json_path, "w", encoding="utf-8") as f:
        json.dump(ordered_result, f, ensure_ascii=False, indent=4)
    logger.info("Updated data written to temporary file tmp_activity.json.")

    # generating pr body markdown
    with open(pr_body_md_path, "w", encoding="utf-8") as f:
        f.write("### Detected a change in activity data, details as follows:\n\n")
        with open(activity_json_path, 'r', encoding='utf-8') as f1, open(tmp_json_path, 'r', encoding='utf-8') as f2:
            old_data, new_data = f1.readlines(), f2.readlines()

        diff = difflib.unified_diff(old_data, new_data)
        f.write("```diff\n")
        f.writelines(diff)
        f.write("\n```\n")
        f.write("> All data are up-to-date. Requesting a review.\n")
        repo_owner = os.environ.get('GITHUB_REPOSITORY_OWNER', 'repository-owner')
        f.write(f"\n> **Repository Owner**: @{repo_owner}\n")
        f.write(f"\n> Last update time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    logger.info("Pull request body markdown generated at activity_update_log.md.")
