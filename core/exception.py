import base64

import numpy as np

from gui.util import log
from gui.util.log import logs


class ScriptError(Exception):
    def __init__(self, message=None, context=None):
        assert context is not None
        self.message = message
        self.context = context
        context.send('stop')
        log.d(message, level=3, logger_box=context.loggerBox)
        super().__init__(self.message)
        self.log_into_file()

    def log_into_file(self):
        with open('error.html', 'a') as f:
            if self.context.connection is None:
                return
            screenshot = self.context.connection.screenshot()
            numpy_array = np.array(screenshot)[:, :, [2, 1, 0]]
            # convert the image to base64 and mix it into the html
            img_base64 = numpy_array.tobytes()
            img_base64 = base64.b64encode(img_base64).decode('utf-8')
            img_html = f'<img src="data:image/png;base64,{img_base64}">'
            f.write(logs)
            f.write(self.message + '\n')

    def __str__(self):
        return self.message
