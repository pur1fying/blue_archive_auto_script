# BAAS 原生安装器

安装器程序与 `setup.toml` 始终放在一起，BAAS 本体则可以安装到绝对路径，也可以安装到以安装器目录为基准的相对路径；默认配置为 `.`。全屏 TUI 的语言由系统 UI 语言自动决定：简体中文系统显示中文，其他系统显示英文。Windows 发布版可执行文件已嵌入 BAAS 图标。

首次安装且目标为 `.`（安装器所在目录）时，因为此时尚无 `setup.toml`，该目录只允许存在安装器自身；发现其他内容便拒绝安装且不会删除。安装完成后再次运行时，可识别的既有 BAAS 会直接放行，不再套用首次目录纯净检查。选择独立的相对或绝对目标时，只检查目标目录本身；安装器旁或目标祖先目录中的其他文件不会阻塞安装。相对路径不得包含父目录分量 `..`（包括 `..`、`../BAAS`、`child/../BAAS`）。已有目标目录只有在能够证明属于 BAAS 安装时才会接受，否则必须选择新目录或空目录。

由于 BAAS 的 Qt 运行环境不兼容中文安装路径，安装目录的任意层级只要包含中文字符，安装器就会在创建 `setup.toml` 或目标目录前拒绝安装，并提示改用仅含 ASCII 字符的路径。

## 更新行为

- 主仓库与 OCR 并行准备；两项都成功后才修改正式文件。
- 安装一开始便在可执行文件旁创建 `setup.toml`，其中记录用户选择的绝对或相对 BAAS 路径；该操作早于仓库准备和网络测速，全程不会使用 `config.toml`。
- 先部署主仓库，再把 OCR 放入 `core/ocr/baas_ocr_client/bin`。
- 配置 MirrorChyan CDK 后，主仓库 `BAAS_repo` 支持无需更新、增量包和全量包。OCR 始终独立使用配置的 Git 源管理，不会向 MirrorChyan 请求 `BAAS_Cpp`。CDK 通过预检后会在安装开始时记录，只有 Mirror 工作流保持可用时才会保留；任一 MirrorChyan 步骤失败都会清空 CDK、停止安装并在 TUI 内弹出具体原因，绝不自动回退 Git。用户可重新填写 CDK，或返回安装设置取消 MirrorChyan。
- Git 会并行测量所有候选源获取远端 SHA 的响应时间；存在本机 Git CLI 时只使用 Git CLI，没有时才回退 libgit2。远端与本地提交相同会直接跳过 `fetch`，实际传输失败则继续尝试通过测速的后续源。
- 文件部署和 `setup.toml` 中的两个版本号在同一事务中提交；完整性检查或 uv 同步失败会回滚正式文件。

## 界面与日志

Git、解压和 uv 的终端输出通过 PTY 获取，并混合显示在同一个可滚动安装日志中。Git、uv、CPython 与 PyPI 的源测速各自在独立 section 中实时展开，测速完成后自动折叠成可用数量、选中源和延迟摘要；完整测速明细仍保留在 `log/installer.log`。可用方向键上/下或 Page Up/Page Down 查看历史。已登记的 CDK 和常见凭据请求头会被脱敏。

当 BAAS 根目录与安装器分离时，安装器会在每次目标合法的安装/更新会话开始时刷新 `.baas-installer/setup-location-v1.json`。这个带版本的指针始终指向可执行文件旁唯一的 `setup.toml`；没有指针的旧安装继续读取 BAAS 工作目录中的 `setup.toml`，指针损坏或失效时也会安全回退。

BAAS 成功以独立进程启动后，安装器立即退出；启动失败时保留错误和重试操作。
Linux 启动时会保留用户显式设置的 `QT_QPA_PLATFORM`；未设置时，只在确认 Wayland 会话和 socket 后选择 `wayland`，X11 与无法明确判断的 XWayland 兼容环境继续使用 Qt 默认平台。

## 便携 Python 环境

默认包管理器为 uv。受管理的 uv、Python、虚拟环境、缓存、凭据、XDG 状态与临时数据全部位于安装目录内（`toolkit/uv`、`.venv`、`tmp`）。`setup.toml` 中的自定义 `runtime_path` 仍然受支持。

依赖同步成功后，会在 `.baas-installer/dependencies-v1.sha256` 保存可迁移的 SHA-256 状态。只要依赖文件、编译锁、Python 版本和受管理环境都没变化，后续运行会跳过 uv 和所有下载测速。整体移动或重命名安装目录时，安装器会先修复自己管理的虚拟环境路径再检查缓存；外部自定义运行时不会被改写。

实际完成依赖解析和同步后，安装器会在安装目录限定的环境中调用受管理的 `uv cache clean`。安装器自身不会递归删除 uv、Python 下载、XDG 或临时目录。uv 本体、已安装 Python、虚拟环境、源测速排名、编译后的依赖文件和依赖 SHA 会保留。依赖 SHA 命中并跳过 uv 时不会改动缓存内容；清理中断或失败时会保留一个很小的 pending 标记，并在后续 SHA 命中允许跳过 uv 前优先重试。

只有确实需要下载时才会对对应资源测速。uv 与 CPython 均包含 CNB Release 镜像，同时保留配置中的 GitHub、Gitee 及代理回退源；PyPI 同样按测速结果选择。各候选源并发测速，并按实测速度依次尝试。已停用的 `baas-cdn.kiramei.workers.dev` 不会被使用。

## 构建与测试

使用 CMake 3.25+、C++20 编译器与 vcpkg：

```console
cmake -S deploy/installer -B build/installer -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build/installer --config Release
ctest --test-dir build/installer -C Release --output-on-failure
```

GitHub Actions 会构建 Windows x64、Linux x64、macOS x64 与 macOS arm64。版本标签构建会把四个平台的程序及 `SHA256SUMS` 发布为 GitHub Release 资产。
