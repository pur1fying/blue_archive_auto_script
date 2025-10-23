import json
import socket
import os.path

from core.exception import OcrInternalError
from core.ocr.baas_ocr_client import Client
from core.utils import is_android


class _Baas_ocr:

    def __init__(self, logger, ocr_needed=None):
        self.logger = logger
        self.client = None
        self._init_client(ocr_needed)

    def recognize_int(self, baas, region, log_info="", filter_score=0.2) -> int:
        res = self.get_region_res(
            baas=baas,
            region=region,
            language="en-us",
            log_info=log_info,
            candidates="0123456789",
            filter_score=filter_score
        )
        result = 0
        for i in range(0, len(res)):
            if res[i].isdigit():
                result = result * 10 + int(res[i])
        return result

    def get_region_pure_english(self, baas, region, log_info="", filter_score=0.2):
        res = self.get_region_res(
            baas=baas,
            region=region,
            language="en-us",
            log_info=log_info,
            candidates="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            filter_score=filter_score
        )
        return res

    def get_region_pure_chinese(self, baas, region, log_info="", filter_score=0.2):
        res = self.get_region_res(
            baas=baas,
            region=region,
            language="zh-cn",
            log_info=log_info,
            candidates="",
            filter_score=filter_score
        )
        temp = ""
        for i in range(0, len(res)):
            if self.is_chinese_char(res[i]):
                temp += res[i]
        return temp

    def get_region_res(self, baas, region, language='zh-cn', log_info="", candidates="", filter_score=0.2):
        img = self.get_area_img(baas.latest_img_array, region, baas.ratio)
        res = self.ocr_for_single_line(
            language=language,
            log_info=log_info,
            origin_image=img,
            candidates=candidates,
            pass_method=baas.ocr_img_pass_method,
            local_path="",
            shared_memory_name=baas.shared_memory_name,
            _logger=baas.logger,
            filter_score=filter_score
        )
        return res

    def get_region_raw_res(self, img, region, language='CN', ratio=1.0, candidates=""):
        img = self.get_area_img(img, region, ratio)
        res = self.ocr(language, img, candidates, 1)
        return res

    @staticmethod
    def is_chinese_char(char):
        return 0x4e00 <= ord(char) <= 0x9fff

    @staticmethod
    def get_area_img(img, area, ratio=1.0):
        img = img[int(area[1] * ratio):int(area[3] * ratio), int(area[0] * ratio):int(area[2] * ratio)]
        return img

    @staticmethod
    def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False

    def _init_client(self, ocr_needed):
        ocr_needed = self.unique_language(ocr_needed)
        self.client = Client.BaasOcrClient()
        self._detect_usable_port()
        self.client.start_server()
        self.enable_thread_pool(4)
        self.init_model(ocr_needed)
        self.test_models(ocr_needed)

    def _detect_usable_port(self):
        port = self.client.config.port
        if self.is_port_free(port):
            return
        self.logger.warning(f"Ocr Port {port} is occupied, try to find usable port.")
        base = 1145
        for i in range(1000):
            _p = base + i
            if self.is_port_free(_p):
                self.logger.info(f"Port: {_p}")
                self._set_port(_p)
                return

            _p = base - i
            if self.is_port_free(_p):
                self.logger.info(f"Port: {_p}")
                self._set_port(_p)
                return
        raise OcrInternalError("Cannot find a free port.")

    def _set_port(self, p):
        self.client.config.config["ocr"]["server"]["port"] = p
        self.client.config.save()
        self.client.config.init_url()

    def enable_thread_pool(self, count=4):
        self.logger.info("Ocr Enable Thread Pool.")
        response = self.client.enable_thread_pool(count=count)
        if response.status_code == 200:
            pass
        else:
            self.logger.error("Enable Thread Pool Error: " + response.text)
            raise OcrInternalError("Enable Thread Pool Error: " + response.text)

    def create_shared_memory(self, baas, size):
        baas.logger.info("Ocr Create Shared Memory [ " + baas.shared_memory_name + " ]")
        self.client.create_shared_memory(baas.shared_memory_name, size)

    def release_shared_memory(self, name):
        self.logger.info("Ocr Release Shared Memory [ " + name + " ]")
        self.client.release_shared_memory(name)

    def init_baas_model(self, baas, gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        logger = baas.logger
        logger.info("Ocr Init Model.")
        logger.info("Language  : " + str(baas.ocr_language))
        logger.info("GPU ID    : " + str(gpu_id))
        logger.info("Num Thread: " + str(num_thread))
        logger.info("EnableCpuMemoryArena: " + str(EnableCpuMemoryArena))
        response = self.client.init_model([baas.ocr_language], gpu_id, num_thread, EnableCpuMemoryArena)
        if response.status_code == 200:
            ret_json = json.loads(response.text)
            logger.info("Time Cost : " + str(ret_json["time"]) + "ms")
        else:
            self.logger.error("Init Model Error: " + response.text)
            raise OcrInternalError("Init Model Error: " + response.text)

    def init_model(self, language: list[str], gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        self.logger.info("Ocr Init Model.")
        self.logger.info("Language  : " + str(language))
        self.logger.info("GPU ID    : " + str(gpu_id))
        self.logger.info("Num Thread: " + str(num_thread))
        self.logger.info("EnableCpuMemoryArena: " + str(EnableCpuMemoryArena))
        response = self.client.init_model(language, gpu_id, num_thread, EnableCpuMemoryArena)
        if response.status_code == 200:
            ret_json = json.loads(response.text)
            self.logger.info("Time Cost : " + str(ret_json["time"]) + "ms")
        else:
            self.logger.error("Init Model Error: " + response.text)
            raise OcrInternalError("Init Model Error: " + response.text)

    def test_models(self, language: list[str], _logger=None):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger
        logger.info("Test Ocr.")
        for lang in language:
            path = os.path.join(
                Client.BaasOcrClient.server_folder_path,
                "resource",
                "ocr_models",
                "test_images",
                f"{lang}.png"
            )
            self.ocr_for_single_line(lang, f"test {lang}", None, "", 2, path, logger)

    def ocr_for_single_line(self,
                            language: str,
                            log_info="",
                            origin_image=None,
                            candidates: str = "",
                            pass_method: int = 1,
                            local_path: str = "",
                            shared_memory_name: str = "",
                            _logger=None,
                            filter_score=0.2
                            ):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger

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
            char_scores = ret_json['char_scores']
            txt = ''.join([char for i, char in enumerate(txt) if char_scores[i] > filter_score])
            logger.info(f"Ocr {log_info} : {txt} | Time : {ret_json['time']}ms")
            return txt
        else:
            logger.error("Ocr For Single Line Error: " + response.text)
            raise OcrInternalError("Ocr For Single Line Error: " + response.text)

    def ocr(self,
            language: str,
            origin_image=None,
            candidates: str = "",
            pass_method: int = 1,
            local_path: str = "",
            ret_options: int = 0b100,
            shared_memory_name: str = "",
            _logger=None
            ):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger
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
            logger.error("Ocr Error: " + response.text)
            raise OcrInternalError("Ocr Error: " + response.text)

    @staticmethod
    def unique_language(ocr_needed):
        ret = []
        for lang in ocr_needed:
            if lang not in ret:
                ret.append(lang)
        return ret

# mock for android
class _Baas_ocr_mock_client:
    def __init__(self):
        # Mock config
        class MockConfig:
            def __init__(self):
                self.port = 1145
                self.config = {"ocr": {"server": {"port": self.port}}}

            def save(self):
                pass

            def init_url(self):
                pass

        self.config = MockConfig()

    def start_server(self):
        pass

    def enable_thread_pool(self, count=4):
        # Mock response
        class MockResponse:
            status_code = 200
            text = ""

        return MockResponse()

    def create_shared_memory(self, name, size):
        pass

    def release_shared_memory(self, name):
        pass

    def init_model(self, language: list[str], gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        class MockResponse:
            status_code = 200
            text = '{"time": 0}'

        return MockResponse()

    def ocr_for_single_line(self, language: str, origin_image=None, candidates: str = "", pass_method: int = 1,
                            local_path: str = "", shared_memory_name: str = ""):
        class MockResponse:
            status_code = 200
            text = '{"text": "mock_text", "char_scores": [1.0] * len("mock_text"), "time": 0}'

        return MockResponse()

    def ocr(self, language: str, origin_image=None, candidates: str = "", pass_method: int = 1, local_path: str = "",
            ret_options: int = 0b100, shared_memory_name: str = ""):
        class MockResponse:
            status_code = 200
            text = '{"text": "mock_text", "time": 0}'

        return MockResponse()


class _Baas_ocr_mock_android:
    def __init__(self, logger, ocr_needed=None):
        self.logger = logger
        self.client = None
        self._init_client(ocr_needed)

    def _init_client(self, ocr_needed):
        self.client = _Baas_ocr_mock_client()

    def recognize_int(self, baas, region, log_info="", filter_score=0.2) -> int:
        self.logger.info(f"Mock recognize_int for {log_info}")
        return 12345

    def get_region_pure_english(self, baas, region, log_info="", filter_score=0.2):
        self.logger.info(f"Mock get_region_pure_english for {log_info}")
        return "mockEnglish"

    def get_region_pure_chinese(self, baas, region, log_info="", filter_score=0.2):
        self.logger.info(f"Mock get_region_pure_chinese for {log_info}")
        return "mock中文"

    def get_region_res(self, baas, region, language='zh-cn', log_info="", candidates="", filter_score=0.2):
        self.logger.info(f"Mock get_region_res for {log_info}")
        return "mock_text"

    def get_region_raw_res(self, img, region, language='CN', ratio=1.0, candidates=""):
        self.logger.info(f"Mock get_region_raw_res")
        return '{"text": "mock_text", "time": 0}'

    @staticmethod
    def is_chinese_char(char):
        return 0x4e00 <= ord(char) <= 0x9fff

    @staticmethod
    def get_area_img(img, area, ratio=1.0):
        img = img[int(area[1] * ratio):int(area[3] * ratio), int(area[0] * ratio):int(area[2] * ratio)]
        return img

    def enable_thread_pool(self, count=4):
        self.logger.info("Mock Ocr Enable Thread Pool.")

    def create_shared_memory(self, baas, size):
        baas.logger.info("Mock Ocr Create Shared Memory [ " + baas.shared_memory_name + " ]")

    def release_shared_memory(self, name):
        self.logger.info("Mock Ocr Release Shared Memory [ " + name + " ]")

    def init_baas_model(self, baas, gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        logger = baas.logger
        logger.info("Mock Ocr Init Model.")

    def init_model(self, language: list[str], gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        self.logger.info("Mock Ocr Init Model.")

    def test_models(self, language: list[str], _logger=None):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger
        logger.info("Mock Test Ocr.")

    def ocr_for_single_line(self,
                            language: str,
                            log_info="",
                            origin_image=None,
                            candidates: str = "",
                            pass_method: int = 1,
                            local_path: str = "",
                            shared_memory_name: str = "",
                            _logger=None,
                            filter_score=0.2
                            ):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger
        logger.info(f"Mock Ocr {log_info} : mock_text | Time : 0ms")
        return "mock_text"

    def ocr(self,
            language: str,
            origin_image=None,
            candidates: str = "",
            pass_method: int = 1,
            local_path: str = "",
            ret_options: int = 0b100,
            shared_memory_name: str = "",
            _logger=None
            ):
        if _logger is None:
            logger = self.logger
        else:
            logger = _logger
        return '{"text": "mock_text", "time": 0}'

    @staticmethod
    def unique_language(ocr_needed):
        ret = []
        if ocr_needed is None:
            return ret
        for lang in ocr_needed:
            if lang not in ret:
                ret.append(lang)
        return ret

if is_android():
    Baas_ocr = _Baas_ocr_mock_android
else:
    Baas_ocr = _Baas_ocr