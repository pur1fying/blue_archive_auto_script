import sys
import time
import cv2
import requests
import os
import subprocess
import datetime
import shutil
import json
from core.ipc_manager import SharedMemory
from core.exception import SharedMemoryError, OcrInternalError


class ServerConfig:
    def __init__(self):
        self.config = None
        self.config_path = os.path.join(BaasOcrClient.server_folder_path, "config", "global_setting.json")
        self.host = None
        self.port = None
        self.server_is_remote = False
        self.base_url = None
        self.__init_config()

    def __init_config(self):
        if not os.path.exists(self.config_path):
            default_config_file_path = os.path.join(BaasOcrClient.server_folder_path, "resource", "global_setting.json")
            if not os.path.exists(default_config_file_path):
                raise Exception("Didn't find default config file.")
            os.mkdir(os.path.dirname(self.config_path))
            shutil.copy(default_config_file_path, self.config_path)
        with open(self.config_path, "r") as f:
            self.config = json.load(f)
            self.host = self.config["ocr"]["server"]["host"]
            self.port = self.config["ocr"]["server"]["port"]
            self.base_url = f"http://{self.host}:{self.port}"
            # check is remote
            if self.host != "localhost" and self.host != "127.0.0.1":
                self.server_is_remote = True


class BaasOcrClient:
    server_folder_path = os.path.join(os.path.dirname(__file__), "bin")
    executable_name = "BAAS_ocr_server"
    if sys.platform == "win32":
        executable_name += ".exe"

    def __init__(self):
        self.exe_path = os.path.join(self.server_folder_path, self.executable_name)

        if not os.path.exists(self.exe_path):
            raise Exception("Didn't find ocr server executable.")
        self.config = ServerConfig()
        self.server_process = None
        self.clear_log()

    # clear log since time_distance days ago
    def clear_log(self, time_distance=7):
        log_folder_path = os.path.join(self.server_folder_path, "output")
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
        if self.server_process is not None:
            return
        # chmod +x BAAS_ocr_server
        if sys.platform == "linux":
            subprocess.run(["chmod", "+x", self.exe_path])
        self.server_process = subprocess.Popen(
            self.exe_path,
            cwd=self.server_folder_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            text=True
        )
        # wait for server start
        for _ in range(0, 30):
            try:
                requests.get(self.config.base_url)
                break
            except requests.exceptions.ConnectionError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Fail to start server.")

    def stop_server(self):
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
