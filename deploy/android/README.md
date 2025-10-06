# Android Deployment
This directory contains the deployment script for Android.

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
        "host": "host.docker.internal", // Or "localhost" if you are not using Docker
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "."
        }
    ]
}
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