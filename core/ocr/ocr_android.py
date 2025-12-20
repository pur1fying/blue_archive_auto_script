import json
import numpy as np
from jnius import autoclass
from jnius import cast # type: ignore
from core.utils import is_android

from .ocr_pc import _Baas_ocr

if is_android():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Bitmap = autoclass('android.graphics.Bitmap')
    BitmapConfig = autoclass('android.graphics.Bitmap$Config')
    ByteBuffer = autoclass('java.nio.ByteBuffer')
    OcrEngine = autoclass('com.benjaminwan.ocrlibrary.OcrEngine')



class _FakeClient:
    class config:
        server_is_remote = False
    
    def start_server(self): ...
    def clear_log(self, time_distance=7): ...
    def create_shared_memory(self, name, size): ...
    def release_shared_memory(self, name): ...
    def init_url(self): ...
    def enable_thread_pool(self, count=4): ...
    def disable_thread_pool(self): ...

class _Baas_ocr_android:
    def __init__(self, logger, ocr_needed=None):
        self.logger = logger
        self.ocr_engine = None
        self.client = _FakeClient()
        self._init_engine()

    def _init_engine(self):
        activity = PythonActivity.mActivity
        context = cast('android.content.Context', activity)
        self.ocr_engine = OcrEngine(context)
        self.logger.info("Android RapidOCR initialized.")

    def recognize_int(self, baas, region, log_info="", filter_score=0.2) -> int:
        res = self.get_region_res(baas, region, log_info=log_info, filter_score=filter_score)
        import re
        numbers = re.findall(r'\d+', res)
        return int("".join(numbers)) if numbers else 0

    def get_region_pure_english(self, baas, region, log_info="", filter_score=0.2):
        return self.get_region_res(baas, region, log_info=log_info, filter_score=filter_score)

    def get_region_pure_chinese(self, baas, region, log_info="", filter_score=0.2):
        res = self.get_region_res(baas, region, log_info=log_info, filter_score=filter_score)
        return "".join([c for c in res if self.is_chinese_char(c)])

    def get_region_res(self, baas, region, language='zh-cn', log_info="", candidates="", filter_score=0.2):
        img = self.get_area_img(baas.latest_img_array, region, baas.ratio)
        return self.ocr_for_single_line(language, img, log_info=log_info, filter_score=filter_score)

    def get_region_raw_res(self, img, region, language='CN', ratio=1.0, candidates=""):
        cropped = self.get_area_img(img, region, ratio)
        return self.ocr(language, cropped)

    def ocr_for_single_line(self, language: str, origin_image, log_info="", candidates: str = "", 
                           pass_method: int = 1, local_path: str = "", shared_memory_name: str = "", 
                           _logger=None, filter_score=0.2):
        logger = _logger if _logger else self.logger
        
        # 转换图片
        bitmap = self._numpy_to_bitmap(origin_image)
        output_bitmap = Bitmap.createBitmap(bitmap.getWidth(), bitmap.getHeight(), BitmapConfig.ARGB_8888)

        # 执行 OCR (maxSideLen=0 代表不缩放)
        start_time = self._get_time()
        ocr_result = self.ocr_engine.detect(bitmap, output_bitmap, 0)
        end_time = self._get_time()

        # 解析结果
        full_text = ""
        text_blocks = ocr_result.getTextBlocks()
        if text_blocks is not None:
            size = text_blocks.size()
            for i in range(size):
                full_text += text_blocks.get(i).getText()

        # 资源释放与日志
        bitmap.recycle()
        output_bitmap.recycle()
        
        logger.info(f"OCR {log_info} : {full_text} | Time : {int((end_time - start_time) * 1000)}ms")
        return full_text

    def ocr(self, language: str, origin_image=None, candidates: str = "", pass_method: int = 1, 
            local_path: str = "", ret_options: int = 0b100, shared_memory_name: str = "", _logger=None):
        text = self.ocr_for_single_line(language, origin_image, _logger=_logger)
        return json.dumps({"text": text, "time": 0})

    def _numpy_to_bitmap(self, np_img):
        import cv2
        
        # 确保内存连续
        if not np_img.flags['C_CONTIGUOUS']:
            np_img = np.ascontiguousarray(np_img)

        # 颜色空间转换 BGR/Gray -> RGBA
        if len(np_img.shape) == 2:
            rgba = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGBA)
        elif len(np_img.shape) == 3 and np_img.shape[2] == 3:
            rgba = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGBA)
        elif len(np_img.shape) == 3 and np_img.shape[2] == 4:
            rgba = cv2.cvtColor(np_img, cv2.COLOR_BGRA2RGBA)
        else:
            rgba = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGBA)

        h, w = rgba.shape[:2]
        bitmap = Bitmap.createBitmap(w, h, BitmapConfig.ARGB_8888)
        
        # 使用 ByteBuffer 填充数据
        buffer = ByteBuffer.wrap(rgba.tobytes())
        bitmap.copyPixelsFromBuffer(buffer)
        
        return bitmap

    # 直接复用原逻辑的静态方法
    @staticmethod
    def is_chinese_char(char):
        return _Baas_ocr.is_chinese_char(char)

    @staticmethod
    def get_area_img(img, area, ratio=1.0):
        return _Baas_ocr.get_area_img(img, area, ratio)

    @staticmethod
    def _get_time():
        import time
        return time.time()

    # Android 端不需要实现的空方法
    def enable_thread_pool(self, count=4): pass
    def create_shared_memory(self, baas, size): pass
    def release_shared_memory(self, name): pass
    def init_baas_model(self, *args, **kwargs): pass
    def init_model(self, *args, **kwargs): pass
    def test_models(self, *args, **kwargs): pass
    @staticmethod
    def unique_language(ocr_needed): return []