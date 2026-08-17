from typing import Optional
from datetime import datetime

from .classes import Log as _Log


def logcat(message: str, level: str = 'INFO', tag: str = 'BAAS') -> None:
    """
    Send message to Android logcat if available. Level is one of
    'DEBUG','INFO','WARNING','ERROR','CRITICAL','VERBOSE'.
    Falls back to printing when logcat is not available.
    """
    try:
        txt = str(message)
        if _Log is None:
            # fallback to stdout with timestamp
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {tag}/{level}: {txt}")
            return

        lvl = (level or 'INFO').upper()
        if lvl == 'DEBUG':
            _Log.d(tag, txt)
        elif lvl == 'INFO':
            _Log.i(tag, txt)
        elif lvl in ('WARNING', 'WARN'):
            _Log.w(tag, txt)
        elif lvl in ('ERROR', 'CRITICAL'):
            _Log.e(tag, txt)
        else:
            # VERBOSE or others
            try:
                _Log.v(tag, txt)
            except Exception:
                _Log.i(tag, txt)
    except Exception:
        # ensure logging never raises in production
        try:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {tag}/{level}: {message}")
        except Exception:
            pass


def d(msg: str, tag: str = 'BAAS') -> None:
    logcat(msg, level='DEBUG', tag=tag)


def i(msg: str, tag: str = 'BAAS') -> None:
    logcat(msg, level='INFO', tag=tag)


def w(msg: str, tag: str = 'BAAS') -> None:
    logcat(msg, level='WARNING', tag=tag)


def e(msg: str, tag: str = 'BAAS') -> None:
    logcat(msg, level='ERROR', tag=tag)


def v(msg: str, tag: str = 'BAAS') -> None:
    logcat(msg, level='VERBOSE', tag=tag)


class Logger:
    """Simple logger wrapper similar to android.util.Log methods."""

    def __init__(self, tag: str = 'BAAS'):
        self.tag = tag

    def d(self, msg: str):
        d(msg, tag=self.tag)

    def i(self, msg: str):
        i(msg, tag=self.tag)

    def w(self, msg: str):
        w(msg, tag=self.tag)

    def e(self, msg: str):
        e(msg, tag=self.tag)

    def v(self, msg: str):
        v(msg, tag=self.tag)
