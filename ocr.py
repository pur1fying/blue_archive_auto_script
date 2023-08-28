from cnocr import CnOcr
from screen_operation import screen_operate


class ocr_character(screen_operate):
    def img_ocr(self, path1):
        img_fp = path1
        ocr = CnOcr()
        out = ocr.ocr(img_fp)
        res = ""
        print(out)
        for i in range(0, len(out)):
            res = res + out[i]["text"]
        return res

