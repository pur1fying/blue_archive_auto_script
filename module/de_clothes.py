def implement(self):
    if self.server == 'CN':
        self.connection.push('src/LocalizeConfig.txt', '/sdcard/Android/data/{0}/files/'.format(self.package))
    elif self.server == "Global":
        self.logger.info("Global server not support")
