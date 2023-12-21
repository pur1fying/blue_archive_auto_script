

x = {
    'notice': (589, 151, 619, 182),
    'notice2': (588, 167, 619, 197),
    'limited': (610, 146, 640, 175),  # 购买次数上限 或 持有体力上限
    'buy20': (632, 268, 656, 288),
    'buy19': (632, 268, 656, 288),
    'buy18': (632, 268, 656, 288),
    'buy17': (632, 268, 656, 288),
    'buy16': (632, 268, 656, 288),
    'buy15': (632, 268, 656, 288),
    'buy14': (632, 268, 656, 288),
    'buy13': (632, 268, 656, 288),
    'buy12': (632, 268, 656, 288),
    'buy11': (632, 268, 656, 288),
    'buy10': (632, 268, 656, 288),
    'buy9': (632, 268, 656, 288),
    'buy8': (632, 268, 656, 288),
    'buy7': (632, 268, 656, 288),
    'buy6': (632, 268, 656, 288),
    'buy5': (632, 268, 656, 288),
    'buy4': (632, 268, 656, 288),
    'buy3': (632, 268, 656, 288),
    'buy2': (632, 268, 656, 288),
    'buy1': (632, 268, 656, 288),
}


def to_buy_ap(self):
    possible = {
        'home_home-feature': (619, 37, 3),
    }
    end = {
        ('buy_ap_limited', 3),
        ('buy_ap_notice', 3),
    }
    return image.detect(self, end, possible, pre_argv=home.go_home(self))


def start(self):
    if self.server == 'CN':
        res = to_buy_ap(self)

        # 购买上限检查
        if res == 'buy_ap_limited':
            return home.go_home(self)

        try:
            need_count = self.tc['config']['count']
            purchased_count = 20 - calc_surplus_count(self)
            # 次数已满
            if need_count <= purchased_count:
                return home.go_home(self)
            # 计算还要购买的次数
            buy_count = need_count - purchased_count
            # 增加次数
            self.click(806, 345, False, min(buy_count, 3) - 1)
            # 点击确认
            self.click(770, 501, False)

            # 确认购买弹窗检测
            if image.compare_image(self, 'buy_ap_notice2', 5):
                # 再次确认购买
                self.click(768, 485, False)

            # 确认超出持有上限弹窗
            if image.compare_image(self, 'buy_ap_limited', 5):
                # 延迟重新运行
                self.finish_seconds = 30
                return home.go_home(self)

            # 关闭获得奖励
            stage.close_prize_info(self, False, True)
            # 如果要购买的次数大于3次,再次运行
            if buy_count > 3:
                return start(self)
        except ValueError:
            self.logger.info("次数识别失败")
        home.go_home(self)
    elif self.server == "Global":
        self.logger.info("Global server not support")


def calc_surplus_count(self):
    """
    计算剩余购买次数,这里必须用图片匹配才能精准,用文字识别小数字必出bug
    """
    for i in range(20, 0, -1):
        if image.compare_image(self, 'buy_ap_buy{0}'.format(i), 0):
            return i
    return 0
