import datetime


def return_current_time():
    current_time = datetime.datetime.now()
    current_date = str(current_time.date())
    current_sec = str(current_time.time())
    len_sec = len(current_sec)
    for i in range(0, len_sec):
        if current_sec[i] == '.':
            current_sec = current_sec[0:i]
            return current_date + " " + current_sec
        if current_sec[i] == ':':
            current_sec = current_sec[0:i] + "." + current_sec[i + 1:len_sec]
