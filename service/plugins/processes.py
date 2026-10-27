"""Native worker-tree ownership; no shell or external process-control utility."""
from __future__ import annotations

from .errors import PluginError


def windows_job(process_id: int):
    """Attach a waiting worker before allowing it to import any plugin code.

    The non-inheritable job handle owns the entire descendant tree. Closing it
    terminates descendants, including children that inherited a stdout pipe.
    See https://learn.microsoft.com/windows/win32/procthread/job-objects.
    """
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    job = kernel.CreateJobObjectW(None, None)
    process = None
    try:
        if not job:
            raise OSError
        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise OSError
        process = kernel.OpenProcess(0x0100 | 0x0001, False, process_id)  # SET_QUOTA | TERMINATE
        if not process or not kernel.AssignProcessToJobObject(job, process):
            raise OSError
    except OSError:
        if job:
            kernel.CloseHandle(job)
        raise PluginError("WORKER_LIFECYCLE_FAILED", "Cannot attach the plugin worker to its process cleanup group.") from None
    finally:
        if process:
            kernel.CloseHandle(process)

    def close():
        nonlocal job
        if job:
            kernel.CloseHandle(job)
            job = None
    return close
