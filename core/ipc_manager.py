import ctypes
import mmap
import cv2
import numpy as np
import os


class SharedMemoryError(Exception):
    pass


class SharedMemory:
    lib_BAAS_path = "C:\\Users\\pc\\Desktop\\work\\c\\BAAS_Cpp\\cmake-build-debug\\lib_BAAS.dll"
    lib_BAAS = None

    def __init__(self, _name, data=None, _size=0):
        self._name = _name
        self.exist = self.shared_memory_exists(self._name)
        if not self.exist:
            if _size <= 0:
                raise SharedMemoryError("Size must be greater than 0")
            self.size = _size
        else:
            self.size = self.get_shared_memory_size(self._name)
        self.shared_memory_ptr = self.init_mem(data)

    def init_mem(self, data=None):
        return self.get_shared_memory(self._name, self.size, data)

    def put_data(self, data, sz):
        self.set_shared_memory_data(self._name, data, sz)

    def __del__(self):
        try:
            self.release()
        except OSError:
            pass

    def release(self):
        SharedMemory.lib_BAAS.release_shared_memory(self._name.encode())

    @staticmethod
    def set_shared_memory_data(_name, data, _size):
        d = np.asarray(data, dtype=np.uint8)
        data_ptr = d.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
        SharedMemory.lib_BAAS.set_shared_memory_data(_name.encode(), _size, data_ptr)

    @staticmethod
    def get_shared_memory(_name, _size=0, data=None):
        if data is None:
            data_ptr = ctypes.POINTER(ctypes.c_int)()
        else:
            d = np.asarray(data, dtype=np.uint8)
            data_ptr = d.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
        return SharedMemory.lib_BAAS.get_shared_memory(_name.encode(), _size, data_ptr)

    @staticmethod
    def shared_memory_exists(_name):
        return SharedMemory.lib_BAAS.shared_memory_exists(_name.encode())

    @staticmethod
    def get_shared_memory_size(_name):
        return SharedMemory.lib_BAAS.get_shared_memory_size(_name.encode())

    @staticmethod
    def get_shared_memory_data(_name, _size):
        data_ptr = ctypes.pointer((ctypes.c_ubyte * _size)())
        SharedMemory.lib_BAAS.get_shared_memory_data(_name.encode(), data_ptr, _size)
        return data_ptr.contents

    @staticmethod
    def init_lib():
        p = SharedMemory.lib_BAAS_path
        if not os.path.exists(p):
            raise SharedMemoryError("lib_BAAS.dll not found")
        try:
            SharedMemory.lib_BAAS = ctypes.CDLL(p)
        except Exception as e:
            raise SharedMemoryError("Failed to load lib_BAAS.dll")


SharedMemory.init_lib()

img = cv2.imread("../request_failed.png")
name = "test"
print(SharedMemory.shared_memory_exists(name))

sm = SharedMemory(name, img, img.size)
print(SharedMemory.shared_memory_exists(name))
input("Press Enter to continue...")

img = cv2.imread("../network_unstable.png")
sm.put_data(img, img.size)

input("Press Enter to continue...")

sm.release()
print(SharedMemory.shared_memory_exists(name))


input("Press Enter to continue...")
exit(0)
