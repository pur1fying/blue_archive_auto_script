def implement(self):
    if self.server == 'CN':
        self.connection.push('src/LocalizeConfig.txt', '/sdcard/Android/data/{0}/files/'.format(self.package_name))
        self.logger.info("de-clothes complete, restart to download resources")
    elif self.server == "Global":
        self.logger.info("Global server not support")
