from cnocr import CnOcr
import time

import log
from screen_operation import screen_operate

class ocr_character():
    def __init__(self):
        self.ocr = CnOcr(rec_model_name='densenet_lite_114-fc')

    def img_ocr(self, path1):
        img_fp = path1
        t1 = time.time()
        out = self.ocr.ocr(img_fp)
        t2 = time.time()
        log.o_p("ocr functioning time: " + str(t2-t1) + "s", 1)
        res = ""
        # print(out)
        for i in range(0, len(out)):
            if out[i]["score"] > 0.7:
                res = res + out[i]["text"]
        return res


if __name__ == "__main__":
    t1 = time.time()
    t = screen_operate()
    ocr = ocr_character()
    t2 = time.time()
    path = t.get_screen_shot_path()
    log.o_p("get screen shot time: " + str(time.time() - t2) + " s", 1)

    print(ocr.img_ocr(path))
    log.o_p("main function functioning time: " + str(time.time() - t1) + " s", 1)


