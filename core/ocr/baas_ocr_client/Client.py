import os
import cv2
import sys
import json
import time
import shutil
import datetime
import platform
import requests
import subprocess
import ctypes
import threading
from typing import Optional

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
        self.init_url()

    def __init_config(self):
        if not os.path.exists(self.config_path):
            default_config_file_path = os.path.join(BaasOcrClient.server_folder_path, "resource", "global_setting.json")
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

def _android_ocr_branch() -> Optional[str]:
    if os.getenv("BAAS_ANDROID", "").lower() not in {"1", "true", "yes", "on"}:
        return None
    arch = platform.machine().lower()
    if arch in {"aarch64", "arm64"}:
        return "android-arm64-v8a"
    if arch in {"x86_64", "amd64"}:
        return "android-x86_64"
    return None


def _is_android_runtime() -> bool:
    return os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}


def _android_library_abi_dir() -> str:
    android_branch = _android_ocr_branch()
    if android_branch == "android-arm64-v8a":
        return "arm64-v8a"
    if android_branch == "android-x86_64":
        return "x86_64"
    raise RuntimeError("Unsupported Android OCR architecture.")


def _server_folder_path() -> str:
    base = os.path.dirname(__file__)
    android_branch = _android_ocr_branch()
    if android_branch:
        return os.path.join(base, "bin-android", android_branch)
    return os.path.join(base, "bin")


class BaasOcrClient:
    server_folder_path = _server_folder_path()
    executable_name = "BAAS_ocr_server"
    if sys.platform == "win32":
        executable_name += ".exe"

    def __init__(self):
        self._android_server_lib = None
        self._android_server_thread = None
        if _is_android_runtime():
            self.server_folder_path = self._prepare_android_runtime_folder()
            BaasOcrClient.server_folder_path = self.server_folder_path
            self.executable_name = "libBAAS_ocr_server.so"
            self.exe_path = self._android_server_library_path(self.server_folder_path)
        else:
            self.exe_path = os.path.join(self.server_folder_path, self.executable_name)
        if not os.path.exists(self.exe_path):
            raise FileNotFoundError("Didn't find ocr server executable.")
        self.config = ServerConfig()
        self.server_process = None
        self.clear_log()

    @staticmethod
    def _android_server_library_path(root: str) -> str:
        return os.path.join(root, "lib", _android_library_abi_dir(), "libBAAS_ocr_server.so")

    def _prepare_android_runtime_folder(self) -> str:
        source_root = _server_folder_path()
        source_binary = self._android_server_library_path(source_root)
        if not os.path.exists(source_binary):
            raise FileNotFoundError("Didn't find Android ocr server library.")

        internal_root = os.getenv("BAAS_ANDROID_INTERNAL_FILES_DIR", "").strip()
        if not internal_root:
            return source_root

        target_root = os.path.join(internal_root, "ocr-runtime", _android_ocr_branch() or "android")
        source_version = os.path.join(source_root, ".baas-ocr-prebuild-sha")
        target_version = os.path.join(target_root, ".baas-ocr-prebuild-sha")
        try:
            source_sha = open(source_version, "r", encoding="utf-8").read().strip()
        except OSError:
            source_sha = ""
        try:
            target_sha = open(target_version, "r", encoding="utf-8").read().strip()
        except OSError:
            target_sha = ""

        target_binary = self._android_server_library_path(target_root)
        if source_sha and source_sha == target_sha and os.path.exists(target_binary):
            return target_root

        if os.path.exists(target_root):
            shutil.rmtree(target_root, ignore_errors=True)
        shutil.copytree(source_root, target_root)
        native_lib_dir = os.getenv("BAAS_ANDROID_NATIVE_LIBRARY_DIR", "").strip()
        native_libcxx = os.path.join(native_lib_dir, "libc++_shared.so") if native_lib_dir else ""
        target_libcxx = os.path.join(target_root, "lib", _android_library_abi_dir(), "libc++_shared.so")
        if native_libcxx and os.path.exists(native_libcxx):
            shutil.copy2(native_libcxx, target_libcxx)
        os.chmod(self._android_server_library_path(target_root), 0o755)
        return target_root

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
        if _is_android_runtime():
            self._start_android_server()
            return
        # chmod +x BAAS_ocr_server
        if sys.platform == "linux":
            subprocess.run(["chmod", "+x", self.exe_path])
        try:
            self.server_process = subprocess.Popen(
                self.exe_path,
                cwd=self.server_folder_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                text=True
            )
        except Exception:
            self.server_process = subprocess.Popen(
                [self.exe_path],
                cwd=self.server_folder_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                text=True
            )
        # wait for server start
        for _ in range(0, 30):
            try:
                ret = requests.get(self.config.base_url)
                if ret.status_code == 200:
                    break
            except requests.exceptions.ConnectionError as e:
                if _ == 29:
                    raise RuntimeError("Fail to start ocr server. " + e.__str__())
                time.sleep(0.1)

    def _start_android_server(self):
        lib_dir = os.path.dirname(self.exe_path)
        native_lib_dir = os.getenv("BAAS_ANDROID_NATIVE_LIBRARY_DIR", "").strip()
        dependency_paths = []
        if native_lib_dir:
            dependency_paths.append(os.path.join(native_lib_dir, "libc++_shared.so"))
        elif os.path.exists(os.path.join(lib_dir, "libc++_shared.so")):
            dependency_paths.append(os.path.join(lib_dir, "libc++_shared.so"))
        dependency_paths.extend(os.path.join(lib_dir, name) for name in ["libonnxruntime.so", "libopencv_java4.so"])
        loaded = set()
        for path in dependency_paths:
            if path in loaded:
                continue
            if os.path.exists(path):
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                loaded.add(path)
        server_lib = ctypes.CDLL(self.exe_path, mode=ctypes.RTLD_GLOBAL)
        server_lib.start_server.argtypes = []
        server_lib.start_server.restype = None
        server_lib.stop_server.argtypes = []
        server_lib.stop_server.restype = None
        self._android_server_lib = server_lib
        self._android_server_thread = threading.Thread(
            target=server_lib.start_server,
            name="baas-ocr-android-server",
            daemon=True,
        )
        self._android_server_thread.start()
        self.server_process = self._android_server_thread
        for _ in range(0, 100):
            try:
                ret = requests.get(self.config.base_url, timeout=1)
                if ret.status_code == 200:
                    break
            except requests.exceptions.RequestException as e:
                if _ == 99:
                    raise RuntimeError("Fail to start ocr server. " + e.__str__())
                time.sleep(0.1)

    def stop_server(self):
        if _is_android_runtime():
            if self._android_server_lib is not None:
                self._android_server_lib.stop_server()
            if self._android_server_thread is not None:
                self._android_server_thread.join(timeout=10)
            self.server_process = None
            self._android_server_thread = None
            self._android_server_lib = None
            return
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
