import os.path
import sys
import cv2
from core.exception import OcrInternalError

use_baas_ocr = False
try:
    from cnocr import CnOcr
except ImportError:
    # Available in Windows and Linux
    if sys.platform == 'win32' or sys.platform == 'linux':
        import json
        from core.ocr.baas_ocr_client import Client
        from core.ocr.baas_ocr_client.server_installer import check_git
        use_baas_ocr = True


class Baas_ocr:
    language_convert_dict = {
        'CN': 'zh-cn',
        'Global': 'en-us',
        'JP': 'ja-jp',
        'NUM': 'en-us'
    }

    def __init__(self, logger, ocr_needed=None):
        self.logger = logger
        if use_baas_ocr:
            self.client = None
            self._init_client(ocr_needed)
            return
        self.ocrEN = None
        self.ocrCN = None
        self.ocrJP = None
        self.ocrNUM = None
        self.initialized = {
            'CN': False,
            'Global': False,
            'NUM': False,
            'JP': False
        }
        self.init(ocr_needed)

    def init(self, ocr_needed):
        try:
            self.logger.info("ocr needed: " + str(ocr_needed))
            if 'NUM' in ocr_needed:
                self.init_NUMocr()
            if 'CN' in ocr_needed:
                self.init_CNocr()
            if 'Global' in ocr_needed:
                self.init_ENocr()
            if 'JP' in ocr_needed:
                self.init_JPocr()
        except Exception as e:
            self.logger.error("OCR init error: " + str(e))
            raise e

    def init_ENocr(self):
        if self.ocrEN is None:
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
        if self.ocrJP is None:
            from core.ocr.jp_ocr import PPOCR_JP
            self.ocrJP = PPOCR_JP()
            img_JP = cv2.imread('src/test_ocr/JP.png')
            self.logger.info("Test ocrJP : " + self.ocrJP.ocr_for_single_line(img_JP)['text'])

    def recognize_number(self, img, area, category=int, ratio=1.0):
        img = self.get_area_img(img, area, ratio)
        if use_baas_ocr:
            res = self.ocr_for_single_line("en-us", "", img, "", 1)
        else:
            res = self.ocrNUM.ocr_for_single_line(img)['text']
            res = res.replace('<unused3>', '')
            res = res.replace('<unused2>', '')
        temp = ''
        for i in range(0, len(res)):
            if res[i].isdigit():
                temp += res[i]
            elif res[i] == '.' and category == float:
                temp += res[i]
        if temp == '':
            return "UNKNOWN"
        # 不提倡返回值类型不统一
        # 涉及的引用太多了 不敢改
        return category(temp)

    def recognize_int(self, baas, area, log_info="") -> int:
        img = self.get_area_img(baas.latest_img_array, area, baas.ratio)
        if use_baas_ocr:
            res = self.ocr_for_single_line(
                "en-us",
                log_info,
                img,
                "0123456789",
                baas.ocr_img_pass_method,
                "",
                baas.shared_memory_name
            )
        else:
            res = self.ocrNUM.ocr_for_single_line(img)['text']
            res = res.replace('<unused3>', '').replace('<unused2>', '')

        result = 0
        for i in range(0, len(res)):
            if res[i].isdigit():
                result = result * 10 + int(res[i])
        return result

    def get_region_pure_english(self, img, region, ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        if use_baas_ocr:
            res = self.ocr_for_single_line("en-us", "", img, "", 1)
        else:
            res = self.ocrEN.ocr_for_single_line(img)['text']
            res = res.replace('<unused3>', '')
            res = res.replace('<unused2>', '')
        temp = ''
        for i in range(0, len(res)):
            if self.is_english(res[i]):
                temp += res[i]
        return temp

    def get_region_pure_chinese(self, img, region, ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        if use_baas_ocr:
            res = self.ocr_for_single_line("zh-cn", "", img, "", 1)
        else:
            res = self.ocrCN.ocr_for_single_line(img)['text']
            res = res.replace('<unused3>', '')
            res = res.replace('<unused2>', '')
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

    def get_region_res(self, img, region, model='CN', ratio=1.0, candidates=""):
        img = self.get_area_img(img, region, ratio)
        res = ""
        if use_baas_ocr:
            language = self.language_convert(model)
            res = self.ocr_for_single_line(language, "", img, candidates, 1)
        else:
            if model == 'CN':
                res = self.ocrCN.ocr_for_single_line(img)['text']
            elif model == 'Global':
                res = self.ocrEN.ocr_for_single_line(img)['text']
            elif model == 'NUM':
                res = self.ocrNUM.ocr_for_single_line(img)['text']
            elif model == 'JP':
                res = self.ocrJP.ocr_for_single_line(img)['text']
            res = res.replace('<unused3>', '')
            res = res.replace('<unused2>', '')
        return res

    def get_region_raw_res(self, img, region, model='CN', ratio=1.0, candidates=""):
        img = self.get_area_img(img, region, ratio)
        res = ""
        if use_baas_ocr:
            language = self.language_convert(model)
            res = self.ocr(language, img, candidates, 1)
        else:
            if model == 'CN':
                res = self.ocrCN.ocr(img)
            elif model == 'Global':
                res = self.ocrEN.ocr(img)
            elif model == 'NUM':
                res = self.ocrNUM.ocr(img)
            elif model == 'JP':
                res = self.ocrJP.ocr(img)
            for i in range(0, len(res)):
                res[i]['text'] = res[i]['text'].replace('<unused3>', '')
                res[i]['text'] = res[i]['text'].replace('<unused2>', '')
        return res

    @staticmethod
    def get_area_img(img, area, ratio=1.0):
        img = img[int(area[1] * ratio):int(area[3] * ratio), int(area[0] * ratio):int(area[2] * ratio)]
        return img

    def _init_client(self, ocr_needed):
        self.kill_existing_ocr_server()
        check_git(logger=self.logger)
        self.client = Client.BaasOcrClient()
        self.client.start_server()
        self.enable_thread_pool(4)
        self.init_model(ocr_needed)
        self.test_models(ocr_needed)

    def kill_existing_ocr_server(self):
        self.logger.info("Ocr Kill Existing Server.")
        Client.BaasOcrClient.kilL_existing_server()

    def enable_thread_pool(self, count=4):
        self.logger.info("Ocr Enable Thread Pool.")
        response = self.client.enable_thread_pool(count=count)
        if response.status_code == 200:
            pass
        else:
            self.logger.error("Enable Thread Pool Error: " + response.text)
            raise OcrInternalError("Enable Thread Pool Error: " + response.text)

    def create_shared_memory(self, name, size):
        self.logger.info("Ocr Create Shared Memory [ " + name + " ]")
        self.client.create_shared_memory(name, size)

    def release_shared_memory(self, name):
        self.logger.info("Ocr Release Shared Memory [ " + name + " ]")
        self.client.release_shared_memory(name)

    def init_model(self, language: list[str], gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        self.logger.info("Ocr Init Model.")
        language = self.language_convert(language)
        self.logger.info("Language  : " + str(language))
        self.logger.info("GPU ID    : " + str(gpu_id))
        self.logger.info("Num Thread: " + str(num_thread))
        response = self.client.init_model(language, gpu_id, num_thread, EnableCpuMemoryArena)
        if response.status_code == 200:
            ret_json = json.loads(response.text)
            self.logger.info("Time Cost : " + str(ret_json["time"]) + "ms")
        else:
            self.logger.error("Init Model Error: " + response.text)
            raise OcrInternalError("Init Model Error: " + response.text)

    def test_models(self, language: list[str]):
        self.logger.info("Test Ocr.")
        language = self.language_convert(language)
        for lang in language:
            path = os.path.join(
                Client.BaasOcrClient.server_folder_path,
                "resource",
                "ocr_models",
                "test_images",
                f"{lang}.png"
            )
            self.ocr_for_single_line(lang, f"test {lang}", None, "", 2, path)

    def ocr_for_single_line(self,
                            language: str,
                            log_info="",
                            origin_image=None,
                            candidates: str = "",
                            pass_method: int = 1,
                            local_path: str = "",
                            shared_memory_name: str = ""
                            ):
        response = self.client.ocr_for_single_line(
            language,
            origin_image,
            candidates,
            pass_method,
            local_path,
            shared_memory_name
        )
        if response.status_code == 200:
            ret_json = json.loads(response.text)
            txt = ret_json['text']
            self.logger.info(f"Ocr {log_info} : {txt} | Time : {ret_json['time']}ms")
            return txt
        else:
            self.logger.error("Ocr For Single Line Error: " + response.text)
            raise OcrInternalError("Ocr For Single Line Error: " + response.text)

    def ocr(self,
            language: str,
            origin_image=None,
            candidates: str = "",
            pass_method: int = 1,
            local_path: str = "",
            ret_options: int = 0b100,
            shared_memory_name: str = ""
            ):
        response = self.client.ocr(
            language,
            origin_image,
            candidates,
            pass_method,
            local_path,
            ret_options,
            shared_memory_name
        )
        if response.status_code == 200:
            return response.text
        else:
            self.logger.error("Ocr Error: " + response.text)
            raise OcrInternalError("Ocr Error: " + response.text)

    @staticmethod
    def language_convert(origin_languages):
        """
            CN      -> zh-cn
            Global  -> en-us
            JP      -> ja-jp
            NUM     -> en-us
        """
        if type(origin_languages) is str:
            if origin_languages not in Baas_ocr.language_convert_dict:
                return origin_languages
            return Baas_ocr.language_convert_dict[origin_languages]
        elif type(origin_languages) is list:
            ret = []
            for lang in origin_languages:
                if lang not in Baas_ocr.language_convert_dict:
                    ret.append(lang)
                    continue
                temp = Baas_ocr.language_convert_dict[lang]
                if temp not in ret:
                    ret.append(temp)
            return ret
