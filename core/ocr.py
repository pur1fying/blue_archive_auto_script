import time

import cv2
from cnocr import CnOcr


class Baas_ocr:
    def __init__(self, logger, ocr_needed):
        self.logger = logger
        self.ocrEN = None
        self.ocrCN = None
        self.ocrJP = None
        self.ocrNUM = None
        try:
            if 'CN' in ocr_needed:
                self.init_CNocr()
            if 'Global' in ocr_needed:
                self.init_ENocr()
            if 'JP' in ocr_needed:
                self.init_JPocr()
            if 'NUM' in ocr_needed:
                self.init_NUMocr()
        except Exception as e:
            self.logger.error("OCR init error: " + str(e))
            raise e

    def init_ENocr(self):
        self.ocrEN = CnOcr(det_model_name="en_PP-OCRv3_det",
                           det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                           rec_model_name='en_number_mobile_v2.0',
                           rec_model_fp='src/ocr_models/en_number_mobile_v2.0_rec_infer.onnx', )
        img_EN = cv2.imread('src/test_ocr/EN.png')
        self.logger.info("Test ocrEN : " + self.ocrEN.ocr_for_single_line(img_EN)['text'])
        return True

    def init_CNocr(self):
        if self.ocrCN is None:
            self.ocrCN = CnOcr(det_model_name='ch_PP-OCRv3_det',
                               det_model_fp='src/ocr_models/ch_PP-OCRv3_det_infer.onnx',
                               rec_model_name='densenet_lite_114-fc',
                               rec_model_fp='src/ocr_models/cn_densenet_lite_136.onnx')
            img_CN = cv2.imread('src/test_ocr/CN.png')
            self.logger.info("Test ocrCN : " + self.ocrCN.ocr_for_single_line(img_CN)['text'])
        return True

    def init_NUMocr(self):
        if self.ocrNUM is None:
            self.ocrNUM = CnOcr(det_model_name='en_PP-OCRv3_det',
                                det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                                rec_model_name='number-densenet_lite_136-fc',
                                rec_model_fp='src/ocr_models/number-densenet_lite_136.onnx')

            img_NUM = cv2.imread('src/test_ocr/NUM.png')
            self.logger.info("Test ocrNUM : " + self.ocrNUM.ocr_for_single_line(img_NUM)['text'])
        return True

    def init_JPocr(self):
        pass

    def get_region_num(self, img, region, category=int):
        img = img[region[1]:region[3], region[0]:region[2]]
        t1 = time.time()
        res = self.ocrNUM.ocr_for_single_line(img)['text']
        ocr_time = round(time.time() - t1, 3)
        res.replace('<unused3>', '')
        res.replace('<unused2>', '')
        self.logger.info("ocr res : " + res + " time: " + str(ocr_time))
        temp = ''
        for i in range(0, len(res)):
            if res[i].isdigit():
                temp += res[i]
            elif res[i] == '.' and category == float:
                temp += res[i]

        if temp == '':
            return "UNKNOWN"
        return category(temp)

    def get_region_pure_english(self, img, region):
        img = img[region[1]:region[3], region[0]:region[2]]
        t1 = time.time()
        res = self.ocrEN.ocr_for_single_line(img)['text']
        ocr_time = round(time.time() - t1, 3)
        res.replace('<unused3>', '')
        res.replace('<unused2>', '')
        self.logger.info("ocr res : " + res + " time: " + str(ocr_time))
        temp = ''
        for i in range(0, len(res)):
            if self.is_english(res[i]):
                temp += res[i]
        return temp

    def get_region_pure_chinese(self, img, region):
        img = img[region[1]:region[3], region[0]:region[2]]
        t1 = time.time()
        res = self.ocrCN.ocr_for_single_line(img)['text']
        ocr_time = round(time.time() - t1, 3)
        res.replace('<unused3>', '')
        res.replace('<unused2>', '')
        self.logger.info("ocr res : " + res + " time: " + str(ocr_time))
        temp = ''
        for i in range(0, len(res)):
            if self.is_chinese_char(res[i]):
                temp += res[i]
        return temp

    def is_upper_english(self, char):
        if 'A' <= char <= 'Z':
            return True
        return False

    def is_lower_english(self, char):
        if 'a' <= char <= 'z':
            return True
        return False

    def is_english(self, char):
        return self.is_upper_english(char) or self.is_lower_english(char)

    def is_chinese_char(self, char):
        return 0x4e00 <= ord(char) <= 0x9fff

    def get_region_res(self, img, region, model='CN'):
        img = img[region[1]:region[3], region[0]:region[2]]
        t1 = time.time()
        res = ""
        if model == 'CN':
            res = self.ocrCN.ocr_for_single_line(img)['text']
        elif model == 'Global':
            res = self.ocrEN.ocr_for_single_line(img)['text']
        elif model == 'NUM':
            res = self.ocrNUM.ocr_for_single_line(img)['text']
        ocr_time = round(time.time() - t1, 3)
        res.replace('<unused3>', '')
        res.replace('<unused2>', '')
        self.logger.info("ocr res : " + res + " time: " + str(ocr_time))
        return res

    def get_region_raw_res(self, img, region, model='CN'):
        img = img[region[1]:region[3], region[0]:region[2]]
        t1 = time.time()
        res = ""
        if model == 'CN':
            res = self.ocrCN.ocr(img)
        elif model == 'Global':
            res = self.ocrEN.ocr(img)
        elif model == 'NUM':
            res = self.ocrNUM.ocr(img)
        ocr_time = round(time.time() - t1, 3)
        for i in range(0, len(res)):
            res[i]['text'] = res[i]['text'].replace('<unused3>', '')
            res[i]['text'] = res[i]['text'].replace('<unused2>', '')
        return res
