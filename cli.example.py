from core.Baas_thread import Baas_thread
from gui.util.config_set import ConfigSet
from main import Main


def main():
    main = Main(ocr_needed=["NUM", "Global", "JP"])  # 日服也必须要 Global，否则会崩溃
    main.init_static_config()
    config = ConfigSet(config_dir="jp_kisaki") # 修改为自己的配置目录名
    baas = Baas_thread(config, None, None, None)
    baas.static_config = main.static_config
    baas.init_all_data()
    baas.ocr = main.ocr  # type: ignore

    baas.solve("restart")  # 重启游戏

    core_tasks(baas)  # 核心任务，无论何时都应该执行
    event_tasks(baas)  # 活动任务，根据活动开放情况选择执行
    # extra_tasks(baas)  # 额外任务，根据实际需求选择执行

    baas.solve("collect_reward")  # 领取奖励


def core_tasks(baas):
    baas.solve("cafe_reward")  # 咖啡厅
    baas.solve("lesson")  # 课程表
    baas.solve("collect_reward")  # 领取奖励
    baas.solve("group")  # 社团
    baas.solve("mail")  # 邮件
    baas.solve("common_shop")  # 一般商店
    baas.solve("tactical_challenge_shop")  # 战术大赛（竞技场）商店
    baas.solve("create")  # 制造
    baas.solve("rewarded_task")  # 悬赏通缉
    baas.solve("arena")  # 战术大赛（竞技场）


def event_tasks(baas):
    baas.solve("activity_sweep")  # 活动扫荡


def extra_tasks(baas):
    baas.solve("clear_special_task_power")  # 特殊任务（活动报告和信用货币）
    baas.solve("scrimmage")  # 学园交流会


if __name__ == "__main__":
    main()
