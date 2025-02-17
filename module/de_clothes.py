def implement(self):
    """
        LocalizeConfig.txt --> isLocalize = false --> restart the game to download resources
    """
    try:
        if self.server == 'CN':
            self.u2.push('src/LocalizeConfig.txt', '/sdcard/Android/data/{0}/files/'.format(self.package_name))
            self.logger.info("De-clothes complete, restart to download resources")
        else:
            self.logger.info(self.server + " server not support")
        return True
    except Exception as e:
        self.logger.error("De-clothes error " + str(e))
        return False
