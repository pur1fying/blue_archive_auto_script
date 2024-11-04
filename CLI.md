# BAAS CLI 用法

BAAS CLI 提供了通过命令行运行 BAAS 核心功能的能力。

**提示**：BAAS CLI 目前为早期开发阶段，功能可能暂时不完善。未来会逐步完善功能，并且在用法上提供更好的设计。

## macOS 下安装及使用

暂时需要 [Anaconda](https://www.anaconda.com/) 提供的 Python 运行环境以支持 OCR 功能正常运行。

1. 安装 Anaconda，创建 Python 运行环境：

  ```bash
  conda init
  # 退出并重新打开终端，确保 conda 正常初始化完成
  conda create -n baas python=3.12
  ```

2. 下载 BAAS 源代码（建议使用 Git clone 方式方便更新），进入源代码目录，安装依赖：

  ```bash
  # 注意，每次打开终端都需要重新激活 conda 环境
  conda activate baas
  pip install pdm
  pdm install
  ```

2. 执行 `pdm run window.py` 运行 BAAS GUI，创建配置文件目录并按需调整配置。

3. 将 `cli.example.py` 复制为 `cli.your_account.py`，修改其中配置文件目录名为 `config` 目录下刚才 BAAS GUI 创建的配置文件目录名。可以通过注释或者取消注释 Python 代码的方式调整 BAAS 需要执行的任务。

4. 执行 `pdm run cli.your_account.py` 运行 BAAS CLI。一次运行将依次执行 `cli.your_account.py` 中列出的所有任务。

5. 可以通过 cron 或者 launchd 等工具定时执行 BAAS CLI。这种情况需要使用以下命令

  ```bash
  conda run -n baas --live-stream pdm run cli.your_account.py
  ```
