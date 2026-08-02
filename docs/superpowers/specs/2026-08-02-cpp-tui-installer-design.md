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

Components are split by responsibility: executable-relative paths, configuration and migration, source ranking, Git CLI, libgit2, MirrorChyan, downloads, repository coordination, transactional deployment, uv environment management, OCR placement, PTY-backed process execution, chunk decoding and redaction, process launch, localization, logging, and TUI presentation.

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

The main repository and OCR are separate update units. Each unit independently tries this backend order:

1. MirrorChyan when a validated CDK is configured
2. Installed Git CLI
3. Bundled libgit2

A failure in one unit does not force the other unit to use the same backend. For example, main may use MirrorChyan while OCR falls back to Git CLI. MirrorChyan uses the `BAAS_repo` resource for main and the platform-specific `BAAS_Cpp` resource for OCR.

### 6.1 No-op detection

The installer reads the expected SHA from `setup.toml`, but treats the actual local Git `HEAD` as authoritative when a valid working tree exists. It queries the remote branch tip with the lightweight equivalent of `git ls-remote` before fetching. If local `HEAD` equals the remote SHA, the unit is marked complete without `fetch`, clone, download, or work-tree mutation. If they differ, only then does preparation fetch the required objects. The libgit2 fallback follows the same list-heads-before-fetch rule.

For MirrorChyan, the installer queries the current resource version first. If the recorded local version is current, it skips the package download. The SHA/version fields in `setup.toml` are reconciled only after the complete workflow succeeds.

### 6.2 Git update and recovery

Git CLI is tried against the ranked source list first. Only after Git CLI exhausts every source does libgit2 try the same ranked source list. This preserves the global backend order MirrorChyan > installed Git CLI > bundled libgit2. Git commands disable terminal prompts, credential UI, askpass, and interactive SSH.

An existing valid repository is updated incrementally: preparation fetches the differing commit without changing the work tree, and deployment hard-resets the selected branch to that commit. The `.git` directory remains installed. A missing or invalid repository is cloned into staging and deployed as a full replacement while preserving protected user data. This handles installations such as `D:\Amusement\BAAS_NEW`, whose main `.git` directory contains only `objects/` and is not a valid repository.

Successful Git updates intentionally retain the original installer's hard-reset semantics: uncommitted code changes in the managed repository are discarded. A failed deployment restores the previous committed `HEAD`, but does not promise to reconstruct pre-existing uncommitted code edits. User configuration and protected data are outside this rule.

### 6.3 MirrorChyan package modes

Both main and OCR accept full and incremental MirrorChyan ZIP packages. Every package must pass the advertised SHA-256 check before extraction.

An incremental package must contain a valid `changes.json` with `deleted`, `added`, and `modified` lists. Paths are normalized after removing the archive's leading repository directory. Absolute paths, drive-qualified paths, `..` traversal, and any path resolving outside the target root are rejected. Every added or modified source must exist in staging before the deployment barrier.

A full package is unpacked to staging and deployed from the archive's first child directory. If an incremental request temporarily returns a full package, the installer retries the incremental request up to ten times with 500 ms between attempts, then accepts the validated full package returned by the final attempt. After a successful MirrorChyan deployment, the corresponding `.git` directory is removed transactionally. No Git metadata is removed before commit.

## 7. Parallel preparation and ordered deployment

The main repository and OCR repository are prepared concurrently but never independently committed to the final installation.

```text
load/migrate setup.toml
        |
        +---- prepare main: no-op, Git, or MirrorChyan package --+
        |                                                        |
        +---- prepare OCR: no-op, Git, or MirrorChyan package ---+--> barrier
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

Preparation never modifies the live installation. If either repository exhausts MirrorChyan, Git CLI, libgit2, and source fallbacks, the installer waits for the other task to stop safely, discards both prepared results, and does not enter deployment.

For an existing Git repository, preparation may fetch objects but must not change the checked-out work tree. Before commit, the installer records old commits and a transaction journal. Git deployment failures restore both repositories to their old committed states. MirrorChyan application backs up affected paths and records additions, modifications, deletions, and `.git` moves so it can restore the previous installation. `setup.toml`, the installer executable, user configuration, and logs are protected.

The commit phase always deploys main before OCR. If either deployment, validation, or uv synchronization fails, the transaction restores every committed unit and leaves the prior SHA/version fields intact. Both SHA/version fields are written together using the atomic configuration-save path only after repository validation and uv synchronization succeed.

Fresh-install failures remove only files owned by the incomplete transaction. Existing working files remain usable. Stale staging directories are recognized from their journal and safely cleaned or rolled back on the next launch.

## 8. OCR ownership

The C++ installer absorbs the desktop OCR prebuild installation and update responsibility currently implemented by `core/ocr/baas_ocr_client/server_installer.py`.

After successful OCR placement, it writes an installer-managed marker with the selected platform, backend, and commit or MirrorChyan version. BAAS startup checks this marker and skips the Python network updater, preventing duplicate updates. Existing installations without the marker retain their current Python behavior until the C++ installer completes one successful OCR migration.

The final OCR executable and libraries must exist directly under `core/ocr/baas_ocr_client/bin`. That directory remains its own Git working tree in Git mode and contains no `.git` directory in MirrorChyan mode.

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

## 10. Process capture, TUI, localization, and diagnostics

### 10.1 PTY process execution

Every user-visible external command runs through a pseudo-terminal: ConPTY on Windows and `forkpty`/`openpty` on Linux and macOS. This includes Git clone/fetch operations, uv, and any external archive or download helper. Output is consumed as arbitrary byte chunks instead of line-oriented stdout/stderr pipes, so tools retain terminal-aware progress output.

Small machine-readable probes such as Git `rev-parse`, `ls-remote`, and tool `--version` may use hidden captured pipes. They never write their raw output to the TUI and must remain non-interactive.

Each PTY stream has an incremental decoder that buffers incomplete UTF-8 sequences, removes ANSI CSI and OSC control sequences, applies backspace, replaces the current logical line on carriage return, and commits it on newline. A carriage-return progress update therefore replaces the final displayed line instead of flooding the history. The same normalized event stream feeds the TUI and disk log.

### 10.2 Unified TUI

The first-run page asks whether MirrorChyan is available and validates the optional CDK. During work, the interface remains in one full TUI view with static task states: waiting, checking, downloading, applying, complete, or failed. It shows percentages only when a real measurable total exists. There is no spinner, animated running glyph, dedicated Git panel, or normal-success page.

All process output appears in one large installation-log region. Each logical line is tagged with time, task, backend, and severity. The view follows the tail by default and supports scrolling through history. Git carriage-return progress is mixed into this same log using the replacement behavior above.

Failures offer retry, the next backend where applicable, and exit. Escape requests cancellation during preparation. Once a commit step starts, cancellation waits for the current atomic step or rollback rather than terminating mid-write.

After installation commits successfully, launch failure does not roll back the installed version. The TUI reports the launch failure and permits another launch attempt. As soon as BAAS starts successfully, the installer exits immediately without displaying a success screen or requiring an Exit action.

### 10.3 Chinese and English

Installer-owned strings live in a two-language message catalog. Windows selects the language from the system UI locale. Linux and macOS inspect `LC_ALL`, then `LC_MESSAGES`, then `LANG`. A case-insensitive locale whose normalized language prefix is `zh` selects Simplified Chinese, including both `zh-CN` and `zh_CN` forms; all other or unknown locales select English. There is no manual language selector. Native child-process output is retained, while installer prefixes, statuses, diagnostics, and actions use the selected language.

### 10.4 Secret handling and persistent logs

Logs and crash diagnostics are written under `<root>/log/installer.log`. A single redaction layer runs before any event reaches either the TUI or disk. It removes the known CDK, `cdk` query values, authorization headers, and cookie values. MirrorChyan requests use in-process libcurl, so the CDK is never placed in a child-process command line, PTY stream, or environment dump.

The operator-provided secret file outside the worktree is test input only. Tests receive its path through a local-only test setting and read it directly at runtime without printing the path or contents, copying, committing, embedding, or passing its contents on a command line. Test completion scans logs, diffs, and artifacts for the secret bytes and reports only pass/fail.

## 11. Build and release automation

The branch starts from the current `upstream/master`. GitHub Actions builds with fixed runner labels:

- `windows-2025`, x86_64
- `ubuntu-24.04`, x86_64
- `macos-15-intel`, x86_64
- `macos-15`, arm64

Pull requests and `workflow_dispatch` build, run the focused tests, and upload temporary Actions artifacts. A manual input may explicitly request a Release for a supplied tag.

Pushing a `v*` tag builds all four targets, calculates SHA-256 hashes, creates or updates the matching GitHub Release, and uploads the executables plus `SHA256SUMS` as Release Assets. Windows keeps the compatible pattern `BlueArchiveAutoScript_<version>_win_x86_64.exe`; all other assets include OS and architecture. Release publishing uses `contents: write` and is idempotent for an existing tag Release.

## 12. Failure handling and verification

### 12.1 Failure rules

- Preparation performs no live installation changes. Failure of one repository joins the other task safely and discards all staging work.
- MirrorChyan failure falls back only the affected repository through Git CLI, libgit2, and ranked sources. The installer fails only after that unit exhausts every permitted path.
- Packages are rejected before the barrier on checksum, manifest, missing-source, or path-safety failure.
- Deployment is journaled and ordered main then OCR. Any deployment, validation, or uv failure restores prior files and committed Git heads and does not persist new SHA/version state.
- Child processes are non-interactive, cancellable where safe, and subject to stage-specific timeouts.
- A BAAS launch failure leaves the successfully installed version committed. A successful launch causes immediate installer exit.

### 12.2 Automated tests

Automated tests cover these risky contracts:

- Legacy/current mixed `setup.toml` migration and unknown-field preservation
- Source ranking, URL-set invalidation, and per-repository backend fallback order
- A local Git `HEAD` equal to the remote branch performs no fetch, clone, or work-tree mutation
- A changed remote branch fetches incrementally, retains `.git`, and updates the stored SHA only after success
- Missing or corrupt Git metadata selects full clone; failed deployment restores the previous committed state
- Parallel preparation barrier with main-before-OCR deployment order
- MirrorChyan full and incremental packages for both main and OCR, including additions, modifications, deletions, checksum failure, manifest failure, path traversal rejection, and transactional `.git` removal
- Incremental-package request receiving a full package follows bounded retry and validated full-package fallback
- PTY decoding for split UTF-8, CSI/OSC sequences, carriage-return replacement, newline commit, and backspace
- Unified log tagging, tail following, scrolling, redaction, and identical normalized TUI/disk events
- Windows, Linux, and macOS locale detection; Chinese and English render snapshots; absence of spinner UI
- Successful launch exits immediately; launch failure remains in the TUI without rolling back installation
- Executable-relative and portable uv path calculation

### 12.3 Local integration and migration tests

Temporary local Git remotes prove both no-op and real incremental updates without depending on upstream movement. The no-op case must record that no fetch command was issued. The update case must prove concurrent preparation, main-before-OCR deployment, retained Git metadata, and atomic SHA persistence.

MirrorChyan integration tests use the operator-provided secret file only when explicitly configured. They exercise the real main and OCR resource APIs and downloads in disposable staging or an isolated installation copy. The tests verify full/incremental behavior where the service exposes those versions, package checksums, placement, and fallback. A final byte-for-byte secret scan covers the repository diff, installer logs, test output captured on disk, staging metadata, and build artifacts; neither the secret nor its local path is printed.

End-to-end Windows migration uses a fresh copy of `D:\Amusement\BAAS_NEW`; the original directory is never modified. The test must prove that corrupt Git metadata is rebuilt, the old configuration is migrated, user data remains, OCR is placed under `core/ocr/baas_ocr_client/bin`, uv replaces the managed pip environment, all uv data remains within the copied installation, and BAAS launches.

The completed copy is then moved as a whole into `E:\tmp`. Verification runs uv path queries, the moved `.venv` interpreter, representative dependency imports, and BAAS startup. It also scans portable metadata and launch files for references to the old installation path. Success requires operation from the new location after the old copied location is absent.

Cross-platform CI builds and runs focused tests on Windows x86_64, Linux x86_64, macOS x86_64, and macOS arm64. Runtime installation is exercised locally on Windows and through safe CI smoke tests that do not require a real MirrorChyan CDK.
