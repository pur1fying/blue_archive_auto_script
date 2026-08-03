# BAAS 原生安装器

安装器会把 BAAS 安装或迁移到安装器可执行文件所在目录。全屏 TUI 的语言由系统 UI 语言自动决定：简体中文系统显示中文，其他系统显示英文。Windows 发布版可执行文件已嵌入 BAAS 图标。

## 更新行为

- 主仓库与 OCR 并行准备；两项都成功后才修改正式文件。
- 安装一开始便在可执行文件旁创建 `setup.toml`，早于仓库准备和网络测速；全程不会使用 `config.toml`。
- 先部署主仓库，再把 OCR 放入 `core/ocr/baas_ocr_client/bin`。
- 配置 MirrorChyan CDK 后，`BAAS_repo` 与 `BAAS_Cpp` 均支持无需更新、增量包和全量包；MirrorChyan 失败会自动回退 Git。
- Git 会先用本机 Git CLI 依次尝试全部源，再用 libgit2 依次尝试全部源。它先比较远端与本地提交，相同则直接跳过 `fetch`。
- 文件部署和 `setup.toml` 中的两个版本号在同一事务中提交；完整性检查或 uv 同步失败会回滚正式文件。

## 界面与日志

Git、解压和 uv 的终端输出通过 PTY 获取，并混合显示在同一个可滚动安装日志中。可用方向键上/下或 Page Up/Page Down 查看历史。安装器消息与子进程输出也会写入 `log/installer.log`；已登记的 CDK 和常见凭据请求头会被脱敏。

BAAS 成功以独立进程启动后，安装器立即退出；启动失败时保留错误和重试操作。

## 便携 Python 环境

默认包管理器为 uv。受管理的 uv、Python、虚拟环境、缓存、凭据、XDG 状态与临时数据全部位于安装目录内（`toolkit/uv`、`.venv`、`tmp`）。`setup.toml` 中的自定义 `runtime_path` 仍然受支持。

依赖同步成功后，会在 `.baas-installer/dependencies-v1.sha256` 保存可迁移的 SHA-256 状态。只要依赖文件、编译锁、Python 版本和受管理环境都没变化，后续运行会跳过 uv 和所有下载测速。整体移动或重命名安装目录时，安装器会先修复自己管理的虚拟环境路径再检查缓存；外部自定义运行时不会被改写。

实际完成依赖解析和同步后，安装器会删除安装目录内的 uv 包缓存、Python 下载缓存、XDG 缓存和 uv 临时目录。uv 本体、已安装 Python、虚拟环境、源测速排名、编译后的依赖文件和依赖 SHA 会保留。依赖 SHA 命中并跳过 uv 时不会改动缓存内容；清理中断或失败时会保留一个很小的 pending 标记，并在后续 SHA 命中允许跳过 uv 前优先重试。

只有确实需要下载时才会对对应资源测速。uv 与 CPython 均包含 CNB Release 镜像，同时保留配置中的 GitHub、Gitee 及代理回退源；PyPI 同样按测速结果选择。各候选源并发测速，并按实测速度依次尝试。已停用的 `baas-cdn.kiramei.workers.dev` 不会被使用。

## 构建与测试

使用 CMake 3.25+、C++20 编译器与 vcpkg：

```console
cmake -S deploy/installer -B build/installer -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build/installer --config Release
ctest --test-dir build/installer -C Release --output-on-failure
```

GitHub Actions 会构建 Windows x64、Linux x64、macOS x64 与 macOS arm64。版本标签构建会把四个平台的程序及 `SHA256SUMS` 发布为 GitHub Release 资产。
