import os
import cv2
import sys
import json
import time
import shutil
import datetime
import requests
import subprocess

from core.ipc_manager import SharedMemory
from core.exception import SharedMemoryError, OcrInternalError
from core.ocr.baas_ocr_client.server_installer import SERVER_BIN_DIR, arch
from core.utils import host_platform_is_android


class ServerConfig:
    def __init__(self):
        self.config = None
        self.config_path = os.path.join(SERVER_BIN_DIR, "config", "global_setting.json")
        self.host = None
        self.port = None
        self.server_is_remote = False
        self.base_url = None
        self.__init_config()
        self.init_url()

    def __init_config(self):
        if not os.path.exists(self.config_path):
            default_config_file_path = os.path.join(SERVER_BIN_DIR, "resource", "global_setting.json")
            if not os.path.exists(default_config_file_path):
                raise FileNotFoundError("Didn't find default config file.")
            os.mkdir(os.path.dirname(self.config_path))
            shutil.copy(default_config_file_path, self.config_path)
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

    def init_url(self):
        self.host = self.config["ocr"]["server"]["host"]
        self.port = self.config["ocr"]["server"]["port"]
        self.base_url = f"http://{self.host}:{self.port}"
        # check is remote
        if self.host != "localhost" and self.host != "127.0.0.1":
            self.server_is_remote = True

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)

class BaasOcrClient:
    def __init__(self):
        # android start from dll
        if host_platform_is_android():
            import ctypes
            self.dll_path = os.path.join(SERVER_BIN_DIR, "lib", arch)
            if not os.path.exists(self.dll_path):
                raise FileNotFoundError("Didn't find ocr server library dir. Expected at " + self.dll_path)
            self.lib_cpp_shared = ctypes.CDLL(os.path.join(self.dll_path, "libc++_shared.so"), mode=ctypes.RTLD_GLOBAL)
            self.lib_onnx = ctypes.CDLL(os.path.join(self.dll_path, "libonnxruntime.so"))
            self.lib_opencv = ctypes.CDLL(os.path.join(self.dll_path, "libopencv_java4.so"))
            self.lib_baas_ocr_server = ctypes.CDLL(os.path.join(self.dll_path, "libBAAS_ocr_server.so"))

        # win / linux / mac start as executable
        else:
            executable_name = "BAAS_ocr_server"
            if sys.platform == "win32":
                executable_name += ".exe"
            self.exe_path = os.path.join(SERVER_BIN_DIR, executable_name)
            if not os.path.exists(self.exe_path):
                raise FileNotFoundError("Didn't find ocr server executable. Expected at " + self.exe_path)
        self.config = ServerConfig()
        self.server_process = None
        self.clear_log()

    # clear log since time_distance days ago
    @staticmethod
    def clear_log(time_distance=7):
        log_folder_path = os.path.join(SERVER_BIN_DIR, "output")
        if not os.path.exists(log_folder_path):
            return
        for name in os.listdir(log_folder_path):
            path = os.path.join(log_folder_path, name)
            if os.path.isdir(path):
                # name is yyyy-mm-dd_hh.mm.ss
                name = name.split("_")[0]
                year, month, day = map(int, name.split("-"))
                time_dis = (datetime.datetime.now() - datetime.datetime(year, month, day)).days
                if time_dis >= time_distance:
                    shutil.rmtree(path)

    def create_shared_memory(self, name, size):
        url = self.config.base_url + "/create_shared_memory"
        pass_name = "/" + name if sys.platform != "win32" else name
        data = {
            "shared_memory_name": pass_name,
            "size": size
        }
        ret = requests.post(url, json=data)
        if ret.status_code == 200:
            SharedMemory.get(name)
        return ret

    def release_shared_memory(self, name):
        url = self.config.base_url + "/release_shared_memory"
        pass_name = "/" + name if sys.platform != "win32" else name
        data = {
            "name": pass_name
        }
        SharedMemory.release(name)
        return requests.post(url, json=data)

    def enable_thread_pool(self, count=4):
        url = self.config.base_url + "/enable_thread_pool"
        data = {
            "thread_count": count
        }
        return requests.post(url, json=data)

    def disable_thread_pool(self):
        url = self.config.base_url + "/disable_thread_pool"
        return requests.post(url)

    def start_server(self):
        if host_platform_is_android():
            self.start_server_android()
        else:
            self.start_server_normal()
        # wait for server start
        for _ in range(0, 30):
            try:
                requests.get(self.config.base_url)
                break
            except requests.exceptions.ConnectionError as e:
                if _ == 29:
                    raise RuntimeError("Fail to start ocr server. " + e.__str__())
                time.sleep(0.1)

    def start_server_android(self):
        self.lib_baas_ocr_server.start_server(SERVER_BIN_DIR.encode("utf-8"))

    def start_server_normal(self):
        if self.server_process is not None:
            return
        # chmod +x BAAS_ocr_server
        if sys.platform == "linux":
            subprocess.run(["chmod", "+x", self.exe_path])
        try:
            self.server_process = subprocess.Popen(
                self.exe_path,
                cwd=SERVER_BIN_DIR,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                text=True
            )
        except Exception:
            self.server_process = subprocess.Popen(
                [self.exe_path],
                cwd=SERVER_BIN_DIR,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                text=True
            )

    def stop_server(self):
        if host_platform_is_android():
            self.stop_server_android()
        else:
            self.stop_server_normal()

    def stop_server_android(self):
        self.lib_baas_ocr_server.stop_server()

    def stop_server_normal(self):
        self.server_process.stdin.write("exit\n")
        self.server_process.stdin.flush()
        return_code = self.server_process.wait(10)
        if return_code != 0:
            raise RuntimeError("Fail to stop server.")
        self.server_process.stdin.close()
        self.server_process = None

    def init_model(self, language: list[str], gpu_id=-1, num_thread=4, EnableCpuMemoryArena=False):
        url = self.config.base_url + "/init_model"
        data = {
            "language": language,
            "gpu_id": gpu_id,
            "num_thread": num_thread,
            "EnableCpuMemoryArena": EnableCpuMemoryArena
        }
        return requests.post(url, json=data)

    def release_model(self, language: list[str]):
        url = self.config.base_url + "/release_model"
        data = {
            "language": language
        }
        return requests.post(url, json=data)

    def release_all(self):
        url = self.config.base_url + "/release_all"
        return requests.get(url)

    def ocr(self,
            language: str,
            origin_image=None,
            candidates: str = "",
            pass_method: int = 0,
            local_path: str = "",
            ret_options: int = 0b100,
            shared_memory_name: str = ""
            ):
        url = self.config.base_url + "/ocr"
        data = {
            "language": language,
            "candidates": candidates,
            "image": {
                "pass_method": pass_method,
            },
            "ret_options": ret_options
        }
        self.get_request_data(data, pass_method, origin_image, local_path, shared_memory_name)
        if pass_method in [0, 2]:
            return requests.post(url, json=data)
        elif pass_method == 1:
            image_bytes = self.get_image_bytes(origin_image)
            files = {
                "data": (None, json.dumps(data), "application/json"),
                "image": ("image.png", image_bytes, "image/png")
            }
            return requests.post(url, files=files)

    def get_text_boxes(
            self,
            language: str,
            origin_image=None,
            pass_method: int = 0,
            local_path: str = "",
            shared_memory_name: str = ""
    ):
        url = self.config.base_url + "/get_text_boxes"
        data = {
            "language": language,
            "image": {
                "pass_method": pass_method,
            },
        }
        self.get_request_data(data, pass_method, origin_image, local_path, shared_memory_name)
        if pass_method in [0, 2]:
            return requests.post(url, json=data)
        elif pass_method == 1:
            image_bytes = self.get_image_bytes(origin_image)
            files = {
                "data": (None, json.dumps(data), "application/json"),
                "image": ("image.png", image_bytes, "image/png")
            }
            return requests.post(url, files=files)

    @staticmethod
    def get_request_data(
            data,
            pass_method,
            origin_image=None,
            local_path: str = "",
            shared_memory_name: str = ""
    ):
        if pass_method == 0:
            col = origin_image.shape[1]
            row = origin_image.shape[0]
            size = col * row * 3
            SharedMemory.set_data(shared_memory_name, origin_image.tobytes(), size)
            data["image"]["shared_memory_name"] = "/" + shared_memory_name if sys.platform != "win32" \
                else shared_memory_name
            data["image"]["resolution"] = [col, row]
        elif pass_method == 1:
            pass
        elif pass_method == 2:
            data["image"]["local_path"] = local_path
        else:
            raise OcrInternalError(f"Invalid pass_method {pass_method}")

    def ocr_for_single_line(self,
                            language: str,
                            origin_image=None,
                            candidates: str = "",
                            pass_method: int = 0,
                            local_path: str = "",
                            shared_memory_name: str = ""
                            ):
        url = self.config.base_url + "/ocr_for_single_line"
        data = {
            "language": language,
            "candidates": candidates,
            "image": {
                "pass_method": pass_method,
            },
        }
        self.get_request_data(data, pass_method, origin_image, local_path, shared_memory_name)
        if pass_method in [0, 2]:
            return requests.post(url, json=data)
        elif pass_method == 1:
            image_bytes = self.get_image_bytes(origin_image)
            files = {
                "data": (None, json.dumps(data), "application/json"),
                "image": ("image.png", image_bytes, "image/png")
            }
            return requests.post(url, files=files)

    @staticmethod
    def get_image_bytes(image):
        _, encoded_image = cv2.imencode('.png', image)
        return encoded_image.tobytes()

    def get_text_box(self):
        pass


if __name__ == "__main__":
    client = BaasOcrClient()
    client.start_server()
    # time.sleep(500)

    client.init_model(["zh-cn"])
    time.sleep(5)
