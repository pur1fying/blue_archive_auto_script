import socket
import threading

from flask import Flask, render_template
# from gevent import pywsgi


class DebuggerView(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = 'BAAS Debugger'
        self.content = ''
        self.route('/')(self.debug_page)
        self.route('/api')(self.debug_api)

    def debug_page(self):
        return render_template('index.html', title=self.title)

    def debug_api(self):
        return {"data": self.content}

    def add_content(self, content):
        self.content += content


debugger_view = DebuggerView(__name__)


def start_view():
    debugger_view.run(host='127.0.0.1', port=5000, debug=False)
    # server = pywsgi.WSGIServer(('127.0.0.1', 5000), debugger_view, log=None)
    # server.serve_forever()


def start_debugger():
    debugger = threading.Thread(target=start_view, daemon=True)
    debugger.start()
