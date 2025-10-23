# Q&A
此文件作为问题记录。

## ModuleNotFoundError: No module named '_posixshmem'
```
Traceback (most recent call last):
  File "/workspaces/baas_for_android/.buildozer/android/app/main.py", line 4, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/app/core/ocr/ocr.py", line 6, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/app/core/ocr/baas_ocr_client/Client.py", line 11, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/app/core/ipc_manager.py", line 4, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/arm64-v8a__ndk_target_24/python3/Lib/multiprocessing/shared_memory.py", line 23, in <module>
ModuleNotFoundError: No module named '_posixshmem'
```

multiprocessing 模块在 Android 上不支持，需要使用其他方案。

## _psutil_linux.abi3.so is for EM_X86_64 (62) instead of EM_AARCH64 (183)
```
Traceback (most recent call last):
  File "/workspaces/baas_for_android/.buildozer/android/app/main.py", line 6, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/app/core/Baas_thread.py", line 14, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/platform/build-arm64-v8a/build/python-installs/boa/arm64-v8a/psutil/__init__.py", line 93, in <module>
  File "/workspaces/baas_for_android/.buildozer/android/platform/build-arm64-v8a/build/python-installs/boa/arm64-v8a/psutil/_pslinux.py", line 26, in <module>
ImportError: dlopen failed: "/data/data/top.qwq123.boa/files/app/_python_bundle/site-packages/psutil/_psutil_linux.abi3.so" is for EM_X86_64 (62) instead of EM_AARCH64 (183)
```

psutil 库在 Android 上不可用，需要对所有使用 psutil 的地方进行处理。