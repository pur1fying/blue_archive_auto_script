from module.explore_normal_task import get_explore_normal_task_missions
from module.explore_hard_task import get_explore_hard_task_data
from core.utils import Logger
from core.Baas_thread import Baas_thread
from gui.util.config_set import ConfigSet
from main import Main

t = Main(ocr_needed=[])
config = ConfigSet(config_dir="D:\\github\\bass\\blue_archive_auto_script\\config\\1708148000")
tt = Baas_thread(config, None, None, None)
tt.init_all_data()

st = [
    1,
    4,
    26,
    99,
    "6,7",
    "1，2，3",
    "18,19,20",
    "18，19，20",
    [18, 19, 20],
    "5,19,21",
    [4, 23, -1],
    "5,16,q9,",
    [5, 16, "q9"]
]
expected_1 = [
    [],
    [[4, 1], [4, 2], [4, 3], [4, 4], [4, 5]],
    [[26, 1], [26, 2], [26, 3], [26, 4], [26, 5]],
    [],
    [[6, 1], [6, 2], [6, 3], [6, 4], [6, 5], [7, 1], [7, 2], [7, 3], [7, 4], [7, 5]],
    [],
    [[18, 1], [18, 2], [18, 3], [18, 4], [18, 5], [19, 1], [19, 2], [19, 3], [19, 4], [19, 5], [20, 1], [20, 2], [20, 3], [20, 4], [20, 5]],
    [[18, 1], [18, 2], [18, 3], [18, 4], [18, 5], [19, 1], [19, 2], [19, 3], [19, 4], [19, 5], [20, 1], [20, 2], [20, 3], [20, 4], [20, 5]],
    [[18, 1], [18, 2], [18, 3], [18, 4], [18, 5], [19, 1], [19, 2], [19, 3], [19, 4], [19, 5], [20, 1], [20, 2], [20, 3], [20, 4], [20, 5]],
    [[5, 1], [5, 2], [5, 3], [5, 4], [5, 5], [19, 1], [19, 2], [19, 3], [19, 4], [19, 5], [21, 1], [21, 2], [21, 3], [21, 4], [21, 5]],
    [[4, 1], [4, 2], [4, 3], [4, 4], [4, 5], [23, 1], [23, 2], [23, 3], [23, 4], [23, 5]],
    [[5, 1], [5, 2], [5, 3], [5, 4], [5, 5], [16, 1], [16, 2], [16, 3], [16, 4], [16, 5]],
    [[5, 1], [5, 2], [5, 3], [5, 4], [5, 5], [16, 1], [16, 2], [16, 3], [16, 4], [16, 5]]
]

for i in range(len(st)):
    ret = get_explore_normal_task_missions(tt, st[i], True)
    print(ret)
    assert ret == expected_1[i]
