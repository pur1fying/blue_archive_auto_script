# Android Deployment
This directory contains the deployment script for Android.

## Build
// TODO

## Install
```powershell
# On you host machine
docker cp <container_id>:/workspaces/baas_on_android/boa-0.1-arm64-v8a-debug.apk .
adb install boa-0.1-arm64-v8a-debug.apk
```

## Debugging
### Logcat
All stdout and stderr will be redirected to logcat. You can use `adb logcat` to view the logs.

```bash
adb logcat -s boa
```

Or you can install Android Studio to get a better experience.

### Remote Debugging
To remote debug the application, you need VSCode and Python extension.

1. Add the following configuration to `.vscode/launch.json`:
```json
{
    "name": "Attach to BoA",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "host.docker.internal", // or "localhost" if you are not using Docker
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "."
        },
        {
            "localRoot": "${workspaceFolder}/.venv/lib/python3.9/site-packages",
            "remoteRoot": "${workspaceFolder}/.buildozer/android/platform/build-arm64-v8a/build/python-installs/boa/arm64-v8a/"
        },
        {
            "localRoot": "/usr/local/lib/python3.9/",
            "remoteRoot": "${workspaceFolder}/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/arm64-v8a__ndk_target_24/python3/Lib/"
        }
    ],
    "justMyCode": false
},
```

2. Add the following code before any import statements in `main.py`:
```python
import debugpy
debugpy.listen(5678, in_process_debug_adapter=True)
print("Waiting for debugger attach...")
debugpy.wait_for_client() # Comment this line if you don't want to block here
```

3. Set breakpoints in VSCode. You can also set breakpoints using code:
```python
import debugpy
debugpy.breakpoint()
```

4. Forward the port 5678 to your development machine:
```bash
adb forward tcp:5678 tcp:5678
```

5. Start the application on your device.

6. Start debugging using `Attach to BoA` configuration.

## Hot patch
Hot patch means to modify the Python code without rebuilding&reinstalling the APK. This 
is extremely useful when no Java code or Python library code is modified.

Currently, the only way to hot patch is done by adb.

```powershell
# On your host machine
docker cp <container_id>:/workspaces/baas_for_android/<file_name> .
adb -s <device_serial> push <file_name> /data/local/tmp/<file_name>
adb shell run-as org.baas.boa cp /data/local/tmp/<file_name> /data/data/org.baas.boa/files/app/<file_name>
```