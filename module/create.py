import time
from core import color, image
from core.utils import kmp, img_crop
from gui.util import log

def implement(self):
    pass
def common_create_judge(self):
    pri = ["花", "Mo", "桃桃", "万圣节", "情人节", "果冻", "色彩", "灿烂", "光芒", "玲珑", "白金", "黄金", "铜", "白银",
           "金属", "隐然"]  # 可设置参数，越靠前的节点在制造时越优先选择
    node_x = [839, 508, 416, 302, 174]
    node_y = [277, 388, 471, 529, 555]
    # 572 278
    node = []
    lo = []
    for i in range(0, 5):
        self.operation("click", (node_x[i], node_y[i]))
        time.sleep(0.5 if i == 0 else 0.1)
        node_info = self.img_ocr(img_crop(self.operation("get_screenshot_array"), 734, 1123, 207, 277))
        for k in range(0, len(pri)):
            if kmp(pri[k], node_info) > 0:
                if k == 0:
                    log.d("choose node :" + pri[0], level=1, logger_box=self.loggerBox)
                    return i
                else:
                    node.append(pri[k])
                    lo.append(i)
    log.d("detected nodes:" + str(node), 1, logger_box=self.loggerBox)
    for i in range(1, len(pri)):
        for j in range(0, len(node)):
            if node[j][0:len(pri[i])] == pri[i]:
                log.d("choose node :" + pri[i], level=1, logger_box=self.loggerBox)
                return lo[j]


