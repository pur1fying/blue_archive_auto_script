def implement(self):
    try:
        if self.server == 'CN':
            self.u2.push('src/LocalizeConfig.txt', '/sdcard/Android/data/{0}/files/'.format(self.package_name))
            self.logger.info("De-clothes complete, restart to download resources")
        elif self.server == "Global":
            self.logger.info("Global server not support")
        elif self.server == "JP":
            self.logger.info("JP server not support")
        return True
    except Exception as e:
        self.logger.error("De-clothes error " + str(e))
        return False
