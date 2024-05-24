import module.dailyGameActivities

func_names = {
    "serikaSummerRamenStall": module.dailyGameActivities.serikaSummerRamenStall.implement,
}


def implement(self):
    if self.dailyGameActivity is None or self.dailyGameActivity not in func_names:
        self.logger.warning("Current Daily Activity is not supported")
        return True
    return func_names[self.dailyGameActivity](self)
