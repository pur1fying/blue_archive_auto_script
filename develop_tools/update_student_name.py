# Usage: this script is used to update the student name list from shacleDB, updated data should be paste into
# core/default_config.py "student_names"
#
# TODO: 1.change default_config.py "student_names" to a json file 2.auto write
#  the updated data into the json file instead of paste it manually
import urllib.request
import json


def download_json(url, file_path):
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    data = json.loads(data)
    with open(file_path, 'w') as file:
        json.dump(data, file)


server = ['cn', 'en', 'jp']

url = "https://raw.githubusercontent.com/SchaleDB/SchaleDB/main/data/"
end = "/students.json"
file_path = "../src/student_name_raw/"
for i in range(0, len(server)):
    download_json(url + server[i] + end, file_path + server[i] + "_student.json")
serverid = {
    "cn": "CN",
    "en": "Global",
    "jp": "JP"
}
servernumber = {
    "CN": 2,
    "Global": 1,
    "JP": 0
}
updated = []
data = []
for i in range(0, len(server)):
    with open(file_path + server[i] + "_student.json", 'r') as file:
        data.append(json.load(file))
for j in range(0, len(data[1])):
    dic = {}
    for i in range(0, len(server)):
        IsReleased = data[i][j]['IsReleased'][servernumber[serverid[server[i]]]]
        name = data[i][j]['Name'].replace("（", "(").replace("）", ")")
        dic[serverid[server[i]] + "_name"] = name
        dic[serverid[server[i]] + "_implementation"] = IsReleased
    updated.insert(0, dic)
for i in range(0, len(updated)):
    print(updated[i])
result = {
    "student_names": updated
}
str = json.dumps(result, ensure_ascii=False, indent=2)
print(str)  # paste output into core/default_config.py "student_names"




