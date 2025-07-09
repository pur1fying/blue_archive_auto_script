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
    url = "https://bluearchive.wiki/wiki/Events#tabber-tabpanel-Japanese_version-0"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 "
                      "Mobile Safari/537.36",
        "Content-Type": "text/html",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    response = requests.get(
        url=url,
        headers=HEADERS,
    )
    html = etree.HTML(response.content.decode('utf-8'), parser=etree.HTMLParser(encoding='utf-8'))
    JP_event_schedules = fetch_activity_table(html, '//*[@id="tabber-tabpanel-Japanese_version-0"]/table/tbody')
    Global_event_schedules = fetch_activity_table(html, '//*[@id="tabber-tabpanel-Global_version-0"]/table/tbody')
    JP_mini_events = fetch_activity_table(html, '//*[@id="tabber-tabpanel-Japanese_version-1"]/table/tbody')
    Global_mini_events = fetch_activity_table(html, '//*[@id="tabber-tabpanel-Global_version-1"]/table/tbody')
    reward_campaigns = fetch_activity_table(html, '//h1[6]/following::table[1]/tbody')
    activities = {
        "JP": {
            "event_schedules": JP_event_schedules,
            "mini_events": JP_mini_events,
            "reward_campaigns": reward_campaigns
        },
        "Global": {
            "event_schedules": Global_event_schedules,
            "mini_events": Global_mini_events,
            "reward_campaigns": reward_campaigns
        }
    }
    return activities


def update_activity(baas_thread):
    baas_thread.logger.info("Updating activity...")
    # activities = update_activity_gamekee_api()
    activities = update_activity_bawiki()
    print(json.dumps(activities, ensure_ascii=False))
    return True
