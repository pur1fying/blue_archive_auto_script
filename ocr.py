from cnocr import CnOcr
import time
import log
from screen_operation import screen_operate


class ocr_character:
    def __init__(self):
        self.ocr = CnOcr(rec_model_name='densenet_lite_114-fc')

    def img_ocr(self, img):
        t2 = time.time()
        out = self.ocr.ocr(img)
        t3 = time.time()
#        log.o_p("ocr functioning time: " + str(t3-t2) + "s", 1)
        res = ""
        # print(out)
        for i in range(0, len(out)):
            if out[i]["score"] > 0.6:
                res = res + out[i]["text"]
        return res


if __name__ == "__main__":
    t1 = time.time()
    t = screen_operate()
    ocr = ocr_character()
    t4 = time.time()
    shot_img = t.get_screen_shot_array()
 #   log.o_p("get screen shot time: " + str(time.time() - t4) + " s", 1)

    print(ocr.img_ocr(shot_img))
    log.o_p("main function functioning time: " + str(time.time() - t1) + " s", 1)

# 193 479 205 498