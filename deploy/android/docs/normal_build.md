# 构建 BoA
## 环境配置


## 构建
在 devcontainer 中执行以下命令：
```bash
source .venv/bin/activate
python deploy/android/build.py
```

在宿主机中执行以下命令：
```bash
docker cp <container_id>:/workspaces/baas_on_android/boa-0.1-arm64-v8a-debug.apk .
adb install boa-0.1-arm64-v8a-debug.apk
```