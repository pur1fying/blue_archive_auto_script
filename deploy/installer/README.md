# BAAS native installer

The installer installs or migrates BAAS next to its own executable. Its full-viewport TUI selects its language from the operating-system UI locale: Simplified Chinese locales use Chinese; all other locales use English. Windows release executables embed the BAAS icon.

## Update behavior

- Main and OCR downloads are prepared concurrently. Live files are changed only after both preparations succeed.
- `setup.toml` is created beside the executable as soon as installation starts, before repository preparation or network probing. No `config.toml` is used.
- The main repository is applied first. OCR is then placed in `core/ocr/baas_ocr_client/bin`.
- With a MirrorChyan CDK, both `BAAS_repo` and `BAAS_Cpp` support current, incremental, and full packages. A failed MirrorChyan attempt falls back to Git.
- Git measures configured sources concurrently by remote-SHA response time. When Git CLI is installed it is used exclusively; libgit2 is the fallback only on systems without Git CLI. An equal remote/local commit skips `fetch`, and a failed real transfer advances to the next source that passed the SHA probe.
- Deployment and the two recorded versions in `setup.toml` are transactional. A failed verification or uv sync rolls live files back.
- An installation-local process lock prevents a second installer from deleting an active transaction. Repository history compaction runs only after rollback-capable validation and durable configuration commit.

## Interface and logs

Git, archive, and uv terminal output is captured through a PTY and shown in one scrollable installation log. Use Up/Down or Page Up/Page Down to inspect history. Installer messages and subprocess output are also written to `log/installer.log`; registered CDKs and common credential headers are redacted.

After a successful detached BAAS launch, the installer exits immediately. A launch failure remains visible and can be retried.

## Portable Python environment

The default package manager is uv. The managed uv executable, Python distributions, virtual environment, cache, credentials, XDG state, and temporary data all stay below the installation root (`toolkit/uv`, `.venv`, `tmp`). A custom `runtime_path` in `setup.toml` remains supported.

Successful dependency synchronization records a portable SHA-256 stamp at `.baas-installer/dependencies-v1.sha256`. When requirements, the compiled lock, Python version, and managed environment still match, later runs skip uv and all download benchmarks. Moving or renaming the whole installation repairs installer-managed virtual-environment paths before this cache check; external custom runtimes are never rewritten.

After a real dependency compile and sync succeeds, the installer removes the installation-local uv package cache, Python download cache, XDG cache, and uv temporary directory. The uv executable, installed Python, virtual environment, source ranking, compiled requirements, and dependency stamp remain in place. A dependency-SHA cache hit does not touch cache contents. An interrupted or failed cleanup leaves a small pending marker and is retried before a later SHA cache hit can skip uv.

When a download is actually required, the installer benchmarks only that source family. uv and CPython include the CNB release mirrors, while uv, CPython, and PyPI retain their configured GitHub, Gitee, and proxy fallbacks. Probes run concurrently and successful sources are attempted in measured order. The retired `baas-cdn.kiramei.workers.dev` endpoint is not used.

## Build and test

Use CMake 3.25+ with a C++20 compiler and vcpkg:

```console
cmake -S deploy/installer -B build/installer -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build/installer --config Release
ctest --test-dir build/installer -C Release --output-on-failure
```

GitHub Actions builds Windows x64, Linux x64, macOS x64, and macOS arm64. Tag builds publish all four binaries and `SHA256SUMS` as GitHub Release assets.
