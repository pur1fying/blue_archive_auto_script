from cnocr import CnOcr


def img_ocr(path1):
    img_fp = path1
    ocr = CnOcr()
    out = ocr.ocr(img_fp)
    res = ""
    # print(out)
    for i in range(0, len(out)):
        if out[i]["score"] > 0.5:
            res = res + out[i]["text"]
    return res
