# C++ TUI Installer Design

## 1. Goal and scope

Replace the manually packaged Python installer entry point with a native C++ TUI installer that can be built and published by GitHub Actions for:

- Windows x86_64
- Linux x86_64
- macOS x86_64
- macOS arm64

The feature branch is based directly on `upstream/master`. The installer owns initial installation, updates, Python runtime and dependency preparation, OCR prebuild installation, configuration migration, launch, and diagnostics. The existing Python installer remains temporarily as a migration reference but is no longer the release entry point.

The work covers the installer failures collected in `Kiramei/baas-tauri#1`: unavailable Git/Gitee endpoints, download timeouts, missing requirements, corrupted Git metadata, OCR prebuild download/update failure, and version state being persisted before an update actually succeeds.

## 2. Non-goals

- Do not support the development repository source list (`MAIN_REPO_SRC_DEV`).
- Do not use `https://baas-cdn.kiramei.workers.dev/...`; it is known to be unusable.
- Do not replace Git installations with ZIP snapshots when MirrorChyan is not in use.
- Do not add broad test coverage or unrelated refactors.
- Do not store uv, Python, cache, temporary, or installer state outside the BAAS installation root when `runtime_path = "default"`.

## 3. Project layout and dependencies

The C++ project lives under `deploy/installer`:

```text
deploy/installer/
├── CMakeLists.txt
├── vcpkg.json
├── include/baas_installer/
├── src/
└── tests/
```

Components are split by responsibility: executable-relative paths, configuration and migration, source ranking, Git CLI, libgit2, MirrorChyan, downloads, repository coordination, transactional deployment, uv environment management, OCR placement, process launch, logging, and TUI presentation.

Dependencies:

- FTXUI for the terminal interface
- libcurl for HTTP requests, streaming downloads, timeouts, and range probes
- libgit2 as the fallback Git implementation
- toml++ for TOML parsing and editing
- nlohmann/json for MirrorChyan responses, rankings, caches, and transaction journals
- libarchive for ZIP and tar archive extraction
- OpenSSL for TLS and SHA-256 verification

Dependencies are resolved through a pinned vcpkg manifest. Release binaries use the appropriate static vcpkg triplet where supported.

## 4. Configuration ownership and migration

There is only one configuration file: `setup.toml` next to the installer executable. No `config.toml` is introduced.

If `setup.toml` does not exist, the TUI performs the first-run MirrorChyan question before creating it. If the user chooses MirrorChyan, the CDK is entered without echo, validated, and stored only after validation succeeds. The CDK is never written to logs.

The loader accepts both current and historical forms:

- Current tables: `[general]`, `[paths]`, `[python]`, and `[repositories]`
- Legacy tables: `[General]`, `[URLs]`, and `[Paths]`
- Historical aliases including `current_BAAS_version`, `current_BAAS_Cpp_version`, `current_baas_sha`, `current_baas_cpp_sha`, `runtime_path`, `BAAS_ROOT_PATH`, `TMP_PATH`, and `TOOL_KIT_PATH`

Current-form fields take precedence. Missing values are read from the legacy form, then from defaults. Unknown tables and keys are preserved. Saving synchronizes the current fields and the legacy compatibility view so both the old GUI and newer service code can read the result. The legacy `package_manager` value becomes `uv`.

In portable mode the persisted path values are relative:

```toml
[paths]
baas_root_path = "."

[python]
runtime_path = "default"

[General]
runtime_path = "default"
package_manager = "uv"

[Paths]
BAAS_ROOT_PATH = "."
```

All runtime paths are resolved from the actual executable directory, not the process working directory. Configuration writes use a sibling temporary file, flush, atomic replacement, and a last-known-good backup. Repository SHA fields are saved only after repository placement, OCR placement, validation, and dependency synchronization succeed.

## 5. Source lists, ranking, and fallback

### Main repository

The stable source candidates are derived from `baas-tauri/crates/baas-updater/src/constants.rs`:

1. GitHub upstream
2. Gitee mirror
3. GitCode mirror
4. v4 gh-proxy
5. v6 gh-proxy
6. cdn.gh-proxy.org
7. gh-proxy.org
8. gh.sevencdn.com
9. githubfast.com

`MAIN_REPO_SRC_DEV` and the custom `baas-cdn.kiramei.workers.dev` source are excluded.

### OCR repository

OCR uses `pur1fying/BAAS_Cpp_prebuild` and its corresponding Gitee and GitHub proxy candidates. The selected platform branch is:

- Windows x86_64: `windows-x64`
- Linux x86_64: `linux-x64`
- macOS x86_64: `macos-x64`
- macOS arm64: `macos-arm64`

### uv, CPython, and PyPI

uv binary, CPython download, and PyPI source candidates follow the stable lists in `baas-updater`, excluding the custom BAAS CDN. User-provided `source_list` values remain eligible and retain their configured ordering as the initial preference.

Each source family has an independent ranking persisted under `<root>/.baas-installer/source-ranking/`. Probing uses a short HEAD request and falls back to a byte-range GET when HEAD is not supported. Ranking records the exact URL set and is discarded if that set changes. Operational failures demote a source and continue with the next candidate. The TUI shows the failed URL, stage, and next fallback without exposing secrets.

## 6. Repository backends and update policy

An effective MirrorChyan CDK selects MirrorChyan for the main repository only. OCR remains Git-managed.

Without MirrorChyan, the main repository must be a real Git working tree. For each ranked URL, the backend order is:

1. Installed Git CLI
2. Bundled libgit2

Only after both backends fail for the current URL does the updater try the next URL. Git commands disable terminal prompts, credential UI, askpass, and interactive SSH. New clones and updates are shallow. Existing repositories use shallow fetch followed by a hard reset to the fetched commit only during the commit phase.

If Git metadata is absent or invalid, the installer prepares a fresh shallow clone in staging while preserving protected user data. This handles installations such as `D:\Amusement\BAAS_NEW`, whose main `.git` directory contains only `objects/` and is not a valid repository.

## 7. Parallel preparation and ordered deployment

The main repository and OCR repository are prepared concurrently but never independently committed to the final installation.

```text
load/migrate setup.toml
        |
        +---- prepare main repository or MirrorChyan package ----+
        |                                                        |
        +---- prepare OCR Git repository ------------------------+--> barrier
        |                                                        |
        +---- prepare uv/Python assets as dependencies allow ----+
                                                                 |
                                              deploy main repository
                                                                 |
                                              deploy OCR repository
                                      to core/ocr/baas_ocr_client/bin
                                                                 |
                                              validate required files
                                                                 |
                                              synchronize dependencies
                                                                 |
                                              persist SHAs and launch
```

A completed preparation task displays `ready; waiting for parallel task` until the barrier is satisfied. The commit phase always deploys the main repository first, then OCR into `<root>/core/ocr/baas_ocr_client/bin`.

For an existing Git repository, preparation may fetch objects but must not change the checked-out work tree. Before commit, the installer records old commits and a transaction journal. Git failures roll both repositories back to their old commits. MirrorChyan application backs up affected paths and records additions, modifications, and deletions so it can restore the previous installation. `setup.toml`, the installer executable, user configuration, and logs are protected.

Fresh-install failures remove only files owned by the incomplete transaction. Existing working files remain usable. Stale staging directories are recognized from their journal and safely cleaned or rolled back on the next launch.

## 8. OCR ownership

The C++ installer absorbs the desktop OCR prebuild installation and update responsibility currently implemented by `core/ocr/baas_ocr_client/server_installer.py`.

After successful OCR placement, it writes an installer-managed marker with the selected branch and commit. BAAS startup checks this marker and skips the Python network updater, preventing duplicate updates. Existing installations without the marker retain their current Python behavior until the C++ installer completes one successful OCR migration.

The final OCR executable and libraries must exist directly under `core/ocr/baas_ocr_client/bin`, with that directory remaining its own Git working tree in Git mode.

## 9. Portable uv and Python environment

When `runtime_path = "default"`, every uv-related path is under the installation root:

```text
<root>/.venv/
<root>/tmp/uv/
<root>/toolkit/uv/uv[.exe]
<root>/toolkit/uv/cache/
<root>/toolkit/uv/cpython/
<root>/toolkit/uv/python-cache/
<root>/toolkit/uv/python-bin/
<root>/toolkit/uv/tools/
<root>/toolkit/uv/tool-bin/
<root>/toolkit/uv/credentials/
<root>/toolkit/uv/xdg/{cache,config,data,bin}/
```

Every uv process receives explicit `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_CACHE_DIR`, `UV_PYTHON_BIN_DIR`, `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR`, `UV_CREDENTIALS_DIR`, `UV_PROJECT_ENVIRONMENT`, `XDG_CACHE_HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_BIN_HOME`, and platform temporary-directory variables. It also receives `UV_NO_CONFIG=1`, `UV_PYTHON_INSTALL_REGISTRY=0`, and `UV_VENV_RELOCATABLE=1`.

The installer downloads a platform-specific uv binary, uses uv to install the configured Python 3.9 release, creates `<root>/.venv` as relocatable, compiles the applicable requirements file to an installer-managed lock, and performs `uv pip sync`. A SHA-256 cache over the requirements input, generated lock, Python version, and PyPI URL skips unchanged dependency work. Missing requirements are detected before deployment is finalized.

Custom `runtime_path` values are preserved and bypass installer-managed uv/Python setup.

## 10. TUI and diagnostics

The first-run page asks whether MirrorChyan is available and validates the optional CDK. The main page shows repository, OCR, uv/Python, dependencies, deployment, and launch task groups with progress and concise logs.

Failures offer retry, Git fallback where applicable, and exit. Escape requests cancellation during preparation. Once a commit step starts, cancellation waits for the current atomic step or rollback rather than terminating mid-write.

Logs and crash diagnostics are written under `<root>/log/installer.log`. Download URLs and failure causes are recorded, but CDKs, credentials, and environment secrets are redacted.

## 11. Build and release automation

The branch starts from the current `upstream/master`. GitHub Actions builds with fixed runner labels:

- `windows-2025`, x86_64
- `ubuntu-24.04`, x86_64
- `macos-15-intel`, x86_64
- `macos-15`, arm64

Pull requests and `workflow_dispatch` build, run the focused tests, and upload temporary Actions artifacts. A manual input may explicitly request a Release for a supplied tag.

Pushing a `v*` tag builds all four targets, calculates SHA-256 hashes, creates or updates the matching GitHub Release, and uploads the executables plus `SHA256SUMS` as Release Assets. Windows keeps the compatible pattern `BlueArchiveAutoScript_<version>_win_x86_64.exe`; all other assets include OS and architecture. Release publishing uses `contents: write` and is idempotent for an existing tag Release.

## 12. Verification

Automated tests remain focused on the risky contracts:

- Legacy/current mixed `setup.toml` migration and unknown-field preservation
- Source ranking, URL-set invalidation, and source/backend fallback order
- Parallel barrier with main-before-OCR commit order
- Failed deployment rollback without premature SHA persistence
- Executable-relative and portable uv path calculation

End-to-end Windows migration uses a copy of `D:\Amusement\BAAS_NEW`; the original directory is never modified. The test must prove that the corrupt main Git repository is rebuilt, the old configuration is migrated, user data remains, OCR is in the required directory, uv replaces the managed pip environment, and BAAS launches.

The completed copy is then moved as a whole into `E:\tmp`. Verification runs uv path queries, the moved `.venv` interpreter, representative dependency imports, and BAAS startup. It also scans portable metadata and launch files for references to the old installation path. Success requires operation from the new location after the old copied location is absent.

Cross-platform build jobs prove compilation on all four targets. Runtime installation is exercised locally on Windows and through safe CI smoke tests that do not require a real MirrorChyan CDK.
