# BAAS 原生安装器

安装器会把 BAAS 安装或迁移到安装器可执行文件所在目录。界面语言由系统 UI 语言自动决定：简体中文系统显示中文，其他系统显示英文。

## 更新行为

- 主仓库与 OCR 并行准备；两项都成功后才修改正式文件。
- 先部署主仓库，再把 OCR 放入 `core/ocr/baas_ocr_client/bin`。
- 配置 MirrorChyan CDK 后，`BAAS_repo` 与 `BAAS_Cpp` 均支持无需更新、增量包和全量包；MirrorChyan 失败会自动回退 Git。
- Git 会先用本机 Git CLI 依次尝试全部源，再用 libgit2 依次尝试全部源。它先比较远端与本地提交，相同则直接跳过 `fetch`。
- 文件部署和 `setup.toml` 中的两个版本号在同一事务中提交；完整性检查或 uv 同步失败会回滚正式文件。

## 界面与日志

Git、解压和 uv 的终端输出通过 PTY 获取，并混合显示在同一个可滚动安装日志中。可用方向键上/下或 Page Up/Page Down 查看历史。安装器消息与子进程输出也会写入 `log/installer.log`；已登记的 CDK 和常见凭据请求头会被脱敏。

BAAS 成功以独立进程启动后，安装器立即退出；启动失败时保留错误和重试操作。

## 便携 Python 环境

默认包管理器为 uv。受管理的 uv、Python、虚拟环境、缓存、凭据、XDG 状态与临时数据全部位于安装目录内（`toolkit/uv`、`.venv`、`tmp`）。`setup.toml` 中的自定义 `runtime_path` 仍然受支持。

## 构建与测试

使用 CMake 3.25+、C++20 编译器与 vcpkg：

```console
cmake -S deploy/installer -B build/installer -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build/installer --config Release
ctest --test-dir build/installer -C Release --output-on-failure
```

GitHub Actions 会构建 Windows x64、Linux x64、macOS x64 与 macOS arm64。版本标签构建会把四个平台的程序及 `SHA256SUMS` 发布为 GitHub Release 资产。
