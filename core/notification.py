import os

# Check if the current OS is Windows
try:
    from win11toast import notify as _notify
    from win11toast import toast as _toast
except ImportError:
    _notify = None
    _toast = None
app_id = 'BlueArchiveAutoScript.exe'
icon_path = '/gui/assets/logo.png'


def get_root_path():
    root_path = os.path.abspath(os.path.dirname(__file__))
    while True:
        if "window.py" in os.listdir(root_path):
            return root_path
        root_path = os.path.dirname(root_path)


def notify(title=None, body=None):
    root_path = get_root_path()
    if _notify is None:
        print(f"{title}: {body}")
        return

    _notify(
        title=title,
        body=body,
        app_id='BlueArchiveAutoScript.exe',
        icon=root_path + icon_path,
    )

def toast(title=None, body=None, button=None, duration=None):
    root_path = get_root_path()
    return _toast(
        title=title,
        body=body,
        app_id='BlueArchiveAutoScript.exe',
        icon=root_path + icon_path,
        button=button, 
        duration=duration
        )
        