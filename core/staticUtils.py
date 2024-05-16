def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
