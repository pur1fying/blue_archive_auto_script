import os.path
from core.device.nemu_client import NemuClient, NemuIpcIncompatible, NemuIpcError


class NemuScreenshot:
    def __init__(self, conn):
        # C:/Program Files/Netease/MuMu Player 12/shell/MuMuPlayer.exe
        self.config_set = conn.config_set
        self.config = conn.config
        self.logger = conn.logger
        self.serial = conn.serial

        self.nemu_folder = self.config.get("program_address")
        self.nemu_folder = os.path.dirname(self.nemu_folder)
        self.nemu_folder = os.path.dirname(self.nemu_folder)  # C:/Program Files/Netease/MuMu Player 12

        self.instance_id = NemuClient.serial_to_id(self.serial)
        if self.instance_id is not None:
            try:
                self.nemu_client = NemuClient.get_instance(self.nemu_folder, self.instance_id, self.logger)
            except (NemuIpcIncompatible, NemuIpcError) as e:
                self.logger.warning(e.__str__())
                self.logger.info("Emulator info incorrect. Try to auto detect mumu player path.")
                path = NemuClient.get_possible_mumu12_folder()
                self.logger.info(f"Auto detect mumu player path: {str(path)}")
                if path is not None:
                    self.logger.info(f"Set new config program_address.")
                    self.config_set.set("program_address", path)
                    self.nemu_folder = os.path.dirname(path)
                    self.nemu_folder = os.path.dirname(self.nemu_folder)
                    try:
                        self.nemu_client = NemuClient.get_instance(self.nemu_folder, self.instance_id, self.logger)
                    except (NemuIpcIncompatible, NemuIpcError) as e:
                        self.logger.error(e.__str__())
                        raise Exception("Unable to init NemuScreenshot with auto detected path.")
                else:
                    self.logger.error("MuMu Player 12 not found.")
                    raise Exception("Unable to use Init NemuScreenshot.")
        else:
            self.logger.error('Can\'t convert serial to instance id.')
            raise Exception("Invalid serial. Unable to use Init NemuScreenshot.")

    def screenshot(self):
        for i in range(3):
            try:
                if i > 0:
                    self.logger.warning("Retry : " + str(i))
                return self.nemu_client.screenshot()
            except Exception as e:
                self.logger.warning("Fail to call nemu screenshot.")
                self.logger.warning(e.__str__())


