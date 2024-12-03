import traceback


class RequestHumanTakeOver(Exception):
    """
        Exception can't be handled by baas.
        1. flag_run = false (click stop button)
        2. unable to connect to emulator
    """

    def __init__(self, message="Request Human Take Over"):
        self.message = message
        super().__init__(self.message)


class ScriptError(Exception):
    def __init__(self, title=None, message=None, context=None):
        traceback.print_exc()
        assert context is not None
        self.message = message
        self.context = context
        context.send('stop')
        lines = message.split('\n')
        _lines = []
        for line in lines:
            while len(line) > 50:
                _lines.append(line[:50])
                line = line[50:]
            if line == '': continue
            _lines.append(line)
        for line in _lines:
            self.context.logger.error(line)
        self.context.logger.error(title)
        self.context.logger.error('All activities stopped. Require human take over.')
        super().__init__(self.message)
        # self.log_into_file()

    def log_into_file(self):
        with open('error.html', 'a') as f:
            if self.context.connection is None:
                return
            # screenshot = self.context.connection.screenshot()
            # numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
            # convert the image to base64 and mix it into the html
            # img_base64 = numpy_array.tobytes()
            # img_base64 = base64.b64encode(img_base64).decode('utf-8')
            # img_html = f'<img src="data:image/png;base64,{img_base64}">'
            f.write(self.context.logger.logs)
            f.write(self.message + '\n')

    def __str__(self):
        return self.message
