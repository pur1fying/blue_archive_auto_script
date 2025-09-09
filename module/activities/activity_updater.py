import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from lxml import etree


def update_activity_gamekee_api():
    activities = {}
    api_url = "https://www.gamekee.com/v1/activity/query"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 "
                      "Mobile Safari/537.36",
        "Content-Type": "text/html",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'game-alias': 'ba'
    }
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
    total_assault_html = etree.HTML(total_assault_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_total_assault  = fetch_activity_table(total_assault_html,'//*[@id="tabber-JP"]/table')
    Global_total_assault = fetch_activity_table(total_assault_html,'//*[@id="tabber-Global"]/table')

    grand_assault_response = requests.get(
        url=grand_assault_url,
        headers=HEADERS,
    )
    grand_assault_html = etree.HTML(grand_assault_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_grand_assault  = fetch_activity_table(grand_assault_html,'//*[@id="tabber-JP"]/table')
    Global_grand_assault = fetch_activity_table(grand_assault_html,'//*[@id="tabber-Global"]/table')

    limit_break_assault_response = requests.get(
        url=limit_break_assault_url,
        headers=HEADERS,
    )
    limit_break_assault_html = etree.HTML(limit_break_assault_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_limit_break_assault  = fetch_activity_table(limit_break_assault_html,'//*[@id="tabber-JP"]/table')
    Global_limit_break_assault = fetch_activity_table(limit_break_assault_html,'//*[@id="tabber-Global"]/table')

    joint_firing_drill_response = requests.get(
        url=joint_firing_drill_url,
        headers=HEADERS,
    )
    joint_firing_drill_html = etree.HTML(joint_firing_drill_response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_joint_firing_drill  = fetch_activity_table(joint_firing_drill_html,'//*[@id="tabber-Japanese_version"]/table')
    Global_joint_firing_drill = fetch_activity_table(joint_firing_drill_html,'//*[@id="tabber-Global_version"]/table')

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


def update_activity(baas_thread):
    baas_thread.logger.info("Updating activity...")
    # activities = update_activity_gamekee_api()
    activities = update_activity_bawiki()
    print(json.dumps(activities, ensure_ascii=False))
    return True
