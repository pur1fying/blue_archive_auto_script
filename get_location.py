from ocr import ocr_character
import log

class locate(ocr_character):
    def __init__(self):
        super().__init__()
        self.page = ["option","choose_duty_student", "choose_supporter","set_supporter","group","help", "notice", "log_in", "sign_up", "clicK_forward", "menu", "mail","formation", "collect_daily_reward", "momo_talk1", "momo_talk2", "shop", "schedule","create","main_page","task","operational_area","road","railway","church","location_select","request_select"]
        self.feature_location = [[908,1018,198,252],[997,1051,120,172], [836,937,126,179],[1027,1075,227,274,],[1001,1078,142,177],[905,1018,172,221],
                                 [542, 640, 220, 280], [60, 113, 940, 971], [811, 860, 273, 310], [817, 1049, 917, 965],[910, 1010, 367, 420],
                                 [40, 120, 300, 345], [1771, 1835, 350, 390], [36, 126, 421, 464], [350, 413, 250, 281],[346, 413, 250, 283],
                                 [44,114,305,344],[259,322,129,166],[1366,1435,256,292],[842,904,1010,1045],[187,241,238,266],[1490,1628,238,307],
                                 [389,487,214,265],[389,487,214,265],[389,487,214,265],[1696,1832,760,832],[1567,1633,541,617]]
        self.key_word = ["选项","员", "选择", "者", "聊天", "帮助", "公告", "菜单", "天", "点击继续", "菜单", "领取", "编队", "每周", "成员", "未读", "神名", "持有","材料","小组","区域","故事","高架","沙漠","讲堂","讲堂","信"]

    def return_location(self):
        path1 = self.get_screen_shot_path()
        for i in range(0, len(self.page)):
            if self.key_word[i] == self.img_ocr(self.img_crop(path1, self.feature_location[i][0], self.feature_location[i][1], self.feature_location[i][2], self.feature_location[i][3])):
                log.o_p("CURRENT POSITION: " + self.page[i], 1)
                return self.page[i]
        log.o_p("UNKNOWN UI PAGE", 1)
        return "UNKNOWN UI PAGE"


if __name__ == '__main__':
    t = locate()
    t.return_location()
