import sys
import platform
from pathlib import Path


def remove_first_dir(path_str):
    path = Path(path_str)
    parts = path.parts
    if len(parts) > 1:
        return Path(*parts[1:]).as_posix()
    else:
        return path_str

def detect_system_info():
    raw_system = platform.system().lower()
    sys_platform = sys.platform.lower()
    machine = platform.machine().lower()

    if "android" in sys_platform or "android" in raw_system:
        _os = "android"
    elif raw_system == "windows":
        _os = "windows"
    elif raw_system == "darwin":
        _os = "darwin"
    elif raw_system == "linux":
        _os = "linux"
    else:
        _os = "universal"

    arch_aliases = {
        "386":      "386",
        "x86":      "386",
        "i386":     "386",
        "x86_32":   "386",

        "x64":      "amd64",
        "amd64":    "amd64",
        "x86_64":   "amd64",
        "intel64":  "amd64",

        "arm":      "arm",
        "arm64":    "arm64",
        "aarch64":  "arm64",
    }
    arch = arch_aliases.get(machine, machine)
    return _os, arch



if __name__ == "__main__":
    os, architecture = detect_system_info()
    print(f"Detected OS: {os}, Architecture: {architecture}")
