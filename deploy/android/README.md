# Android Deployment
This directory contains the deployment script and Android wrapper for BaasOnAndroid.

## Setup
You'll need a Linux environment to build BaasOnAndroid. MacOS is not tested. 
// WIP

## Build

Building includes 3 stages:
```
graph TD
    %% One-time Setup Section
    subgraph Setup [One-time Setup]
        A[PySide Android Setup] --> B[BoA]
        B --> C[PythonForAndroid]
        C --> D[Gradle]
    end

    %% Deployment Process Section
    subgraph Deployment [pyside-deploy-android Process]
        E[Download Qt deps & Generate Recipes] --> F[Copy files & Save to Git]
        F --> G[Generate buildozer.spec]
        
        subgraph BuildSteps [Internal Build Loop]
            H1[Install & Build Python deps] --> H2[Compile Python Source Code]
            H2 --> H3[Collect .pyd & Resource Files]
            H3 --> H4[Generate Android Project]
            H4 --> H5[Patch build.gradle <br/>'done by hook of BoA']
        end
        
        G --> H1
        H5 --> I[Build Java]
    end

    %% Connection between Setup and Deployment
    D -.-> E
```

```shell
# Setup env
sh ./deploy/android/setup_devcontainer.sh
source .venv/bin/activate
# Build
buildozer android debug
```

## Install
For Docker/Devcontainer users, adb has already beed set up correctly. 
Simply start adb server on Windows side and connect to target device. 
Then adb commands start to will on the Linux side.

```shell
# Windows
adb devices

# Docker
adb install ./boa-0.1-arm64-v8a-debug.apk
```

## Debugging
### Logcat
All stdout and stderr will be redirected to logcat. You can use `adb logcat` to view the logs.

```bash
adb logcat -s boa
```

Or you can install Android Studio to get a better experience.

### Debug Python Code
To debug the Python code, you need VSCode and Python extension.

> **NOTE**: PyCharm is not tested.

1. First build and install BoA

2. Add the following code at the very beginning of `main.py`:
```python
# main.py
import debugpy
debugpy.listen(5678, in_process_debug_adapter=True)
print("Waiting for debugger attach...")
debugpy.wait_for_client() # Comment this line if you don't want to block here
```

3. Set breakpoints in VSCode. You can also set breakpoints using code:
```python
breakpoint()
```

4. Start debugging using `Sync and Start BoA` configuration, or `Attach to BoA` if you want push files and start BoA manually.

### Debug Java Code
1. Android Studio -> File -> Profile or Debug APK
2. Open any decompiled smali file from the left side Project View
3. Then you will see this tip "Disassembled classes.dex file. To set up breakpoints for debugging, please attach Kotlin/Java source files."
4. Attach `${workspace}/deploy/android/src`.
5. Set breakpoints and start debug

> **Note**
> 
> For WSL2 users, UNC paths can help you access files in WSL2 from Windows directly.
> Run `explorer.exe .` in WSL2 to find out the actual working directory path.

> **Note 2**
> 
> If you keep getting errors like `Error running 'Android Java Debugger (pid: 17964, debug port: 53357)' Unable to open debugger port (localhost:53357): java.io.IOException`, go to Edit Configurations -> Debugger -> Debug type, and change it to "Java Only"

## Hot patch
Hot patch means to modify the Python code without rebuilding&reinstalling the APK. This 
is extremely useful when no Java code is modified or Python dependencies are changes.

```shell
# On host/WSL2
python3 deploy/android/sync.py
python3 deploy/android/sync.py --dry-run # list changes only
```