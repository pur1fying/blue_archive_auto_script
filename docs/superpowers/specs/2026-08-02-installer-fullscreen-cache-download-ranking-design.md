# Installer Full-Screen, Dependency Cache, and Download Ranking Design

## 1. Scope

This increment improves the native C++ installer on `feat/cpp-tui-installer` without changing its repository deployment model. It covers seven user-visible requirements:

1. Fill the current terminal viewport with the TUI.
2. Skip dependency resolution and synchronization when a verified SHA-256 dependency stamp is unchanged.
3. Replace the title and restore the historical welcome, author, license, repository, and community information.
4. Keep a managed installation usable after its containing directory is renamed or moved.
5. Create `setup.toml` as soon as installation begins.
6. Embed the project icon in the Windows executable.
7. Benchmark uv, CPython, and PyPI sources only when the corresponding network operation is required, including the supplied CNB mirrors.

The existing constraints remain in force: `setup.toml` is the only configuration file, all managed uv data stays below the installation root, child command output is captured through PTY chunks, `MAIN_REPO_SRC_DEV` is excluded, and `baas-cdn.kiramei.workers.dev` is never used.

## 2. Confirmed root causes

### 2.1 Repeated dependency work

The current implementation runs `uv python install`, `uv pip compile`, and `uv pip sync` on every invocation. It then runs `uv cache clean`, deleting the artifacts that would otherwise accelerate later work. Although the earlier design mentioned a requirements cache, no dependency stamp is implemented.

### 2.2 Rename failure

A real renamed-installation probe reproduced the failure. The managed `.venv/pyvenv.cfg` retained the old absolute CPython `home` path. The installer considered the environment reusable because it checked only `pyvenv.cfg` existence and a marker containing the Python version. `uv pip sync` then rejected the broken environment.

The fix must repair relocatable metadata before deciding whether dependency work can be skipped. Merely retrying uv or recreating every environment would hide the cause and discard otherwise valid installations.

### 2.3 Slow downloads

The current uv path tries sources in a fixed order. Source ranking helpers exist but are not connected to uv, CPython, or PyPI setup. The supplied CNB release assets are not in the source lists.

## 3. TUI layout and identity

`ScreenInteractive::Fullscreen()` remains the terminal backend. The renderer will stop centering a minimum-sized panel and instead return a bordered element constrained to the full available width and height. The setup page and installation page both fill the viewport. The installation log remains the flexible region and receives all remaining vertical space.

The header is exactly:

```text
    ____  ___    ___   _____
   / __ )/   |  /   | / ___/
  / __  / /| | / /| | \__ \
 / /_/ / ___ |/ ___ |___/ /
/_____/_/  |_/_/  |_/____/
```

The selected system language controls the welcome line:

- English: `Welcome to BlueArchive Auto Script!`
- Simplified Chinese: `欢迎使用蔚蓝档案自动脚本！`

The header also restores these stable project details from the historical installer:

- `Developed by pur1fying`
- `LICENSE: GPL-3.0`
- `https://github.com/pur1fying/blue_archive_auto_script`
- `Official QQ Group: 658302636`

These details are visible in both supported languages. Tests render a fixed terminal-sized screen and verify that the outer border reaches all four edges, the five title rows are present, and the localized welcome and metadata are visible.

## 4. Immediate configuration durability

After the user presses Start, the selected MirrorChyan setting is copied into the in-memory configuration and `save_config_atomic` runs before repository preparation, source probes, or downloads. This guarantees that `setup.toml` appears immediately.

The early save retains the last known successful repository SHA values. A later successful installation atomically saves both new repository versions. If deployment fails, file rollback restores managed files while the newly created or updated `setup.toml` remains, containing the selected settings and old SHA values. A configuration write failure stops installation before any live deployment work.

## 5. Dependency stamp and relocation repair

### 5.1 Stamp format

Successful dependency synchronization writes `<root>/.baas-installer/dependencies-v1.sha256`. The fingerprint is SHA-256 over a canonical byte sequence containing:

- dependency-stamp schema version `1`;
- the selected platform;
- the complete applicable requirements file bytes;
- configured Python version;
- portable or custom runtime mode;
- custom interpreter path when custom mode is used; and
- the generated lock file digest.

The persisted record contains the input digest and lock digest. Paths for a portable runtime are not included, so moving the installation does not invalidate the stamp. The record is written atomically only after synchronization succeeds.

### 5.2 Cache-hit validation

Before invoking uv, the installer checks:

- the requirements and lock files exist;
- their freshly computed digests match the stamp;
- the configured runtime mode and Python version match;
- for portable mode, the managed marker, virtual-environment Python executable, managed CPython directory, and `pyvenv.cfg` exist; or
- for custom mode, the configured interpreter exists.

If all checks pass, dependency resolution and synchronization are skipped. The TUI and log explicitly report a dependency-cache hit. No uv, CPython, PyPI probe, or cache cleanup command runs.

### 5.3 Relocation repair

For an installer-managed environment, `pyvenv.cfg` is parsed before cache validation. When its `home`, `executable`, or `command` fields point below an old installation root, the old managed prefix is replaced with the current managed CPython path and the file is atomically rewritten. Unrelated external interpreter paths are never rewritten.

After repair, the virtual-environment interpreter is checked for existence. A valid dependency stamp can then skip uv completely. If repair cannot produce a valid environment, the normal cache-miss path recreates the virtual environment and synchronizes from the existing compiled lock where safe.

### 5.4 Cache miss

On a missing or different stamp, the installer:

1. ensures uv exists;
2. ensures the requested managed CPython exists, when portable mode is selected;
3. creates or repairs the virtual environment;
4. benchmarks PyPI candidates;
5. compiles the requirements file;
6. synchronizes the compiled lock; and
7. writes the new stamp.

The installer no longer runs `uv cache clean` after success. Operational failures do not update the stamp.

## 6. On-demand source benchmarking

Source benchmarking uses concurrent short HTTP probes and stable latency ordering. HEAD is attempted first, followed by a byte-range GET when HEAD is unsupported. Probes use in-process libcurl and report sanitized progress through the unified installer log; they do not start child commands or expose credentials.

Benchmarking is strictly demand-driven:

- uv candidates are probed only when the uv executable is missing;
- CPython candidates are probed only when the requested managed Python is missing;
- PyPI candidates are probed only when the dependency stamp is invalid;
- a complete dependency-cache hit runs none of these probes.

The ranked list is tried in order. A download or install failure immediately falls through to the next ranked candidate. Actual external uv and curl operations continue to run through the PTY-backed process runner so their chunked progress remains complete.

### 6.1 uv candidates

Each base URL is joined with the platform uv archive filename. The supplied CNB source is added ahead of the existing stable fallbacks:

```text
https://cnb.cool/kiramei/baas-tauri/-/releases/download/uv-down
```

The downloaded archive must still match the pinned official uv 0.5.11 SHA-256 before extraction, regardless of which mirror wins.

### 6.2 CPython candidates

The supplied CNB Python release base is added ahead of the existing stable fallbacks:

```text
https://cnb.cool/kiramei/baas-tauri/-/releases/download
```

It is passed to uv as `UV_PYTHON_INSTALL_MIRROR`, preserving uv's expected release-tag suffix. GitHub, Gitee, and supported GitHub proxy bases remain fallbacks. A source that lacks the requested platform asset simply fails its probe or install and is skipped.

### 6.3 PyPI candidates

Configured sources retain priority as candidates but participate in the same benchmark. The default Aliyun, Douban, Huawei, Tencent, 163, Tsinghua, USTC, and official PyPI sources remain available. No ranking or network access occurs on a dependency-cache hit.

## 7. Windows executable icon

A Windows resource script embeds `deploy/installer/logo.ico` as the executable's primary icon. CMake enables and compiles the resource only on Windows, so Linux and macOS builds remain unchanged. A Windows-only integration test calls the Win32 icon extraction API on the built installer and fails when no embedded icon can be loaded.

## 8. Testing and release verification

Test-driven implementation adds focused failures before each production change:

- rendered TUI consumes the complete terminal viewport;
- title, localized welcome, author, license, repository, and QQ group render correctly;
- `setup.toml` exists before either repository preparation callback begins;
- a matching dependency stamp produces zero uv commands and zero source probes;
- a changed requirements byte invalidates the stamp and runs compile/sync;
- a moved managed environment rewrites only old managed paths and then hits the cache;
- missing uv, CPython, and invalid dependencies trigger only their respective benchmark families;
- CNB candidates are present while the retired BAAS CDN remains absent;
- source probes run concurrently and downloads follow ranked order;
- the Windows release executable exposes the embedded icon.

Fresh verification includes both existing local Windows builds, the complete CTest suite, a disposable migration, and a whole-directory rename followed by dependency imports and BAAS launch. Linux verification uses the authorized test directory `/home/kiramei/Workspace/Tests/BAAS`; connection credentials remain runtime-only and must not be written to files, logs, shell history, commits, process arguments, or artifacts. Cross-platform GitHub Actions remains required before completion.

## 9. Security and rollback

- MirrorChyan CDKs and external test credentials remain secret and use the existing redaction boundary.
- The retired BAAS CDN is rejected by tests across every source family.
- Downloaded uv archives retain pinned digest verification.
- Dependency stamps are never written until the matching environment is synchronized successfully.
- Relocation repair uses atomic replacement and is limited to an installer-managed virtual environment.
- Early `setup.toml` creation does not authorize early repository SHA persistence.
- Existing untracked worktree files and external installations remain outside commits.
