import os.path
from core.device.nemu_client import NemuClient, NemuIpcIncompatible, NemuIpcError


class NemuScreenshot:
    def __init__(self, conn):
        # C:/Program Files/Netease/MuMu Player 12/shell/MuMuPlayer.exe
        self.config = conn.config
        self.logger = conn.logger
        self.serial = conn.serial

        self.nemu_folder = self.config.get("program_address")
        self.nemu_folder = os.path.dirname(self.nemu_folder)
        self.nemu_folder = os.path.dirname(self.nemu_folder)    # C:/Program Files/Netease/MuMu Player 12

        self.instance_id = NemuClient.serial_to_id(self.serial)
        if self.instance_id is not None:
            try:
                self.nemu_client = NemuClient.get_instance(self.nemu_folder, self.instance_id, self.logger)
            except (NemuIpcIncompatible, NemuIpcError) as e:
                self.logger.error(e.__str__())
                self.logger.error('Emulator info incorrect')
        else:
            self.logger.error('Unable to use Init Nemu Screenshot.')
            raise Exception("Unable to use Init Nemu Screenshot.")

    def screenshot(self):
        return self.nemu_client.screenshot()


