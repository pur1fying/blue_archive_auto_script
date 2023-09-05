import time
from ocr import ocr_character
from screen_operation import screen_operate


class locate(ocr_character, screen_operate):
    def __init__(self):
        ocr_character.__init__(self)
        screen_operate.__init__(self)
        self.keyword = ["总力战信息", "区域", "排名", "奖励", "奖励信息", "调整编队", "部队", "选择值日员", "更新",
                        "增益", "袭击", "火车", "确认", "聊天", "组员列表", "点击继续", "访问", "自动加入",
                        "扫荡完成", "任务信息", "材料", "进入剧情", "剧情信息", "选择剧情", "变更", "全部收纳",
                        "邀请券", "库存", "第1任务", "第2任务", "第3任务", "第4任务", "第5任务", "第6任务", "第7任务",
                        "第8任务", "第9任务", "第10任务", "第11任务", "第12任务", "第13任务", "第14任务", "第15任务",
                        "第16任务", "第17任务", "第18任务", "第19任务", "第20任务", "第21任务", "第22任务", "第23任务", "第24任务",
                        "第二任务", "预设", "收益", "家具信息", "基本信息", "经验值", "好感等级", "说明", "主要能力值", "游戏",
                        "图像", "音量", "成就", "沙勒业务区", "沙勒生活区", "歌赫娜中央区", "阿拜多斯高等学院", "千禧年学习区",
                        "制造", "种类", "使用", "单价", "成员等级", "成员列表", "筛选", "排序", "道具", "装备", "主线",
                        "支线", "日程报告", "对战纪录", "防御编队", "选择购买", "挑战次数不足", "入场券不足",
                        "档案", "普通", "困难", "帮助", "邀请券", "礼物", "特别委托", "据点", "工厂", "广场", "信用",
                        "讲堂", "详细信息", "】开启", "已更新",
                        "高架", "铁路", "预设", "点击继续", "公告", "活动", "通知", "跳过", "预告", "咖啡厅", "日程",
                        "成员", "日程信息","对战结果","失败",
                        "工作任务", "编队", "小组", "材料列表", "商店", "招募", "业务区", "任务", "故事", "悬赏通缉",
                        "帮助", "选项", "队长", "支援",
                        "菜单", "青辉石", "礼包", "购买", "账号信息", "账号设置", "学院", "部队编组", "邮箱", "过期邮件",
                        "领取记录", "对手信息", "等级提升", "节点信息",
                        "每日", "每周", "切换账号", "天", "全部查看", "列表", "启动", "选择日程", "全部日程",
                        "日程券信息"]
        self.keyword_apper_time_dictionary = {i: 0 for i in self.keyword}

    def build_next_array(self, patten):
        next_array = [0]
        prefix_len = 0
        i = 1
        while i < len(patten):
            if patten[prefix_len] == patten[i]:
                prefix_len += 1
                next_array.append(prefix_len)
                i += 1
            else:
                if prefix_len == 0:
                    next_array.append(0)
                    i += 1
                else:
                    prefix_len = next_array[prefix_len - 1]
        return next_array

    def pd(self, list1, list2):
        for i in range(0, len(list1)):
            if self.keyword_apper_time_dictionary[list1[i]] < list2[i]:
                return False
        return True

    def return_location(self):

        if self.pd(["选项", "游戏", "图像", "音量"], [1, 1, 1, 1]):
            return "option"
        elif self.pd(["预告"], [1]) or self.pd(["】开启"], [1]) or self.pd(["已更新"], [1]):
            return "main_notice"
        elif self.pd(["对手信息"], [1]):
            return "component_message"
        elif self.pd(["对战结果"], [1]) or self.pd(["失败", "确认"], [1, 1]) :
            return "combat_result"
        elif self.pd(["节点信息"], [1]):
            return "node_information"
        elif self.pd(["详细信息"], [1]):
            return "detailed_message"
        elif self.pd(["通知"], [1]):
            if self.pd(["挑战次数不足"], [1]) or self.pd(["入场券不足"], [1]):
                return "charge_notice"
            else:
                return "notice"
        elif self.pd(["日程信息"], [1]):
            return "schedule_message"
        elif self.pd(["点击继续"], [1]):
            return "click_forward"
        elif self.pd(["聊天", "组员列表"], [1, 1]):
            return "group"
        elif self.pd(["访问", "自动加入"], [1, 1]):
            return "-group"
        elif self.pd(["帮助"], [1]):
            return "help"
        elif self.pd(["日程券信息"], [1]):
            return "schedule_ticket_message"
        elif self.pd(["日程报告"], [1]):
            return "schedule_report"
        elif self.pd(["等级提升"], [1]):
            return "positive_impression_up"
        elif self.pd(["天"], [6]):
            return "sign_in"
        elif self.pd(["全部日程", "奖励"], [1, 1]):
            if self.pd(["沙勒业务区"], [1]):
                return "schedule1"
            elif self.pd(["沙勒生活区"], [1]):
                return "schedule2"
            elif self.pd(["歌赫娜中央区"], [1]):
                return "schedule3"
            elif self.pd(["阿拜多斯高等学院"], [1]):
                return "schedule4"
            elif self.pd(["千禧年学习区"], [1]):
                return "schedule5"
            else:
                return "UNKNOWN UI PAGE"
        elif self.pd(["切换账号"], [1]):
            return "log_in"
        elif self.pd(["任务信息"], [1]):
            return "task_message"
        elif self.pd(["总力战信息"], [1]):
            return "total_force_message"
        elif self.pd(["选择值日员"], [1]):
            return "choose_person_on_duty"
        elif self.pd(["扫荡完成", "确认"], [1, 1]) or self.pd(["奖励", "确认"], [1, 1]):
            return "task_finish"
        elif self.pd(["调整编队"], [1]):
            return "adjust_formation"
        elif self.pd(["基本信息", "家具信息"], [1, 1]):
            return "cafe_message"
        elif self.pd(["预设"], [3]):
            return "preset"
        elif self.pd(["库存"], [1]):
            return "furniture"
        elif self.pd(["账号设置"], [1]):
            return "set_account_message"
        elif self.pd(["说明"], [1]):
            return "declaration"
        elif self.pd(["收益"], [2]):
            return "cafe_reward"
        elif self.pd(["成员列表", "成员等级"], [1, 1]):
            return "member_arrangement"
        elif self.pd(["账号信息", "变更"], [1, 1]):
            return "account_message"
        elif self.pd(["对战纪录", "防御编队"], [1, 1]):
            return "arena"
        elif self.pd(["菜单"], [1]):
            return "menu"
        elif self.pd(["青辉石"], [2]) or self.pd(["礼包"], [2]):
            return "recharge"
        elif self.pd(["单价"], [1]):
            return "charge_power"

        elif self.pd(["奖励"], [3]):
            return "schedule"
        elif self.pd(["全部日程"], [1]):
            return "all_schedule"
        elif self.pd(["材料列表"], [1]):
            return "manufacture_store"
        elif self.pd(["工作任务", "每日", "每周"], [1, 1, 1]) or self.pd(["成就", "每日", "每周"], [1, 1, 1]):
            return "work_task"
        elif self.pd(["全部查看", "列表", "启动"], [1, 1, 1]):
            return "create"
        elif self.pd(["编队", "队长", "支援"], [1, 1, 1]):
            return "attack_formation"
        elif self.pd(["过期邮件", "领取记录"], [1, 1]):
            return "mail"
        elif self.pd(["部队编组"], [1]):
            return "formation"
        elif self.pd(["全部收纳"], [1]) or self.pd(["邀请券"], [1]):
            return "cafe"
        elif self.pd(["招募"], [3]):
            return "recruit"
        elif self.pd(["经验值", "信用"], [1, 1]):
            return "choose_special_task"
        elif self.pd(["广场"], [3]):
            return "special_task_credit"
        elif self.pd(["工厂"], [3]):
            return "special_task_guard"
        elif self.pd(["高架"], [3]):
            return "rewarded_task_road"
        elif self.pd(["火车"], [3]):
            return "rewarded_task_rail"
        elif self.pd(["讲堂"], [3]) or self.pd(["增益", "袭击"], [1, 1]):
            return "rewarded_task_classroom"
        elif self.pd(["部队"], [3]):
            return "troop_formation"
        elif self.pd(["装备", "主要能力值"], [1, 1]):
            if self.pd(["排序"], [1]):
                return "sort_equipment"
            else:
                return "equipment"
        elif self.pd(["成员列表", "成员等级"], [1, 1]):
            return "member_arrangement"
        elif self.pd(["奖励信息", "排名"], [1, 1]):
            return "total_force_fight"
        elif self.pd(["道具", "使用"], [1, 1]):
            if self.pd(["排序"], [1]):
                return "sort_item"
            elif self.pd(["筛选", "种类"], [1, 1]):
                return "item_filter"
            else:
                return "item"
        elif self.pd(["悬赏通缉", "任务"], [1, 1, 1]):
            return "business_area"
        elif self.pd(["第24任务"], [1]):
            return "task_24"
        elif self.pd(["第23任务"], [1]):
            return "task_23"
        elif self.pd(["第22任务"], [1]):
            return "task_22"
        elif self.pd(["第21任务"], [1]):
            return "task_21"
        elif self.pd(["第20任务"], [1]):
            return "task_20"
        elif self.pd(["第19任务"], [1]):
            return "task_19"
        elif self.pd(["第18任务"], [1]):
            return "task_18"
        elif self.pd(["第17任务"], [1]):
            return "task_17"
        elif self.pd(["第16任务"], [1]):
            return "task_16"
        elif self.pd(["第15任务"], [1]):
            return "task_15"
        elif self.pd(["第14任务"], [1]):
            return "task_14"
        elif self.pd(["第13任务"], [1]):
            return "task_13"
        elif self.pd(["第12任务"], [1]):
            return "task_12"
        elif self.pd(["第11任务"], [1]):
            return "task_11"
        elif self.pd(["第10任务"], [1]):
            return "task_10"
        elif self.pd(["第9任务"], [1]):
            return "task_9"
        elif self.pd(["第8任务"], [1]):
            return "task_8"
        elif self.pd(["第7任务"], [1]):
            return "task_7"
        elif self.pd(["第6任务"], [1]):
            return "task_6"
        elif self.pd(["第5任务"], [1]):
            return "task_5"
        elif self.pd(["第4任务"], [1]):
            return "task_4"
        elif self.pd(["第3任务"], [1]):
            return "task_3"
        elif self.pd(["第2任务"], [1]):
            return "task_2"
        elif self.pd(["第1任务"], [1]):
            return "task_1"
        elif self.pd(["讲堂", "铁路", "材料"], [1, 1, 1]):
            return "rewarded_task"
        elif self.pd(["公告", "活动", "预告"], [1, 1, 1]):
            return "story_choose"
        elif self.pd(["主线", "支线", "档案", "故事"], [1, 1, 1, 3]):
            return "choose_event"
        elif self.pd(["制造", "成员", "商店", "小组"], [1, 1, 1, 1]):
            if self.pd(["学院"], [1]) or self.pd(["好感等级"], [1]):
                return "momo_talk"
            else:
                return "main_page"
        elif self.pd(["购买", "更新"], [3, 1]) or self.pd(["购买", "选择购买"], [3, 1]):
            return "shop"
        else:
            return "UNKNOWN UI PAGE"

    def kmp(self, patten, string):
        next_array = self.build_next_array(patten)
        i = 0
        j = 0
        cnt = 0
        len1 = len(patten)
        len2 = len(string) - 1
        while i <= len2:
            if string[i] == patten[j]:
                i += 1
                j += 1
            elif j >= 1:
                j = next_array[j - 1]
            else:
                i += 1
            if j == len1:
                cnt += 1
                j = next_array[j - 1]
        return cnt

    def get_keyword_appear_time(self, string):
        for i in range(0, len(self.keyword)):
            self.keyword_apper_time_dictionary[self.keyword[i]] = self.kmp(self.keyword[i], string)
        #  print(self.keyword[i], " ", self.keyword_apper_time_dictionary[self.keyword[i]])


if __name__ == '__main__':
    t1 = time.time()
    t = locate()
    path = t.get_screen_shot_array()
    t.get_keyword_appear_time(t.img_ocr(path))
    print(t.return_location())
    t4 = time.time()
    print(t4 - t1)
