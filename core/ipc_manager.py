import cv2
import numpy as np
import os
from multiprocessing import shared_memory
from core.exception import SharedMemoryError


class SharedMemory:
    shm_map = {}

    @staticmethod
    def get(name):
        if name not in SharedMemory.shm_map:
            SharedMemory.shm_map[name] = SharedMemory(name)
        return SharedMemory.shm_map[name]

    @staticmethod
    def shm_exists(name):
        return name in SharedMemory.shm_map

    @staticmethod
    def set_data(name, data, size):
        if name not in SharedMemory.shm_map:
            raise SharedMemoryError(f"Shared memory {name} not found")
        shm = SharedMemory.shm_map[name]
        if shm.size < size:
            raise SharedMemoryError(f"Shared memory {name} size {shm.size} not enough for {size}")
        shm.shm.buf[:size] = data

    @staticmethod
    def release(name):
        if name in SharedMemory.shm_map:
            SharedMemory.shm_map[name]._release()
            del SharedMemory.shm_map[name]

    def __init__(self, name):
        self.name = name
        self.size = None
        self.shm = None
        self._init()

    def _init(self):
        self.shm = shared_memory.SharedMemory(create=False, name=self.name)
        if self.shm is None:
            raise SharedMemoryError(f"Shared memory {self.name} not found")
        self.size = self.shm.size

    def _release(self):
        self.shm.close()
        self.shm.unlink()
