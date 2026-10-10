import os
import time
from datetime import datetime


def implement(self):
    if not self.is_android_device:
        return True
    cur_package = self.u2.app_current()["package"]
    if cur_package != self.package_name:
        if cur_package != self.package_name:
            self.logger.warning("APP NOT RUNNING current package: " + cur_package)
        start(self)
        return True
    self.logger.info("CHECK RESTART")
    if check_need_restart(self):
        self.logger.info("current package: " + cur_package)
        self.logger.info("--STOP CURRENT BLUE ARCHIVE--")
        self.u2.app_stop(self.package_name)
        time.sleep(2)
        start(self)
        _mark_day_restart_done(self)
        return True
    return True


def start(self):
    self.logger.info("-- START BLUE ARCHIVE --")
    activity_name = self.activity_name
    if self.server == "CN":
        activity_name = None
    self.u2.app_start(self.package_name, activity_name)
    self.to_main_page()


def _config_dir(self) -> str:
    for attr in ("config_path", "config_dir"):
        try:
            v = getattr(self, attr, None)
            if v:
                return str(v)
        except Exception:
            pass
    try:
        cs = getattr(self, "config_set", None)
        v = getattr(cs, "config_dir", None) if cs is not None else None
        if v:
            return str(v)
    except Exception:
        pass
    return "."


def _day_flag_path(self) -> str:
    return os.path.join(_config_dir(self), "hoard_ap_day_restart.flag")


def _mark_day_restart_done(self) -> None:
    try:
        day_key = datetime.now().strftime("%Y-%m-%d")
        with open(_day_flag_path(self), "w", encoding="utf-8") as f:
            f.write(day_key)
    except Exception as e:
        # 旗标写失败=下一轮 04:00 窗口会再重启一次，行为安全但要知道
        try:
            self.logger.warning(f"[hoard_ap] 日界重启旗标写入失败: {e}")
        except Exception:
            pass


def _already_restarted_today(self) -> bool:
    try:
        p = _day_flag_path(self)
        if not os.path.isfile(p):
            return False
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip() == datetime.now().strftime("%Y-%m-%d")
    except Exception:
        return False


def check_need_restart(self):
    """国服日界 04:00 必须关开一次。

    原逻辑仅 ±60 秒命中：4:01 再进调度会直接跳过，后续被日界弹窗卡死。
    现改为：重置时刻起 30 分钟窗口内，每天强制一次（同日旗标防连刷）。
    """
    now = datetime.now()
    if _already_restarted_today(self):
        return False
    if self.server == "CN":
        reset_h = 4
    elif self.server in ("Global", "JP"):
        reset_h = 3
    else:
        return False
    reset_at = datetime(year=now.year, month=now.month, day=now.day, hour=reset_h)
    # 窗口：[reset, reset+30min]
    delta = (now - reset_at).total_seconds()
    if 0 <= delta <= 30 * 60:
        return True
    # 仍保留原 ±60s（时钟略快时）
    if abs(time.time() - reset_at.timestamp()) <= 60:
        return True
    return False
