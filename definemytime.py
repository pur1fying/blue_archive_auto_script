import datetime


class my_time:
    def return_current_time(self):
        current_time = datetime.datetime.now()
        current_date = str(current_time.date())
        current_sec = str(current_time.time())
        leng = len(current_sec)
        for i in range(0, leng):
            if current_sec[i] == '.':
                current_sec = current_sec[0:i+2]
                return current_date + " " + current_sec
            if current_sec[i] == ':':
                current_sec = current_sec[0:i] + "." + current_sec[i+1:leng]

