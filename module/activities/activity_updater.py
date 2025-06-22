import json
import time

import requests


def update_activity(baas_thread):
    baas_thread.logger.info("Updating activity...")
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
        activities[pub_area].append({"title": activity_title, "begin_time": begin_time, "end_time": end_time})
    print(json.dumps(activities, ensure_ascii=False))
    return True
