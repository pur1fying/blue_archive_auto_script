import json
import time

import requests

from deploy.installer.mirrorc_update.utils import detect_system_info
from const import CdkState, MirrorCErrorCode, UpdateType


class RequestReturn:
    def __init__(self, response_json):
        self.code = response_json["code"]
        self.message = response_json["msg"]
        # server internal error
        if self.code < MirrorCErrorCode.SUCCESS.value:
            return


        if self.code not in [
            MirrorCErrorCode.SUCCESS.value,
            MirrorCErrorCode.KEY_INVALID.value,
            MirrorCErrorCode.KEY_EXPIRED.value,
            MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value,
            MirrorCErrorCode.KEY_MISMATCHED.value,
            MirrorCErrorCode.KEY_BLOCKED.value
        ]:
            return

        self.data = response_json["data"]

        self.has_url = "url" in self.data
        self.release_note = self.data.get("release_note")
        self.latest_version_name = self.data.get("version_name")
        if self.has_url:
            self.sha256 = self.data.get("sha256")
            self.download_url = self.data.get("url")
            self.update_type = UpdateType.FULL if self.data.get("update_type") == "full" else UpdateType.INCREMENTAL
            self.file_size = self.data.get("file_size")
            self.cdk_expired_time = self.data.get("cdk_expired_time")

class ServerInternalError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MirrorC_Updater:

    basic_url = "https://mirrorchyan.com/api/resources/"
    user_agent = "BAAS_GUI"
    default_channel = "stable"
    default_app = "BAAS_repo"
    os, arch = detect_system_info()

    def get_cdk_state(self, cdk, timeout=3.0) -> CdkState:
        self.params["cdk"] = cdk

        response = requests.get(url=self.url, params=self.params, timeout=timeout)
        code = response.json()["code"]
        print(json.dumps(response.json(), indent=4))
        if code < 0:
            raise ServerInternalError("Error code : " + str(code))
        if code == 0:
            return CdkState.VALID
        elif code == MirrorCErrorCode.KEY_INVALID.value:
            return CdkState.INVALID
        elif code == MirrorCErrorCode.KEY_EXPIRED.value:
            return CdkState.EXPIRED
        elif code == MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value:
            return CdkState.EXHAUSTED
        elif code == MirrorCErrorCode.KEY_MISMATCHED.value:
            return CdkState.MISMATCHED
        elif code == MirrorCErrorCode.KEY_BLOCKED.value:
            return CdkState.BLOCKED
        else:
            raise ValueError(f"Unexpected response code: {code}")


    def __init__(self, app=default_app, current_version = "", channel = default_channel):
        self.app = app
        self.current_version = current_version
        self.channel = channel
        self.url = f"{self.basic_url}{self.app}/latest"
        self.params = {
            "channel": self.channel,
            "current_version": self.current_version,
            "user_agent": MirrorC_Updater.user_agent
        }

        if app == "BAAS_Cpp" or app == "BAAS_Cpp_cuda":
            self.params["os"] = MirrorC_Updater.os
            self.params["arch"] = MirrorC_Updater.arch

    def get_latest_version(self, cdk="", timeout=3.0):
        """
        Get the latest version of the application.
        :param cdk: The cdk to check.
        :param timeout: Request timeout in seconds.
        :return: The latest version as a string.
        """
        self.params["cdk"] = cdk
        response = requests.get(url=self.url, params=self.params, timeout=timeout)
        return RequestReturn(response.json())


