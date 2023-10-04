import logging
import threading

from flask import Flask, render_template
from gevent import pywsgi


class DebuggerView(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.WARNING)
        self.content = 'BAAS Debugger'
        self.route('/')(self.debug_page)
        self.route('/api')(self.debug_api)

    def debug_page(self):
        return render_template('index.html', content=self.content)

    def debug_api(self):
        return {"data": self.content}

    def add_content(self, content):
        self.content += content


debugger_view = DebuggerView(__name__)


def start_view():
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), debugger_view)
    server.serve_forever()


def start_debugger():
    debugger = threading.Thread(target=start_view, daemon=True)
    debugger.start()
