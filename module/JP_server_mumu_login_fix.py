

def implement(self):
    self.logger.info("[ su ] response : ")
    self.logger.info(str(self.connection.shell('su')))
    self.logger.info("[ rm -rf /system/xbin/{su,mu_bak} /system/bin/su ] response : ")
    self.logger.info(str(self.connection.shell('rm -rf /system/xbin/{su,mu_bak} /system/bin/su')))
    return True
