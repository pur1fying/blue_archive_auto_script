import json
import shutil
import requests

from mirrorc_update.utils import detect_system_info, remove_first_dir
from mirrorc_update.const import CdkState, MirrorCErrorCode


class RequestReturn:
    def __init__(self, response_json):
        self.code = response_json["code"]
        self.message = response_json["msg"]
        # server internal error
        if self.code < MirrorCErrorCode.SUCCESS.value:
            self.has_data = False
            return

        if self.code not in [
            MirrorCErrorCode.SUCCESS.value,
            MirrorCErrorCode.KEY_INVALID.value,
            MirrorCErrorCode.KEY_EXPIRED.value,
            MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value,
            MirrorCErrorCode.KEY_MISMATCHED.value,
            MirrorCErrorCode.KEY_BLOCKED.value
        ]:
            self.has_data = False
            return
        self.has_data = True
        self.data = response_json["data"]

        self.has_url = "url" in self.data
        self.release_note = self.data.get("release_note")
        self.latest_version_name = self.data.get("version_name")
        if self.has_url:
            self.sha256 = self.data.get("sha256")
            self.download_url = self.data.get("url")
            self.update_type = self.data.get("update_type")
            self.file_size = self.data.get("filesize")
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

    def __init__(self, app=default_app, current_version="", channel=default_channel):
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

    def set_version(self, version):
        self.current_version = version
        self.params["current_version"] = version

    def get_latest_version(self, cdk="", timeout=3.0):
        self.params["cdk"] = cdk
        response = requests.get(url=self.url, params=self.params, timeout=timeout)
        return RequestReturn(response.json())

    @staticmethod
    def apply_update(source_dir, changes_json_path, target_dir, logger):
        try:
            logger.info("Applying incremental update...")
            if not source_dir.exists() or not source_dir.is_dir():
                raise FileNotFoundError(f"Update source directory not found: {source_dir}")

            if not changes_json_path.exists() or not changes_json_path.is_file():
                raise FileNotFoundError(f"Changes JSON file not found: {changes_json_path}")

            with open(changes_json_path, 'r', encoding='utf-8') as f:
                changes = json.load(f)

            target_dir.mkdir(parents=True, exist_ok=True)

            # deleted
            deleted = changes.get("deleted", [])
            if len(deleted) > 0:
                total = len(deleted)
                cnt = 0
                logger.info(f"Deleted : [ {total} ]")
                for file in deleted:
                    cnt += 1
                    dest_file = target_dir / remove_first_dir(file)
                    if dest_file.exists():
                        if dest_file.is_file():
                            dest_file.unlink()
                            logger.success(f"Deleting {cnt}/{total}")
                            logger.info(f"{file}")
                    else:
                        logger.warning(f"File not found for deletion: {file}")
            else:
                logger.info("No Deleted File")

            # added
            added = changes.get("added", [])
            if len(added) > 0:
                total = len(added)
                logger.info(f"Added : [ {total} ]")
                cnt = 0
                for file in added:
                    cnt += 1
                    source_file = source_dir / file
                    dest_file = target_dir / remove_first_dir(file)
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        logger.success(f"Adding {cnt}/{total}")
                        logger.info(f"{file}")
                    else:
                        logger.warning(f"Source file not found for adding : {source_file}")
            else:
                logger.info("No Added File")

            # modified
            modified = changes.get("modified", [])
            if len(modified) > 0:
                total = len(modified)
                logger.info(f"Modified : [ {total} ]")
                cnt = 0
                for file in modified:
                    cnt += 1
                    source_file = source_dir / file
                    dest_file = target_dir/ remove_first_dir(file)
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        logger.success(f"Modifying {cnt}/{total}")
                        logger.info(f"{file}")
                    else:
                        logger.warning(f"Source file not found for modification : {source_file}")
            else:
                logger.info("No Modified File")

            logger.info("MirrorC Incremental Update Success.")
            return True

        except Exception as e:
            logger.error(f"MirrorC Incremental Update failed : {str(e)}")
            return False

    @staticmethod
    def log_mirrorc_error(ret : RequestReturn, logger):
        if ret.code == MirrorCErrorCode.KEY_INVALID.value:
            logger.warning("Your CDK is invalid.")
        elif ret.code == MirrorCErrorCode.KEY_EXPIRED.value:
            logger.warning("Your CDK is expired.")
        elif ret.code == MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value:
            logger.warning("CDK resource quota exhausted.")
        elif ret.code == MirrorCErrorCode.KEY_MISMATCHED.value:
            logger.warning("CDK is mismatched.")
        elif ret.code == MirrorCErrorCode.KEY_BLOCKED.value:
            logger.warning("CDK is blocked.")
        elif ret.code == MirrorCErrorCode.UNDIVIDED.value:
            logger.warning("Undivided error, message: " + ret.message)
        elif ret.code < MirrorCErrorCode.SUCCESS.value:
            logger.warning("Server internal error, code : " + str(ret.code) + ", message: " + ret.message)
            logger.warning("This is a problem with mirrorc, not BAAS, please report to mirrorc support.")
        if ret.code in [
            MirrorCErrorCode.KEY_INVALID.value,
            MirrorCErrorCode.KEY_EXPIRED.value,
            MirrorCErrorCode.RESOURCE_QUOTA_EXHAUSTED.value,
            MirrorCErrorCode.KEY_MISMATCHED.value,
            MirrorCErrorCode.KEY_BLOCKED.value
        ]:
            logger.info("If you want to use mirrorc to update BAAS.")
            logger.info("Please visit https://mirrorchyan.com/zh/get-start to get a valid CDK.")
