from enum import Enum, auto

class CdkState(Enum):
    VALID = auto()
    INVALID = auto()
    EXPIRED = auto()
    EXHAUSTED = auto()
    MISMATCHED = auto()
    BLOCKED = auto()

class MirrorCErrorCode(Enum):
    """
    Enum for MirrorC error codes.
    """
    SUCCESS = 0
    UNDIVIDED = 1
    INVALID_PARAMS = 1001
    KEY_EXPIRED = 7001
    KEY_INVALID = 7002
    RESOURCE_QUOTA_EXHAUSTED = 7003
    KEY_MISMATCHED = 7004
    KEY_BLOCKED = 7005
    RESOURCE_NOT_FOUND = 8001
    INVALID_OS = 8002
    INVALID_ARCH = 8003
    INVALID_CHANNEL = 8004
