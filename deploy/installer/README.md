# BAAS native installer

The installer installs or migrates BAAS next to its own executable. Its language is selected from the operating-system UI locale: Simplified Chinese locales use Chinese; all other locales use English.

## Update behavior

- Main and OCR downloads are prepared concurrently. Live files are changed only after both preparations succeed.
- The main repository is applied first. OCR is then placed in `core/ocr/baas_ocr_client/bin`.
- With a MirrorChyan CDK, both `BAAS_repo` and `BAAS_Cpp` support current, incremental, and full packages. A failed MirrorChyan attempt falls back to Git.
- Git uses the installed Git CLI across every configured source before libgit2. It compares the remote and local commit first; an equal commit skips `fetch`.
- Deployment and the two recorded versions in `setup.toml` are transactional. A failed verification or uv sync rolls live files back.

## Interface and logs

Git, archive, and uv terminal output is captured through a PTY and shown in one scrollable installation log. Use Up/Down or Page Up/Page Down to inspect history. Installer messages and subprocess output are also written to `log/installer.log`; registered CDKs and common credential headers are redacted.

After a successful detached BAAS launch, the installer exits immediately. A launch failure remains visible and can be retried.

## Portable Python environment

The default package manager is uv. The managed uv executable, Python distributions, virtual environment, cache, credentials, XDG state, and temporary data all stay below the installation root (`toolkit/uv`, `.venv`, `tmp`). A custom `runtime_path` in `setup.toml` remains supported.

## Build and test

Use CMake 3.25+ with a C++20 compiler and vcpkg:

```console
cmake -S deploy/installer -B build/installer -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build build/installer --config Release
ctest --test-dir build/installer -C Release --output-on-failure
```

GitHub Actions builds Windows x64, Linux x64, macOS x64, and macOS arm64. Tag builds publish all four binaries and `SHA256SUMS` as GitHub Release assets.
