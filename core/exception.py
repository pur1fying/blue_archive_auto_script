import traceback


class SharedMemoryError(Exception):
    """
        Shared memory error.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RequestHumanTakeOver(Exception):
    """
        Exception can't be handled by baas.
        1. flag_run = false (click stop button)
        2. unable to connect to emulator
    """

    def __init__(self, message="Request Human Take Over"):
        self.message = message
        super().__init__(self.message)


class PackageIncorrect(Exception):
    """
        every 20s core.picture.co_detect func didn't match a feature it will check the package through adb.
        possible reasons:
        1. Game crushed.
        2. When starting the game BAAS may click into browser in Global server.
    """

    def __init__(self, message="Package Incorrect"):
        self.message = message
        super().__init__(self.message)


class FunctionCallTimeout(Exception):
    """
        core.picture.co_detect func call timeout 600s reached.
        possible reasons:
        1. Meet unexpected ui.
        2. Game keeps loading.
    """

    def __init__(self, message="Function Call Timeout"):
        self.message = message
        super().__init__(self.message)


class OcrInternalError(Exception):
    """
        BAAS_ocr_server internal error
    """
    def __init__(self, message="Ocr Internal Error"):
        self.message = message
        super().__init__(self.message)


class LogTraceback:
    def __init__(self, title=None, message=None, context=None):
        traceback.print_exc()
        assert context is not None
        self.message = message
        self.context = context
        context.send('stop')
        self.context.logger.error(title)
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
        self.context.logger.error('All activities stopped. Require human take over.')
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
