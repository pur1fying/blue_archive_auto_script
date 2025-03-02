import asyncio
import threading

from core.Baas_thread import Baas_thread
from core.config.config_set import ConfigSet
from main import Main

baas_lock = threading.Lock()


def baas_solve_with_lock(baas: Baas_thread, task: str):
    with baas_lock:
        baas.logger.info(f"===== Running task: {task}")
        baas.solve(task)


async def execute_task(baas: Baas_thread, task: str):
    # Run the synchronous function in a separate thread with a lock to ensure
    # only one task is running at a time.
    await asyncio.to_thread(baas_solve_with_lock, baas, task)


async def regular_tasks(baas: Baas_thread):
    for task in [
        "restart",  ## 重启游戏
        "cafe_reward",  # 咖啡厅
        "lesson",  # 课程表
        "collect_reward",  # 领取奖励
        "group",  # 社团
        "mail",  # 邮件
        "common_shop",  # 一般商店
        "tactical_challenge_shop",  # 战术大赛（竞技场）商店
        "create",  # 制造
        "rewarded_task",  # 悬赏通缉
        # "activity_sweep",  # 活动扫荡
        # "clear_special_task_power",  # 特殊任务（活动报告和信用货币）
        # "scrimmage",  # 学园交流会
        "collect_reward",  # 领取奖励
    ]:
        await execute_task(baas, task)


async def arena_tasks(baas: Baas_thread):
    for i in range(5):
        await execute_task(baas, "arena")  # 战术大赛（竞技场）
        if i < 4:
            await asyncio.sleep(60)


async def main():
    main = Main(ocr_needed=["NUM", "Global", "JP"])  # 日服也必须要 Global，否则会崩溃
    config = ConfigSet(config_dir="jp_kisaki")  # 修改为自己的配置目录名
    baas = Baas_thread(config, None, None, None)
    baas.init_all_data()
    baas.ocr = main.ocr  # type: ignore

    # 竞技场每次战斗之间需要等待 1 分钟，因此使用单独任务组执行。
    # asyncio 将会在等待期间自动执行其他任务，不浪费时间。
    await asyncio.gather(regular_tasks(baas), arena_tasks(baas))


asyncio.run(main())
