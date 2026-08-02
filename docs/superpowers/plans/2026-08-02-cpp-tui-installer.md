# C++ TUI Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform C++ TUI installer that migrates legacy BAAS installs, manages main and OCR repositories transactionally, and keeps a uv-based portable runtime inside the installation directory.

**Architecture:** A standalone CMake/vcpkg application under `deploy/installer` owns executable-relative paths, TOML migration, ranked source fallback, Git CLI/libgit2 operations, MirrorChyan, parallel preparation, main-then-OCR deployment, uv setup, TUI rendering, and launch. Repository SHAs are persisted only after deployment and dependency synchronization succeed.

**Tech Stack:** C++20, CMake, vcpkg, FTXUI, libcurl, libgit2, toml++, nlohmann/json, libarchive, OpenSSL, Catch2, GitHub Actions.

## Global Constraints

- Base: `upstream/master`; branch: `feat/cpp-tui-installer`.
- Only executable-adjacent `setup.toml`; never create `config.toml`.
- Preserve/synchronize legacy and current setup schemas and unknown fields.
- `runtime_path = "default"` means portable; all uv, Python, cache, temp, and state paths stay below the install root.
- Exclude `MAIN_REPO_SRC_DEV` and `baas-cdn.kiramei.workers.dev`.
- Main uses MirrorChyan when selected; otherwise each ranked URL uses Git CLI then libgit2. OCR always uses Git.
- Prepare main/OCR concurrently; deploy main first, then OCR to `core/ocr/baas_ocr_client/bin`.
- Publish four executables and SHA256SUMS to GitHub Releases for `v*` tags.
- Tests focus on migration, fallback, deployment/rollback, and portability.

---

### Task 1: CMake application skeleton and portable paths

**Files:**
- Create: `deploy/installer/CMakeLists.txt`
- Create: `deploy/installer/vcpkg.json`
- Create: `deploy/installer/include/baas_installer/paths.hpp`
- Create: `deploy/installer/src/paths.cpp`
- Create: `deploy/installer/src/main.cpp`
- Create: `deploy/installer/tests/test_paths.cpp`
- Modify: `deploy/installer/README.md`

**Interfaces:**
- Produces `InstallPaths::from_executable(path)` with `root`, `setup_toml`, `tmp_dir`, `toolkit_dir`, `uv_dir`, `venv_dir`, `logs_dir`, and `state_dir`.
- Produces `BlueArchiveAutoScript` and `baas-installer-tests` targets.

- [ ] Write a failing Catch2 test using `E:\\tmp\\BAAS\\BlueArchiveAutoScript.exe` and assert every path is rooted at `E:\\tmp\\BAAS`.
- [ ] Run `cmake --preset installer-debug && cmake --build --preset installer-debug && ctest --test-dir build/installer-debug -R paths --output-on-failure`; expect failure because targets are absent.
- [ ] Add C++20 CMake/vcpkg manifests and the minimal `InstallPaths` implementation based on the executable parent, never cwd.
- [ ] Re-run the focused test and a release build; expect PASS and one executable.
- [ ] Commit: `feat(installer): add C++ build skeleton`.

### Task 2: setup.toml compatibility and atomic save

**Files:**
- Create: `deploy/installer/include/baas_installer/config.hpp`
- Create: `deploy/installer/src/config.cpp`
- Create: `deploy/installer/tests/test_config.cpp`

**Interfaces:**
- `InstallerConfig load_config(const InstallPaths&)`
- `InstallerConfig parse_config(std::string_view)`
- `std::string render_config(const InstallerConfig&)`
- `void save_config_atomic(const InstallerConfig&, const InstallPaths&)`

- [ ] Write a failing test with legacy `[General]/[URLs]/[Paths]`, old SHA aliases, `runtime_path = "default"`, and a custom table; assert current/legacy output and unknown-field preservation.
- [ ] Run `ctest --test-dir build/installer-debug -R config --output-on-failure`; expect missing API failure.
- [ ] Implement lowercase-first precedence, legacy aliases, defaults, portable `"."` paths, `package_manager = "uv"`, and preserved TOML tree.
- [ ] Implement sibling `.new` write, flush, backup, atomic rename, and recovery on failure.
- [ ] Re-run config tests; expect PASS for mixed schema, unknown fields, and atomic save.
- [ ] Commit: `feat(installer): migrate legacy setup configuration`.

### Task 3: Source constants, ranking, and HTTP fallback

**Files:**
- Create: `deploy/installer/include/baas_installer/sources.hpp`
- Create: `deploy/installer/src/sources.cpp`
- Create: `deploy/installer/tests/test_sources.cpp`

**Interfaces:**
- `enum class SourceKind { MainGit, OcrGit, Uv, Cpython, Pypi }`
- `default_sources(kind, config)`
- `load_or_rank_sources(kind, paths, config, probe)`
- `SourceRanking::active_urls()` and `mark_failed(url)`

- [ ] Write a failing test proving the retired custom CDN and dev repo are absent, Gitee can outrank GitHub by measured latency, and a failed URL is demoted.
- [ ] Run the focused source test; expect missing API failure.
- [ ] Add approved main/OCR/uv/CPython/PyPI URLs, 5-second HEAD then range-GET probing, and JSON rankings under `.baas-installer/source-ranking`.
- [ ] Invalidate rankings when URL sets change and stop after three all-failed ranking cycles.
- [ ] Re-run source tests; expect PASS.
- [ ] Commit: `feat(installer): add ranked source fallback`.

### Task 4: Git CLI then libgit2 preparation

**Files:**
- Create: `deploy/installer/include/baas_installer/git_repository.hpp`
- Create: `deploy/installer/src/git_repository.cpp`
- Create: `deploy/installer/tests/test_git_repository.cpp`

**Interfaces:**
- `PreparedRepository prepare_repository(const RepositoryRequest&, GitExecutor&, SourceRanking&)`
- `GitExecutor` exposes CLI/libgit2 prepare, head, commit, and rollback.
- `PreparedRepository` records staging/target paths, old/new SHA, URL, backend, and replacement requirement.

- [ ] Write a failing fake-executor test asserting call order `cli:first-url, git2:first-url` before advancing URLs.
- [ ] Run focused test; expect missing API failure.
- [ ] Implement noninteractive shallow CLI clone/fetch and matching libgit2 operations with bounded timeouts.
- [ ] Detect invalid `.git`; prepare a clean staged replacement while preserving protected user paths.
- [ ] Re-run tests for fallback order, invalid metadata, and noninteractive environment; expect PASS.
- [ ] Commit: `feat(installer): prepare repositories with Git fallback`.

### Task 5: MirrorChyan staging and integrity

**Files:**
- Create: `deploy/installer/include/baas_installer/mirrorchyan.hpp`
- Create: `deploy/installer/src/mirrorchyan.cpp`
- Create: `deploy/installer/tests/test_mirrorchyan.cpp`

**Interfaces:**
- `validate_cdk(cdk, http)`
- `query_mirror_latest(cdk, current_sha, http)`
- `prepare_mirror_package(latest, paths, http)`
- `apply_mirror_package(package, journal)` / `rollback_mirror_package(journal)`

- [ ] Write a failing test that rejects a bad SHA-256 before any live file changes.
- [ ] Run focused test; expect missing API failure.
- [ ] Implement MirrorChyan status mapping, redacted CDK handling, timeouts, streamed download, digest verification, archive extraction, and change journal.
- [ ] Re-run tests for CDK states, digest rejection, and no pre-verification writes; expect PASS.
- [ ] Commit: `feat(installer): stage MirrorChyan main updates`.

### Task 6: Parallel prepare and transactional ordered deployment

**Files:**
- Create: `deploy/installer/include/baas_installer/deployment.hpp`
- Create: `deploy/installer/src/deployment.cpp`
- Create: `deploy/installer/tests/test_deployment.cpp`

**Interfaces:**
- `WorkflowResult install_or_update(config, paths, services, progress)`
- `commit_prepared(main, ocr, journal)`
- `rollback(journal)`

- [ ] Write a failing fake-services test asserting both prepares finish, then `commit-main`, `commit-ocr`; on OCR failure assert `rollback-ocr`, `rollback-main`, and unchanged SHAs.
- [ ] Run focused test; expect missing coordinator failure.
- [ ] Implement UUID staging under `tmp/installer`, concurrent main/OCR preparation, barrier, main-first/OCR-second placement, required-file validation, JSON journal, and reverse rollback.
- [ ] Protect installer executable, `setup.toml`, logs, and user configuration during corrupt-repository replacement.
- [ ] Re-run deployment tests; expect PASS.
- [ ] Commit: `feat(installer): deploy main and OCR transactionally`.

### Task 7: Fully portable uv/Python environment

**Files:**
- Create: `deploy/installer/include/baas_installer/uv_environment.hpp`
- Create: `deploy/installer/src/uv_environment.cpp`
- Create: `deploy/installer/tests/test_uv_environment.cpp`

**Interfaces:**
- `UvEnvironment make_uv_environment(paths, config)`
- Process specs for uv download, `python install`, relocatable `venv`, `pip compile`, `pip sync`, and cache cleanup.
- `requirements_unchanged(...)`

- [ ] Write a failing test asserting every UV/XDG/TMP value begins with the simulated moved root and flags include `UV_VENV_RELOCATABLE=1`, `UV_NO_CONFIG=1`, and `UV_PYTHON_INSTALL_REGISTRY=0`.
- [ ] Run focused test; expect missing API failure.
- [ ] Implement platform uv archives and all approved scoped directories under `toolkit/uv`, `.venv`, and `tmp/uv`.
- [ ] Add Python 3.9 install, requirements discovery, compile/sync, and SHA-256 cache; custom runtime bypasses managed setup.
- [ ] Re-run tests for portable paths, cache hit/miss, and custom-runtime skip; expect PASS.
- [ ] Commit: `feat(installer): manage portable uv runtime`.

### Task 8: FTXUI, launcher, logging, and OCR handoff

**Files:**
- Create: `deploy/installer/include/baas_installer/tui.hpp`
- Create: `deploy/installer/src/tui.cpp`
- Create: `deploy/installer/src/launcher.cpp`
- Modify: `deploy/installer/src/main.cpp`
- Modify: `core/ocr/baas_ocr_client/server_installer.py`
- Modify: `main.py`
- Create: `tests/core/ocr/test_server_installer_marker.py`

**Interfaces:**
- `run_tui(paths, services)`
- `ProgressSink::task(id, state, detail)`
- `launch_baas(paths, config)`
- Python `should_skip_installer_managed_update() -> bool`

- [ ] Write a failing Python test that creates `bin/.baas-installer-managed.json` and expects legacy OCR network update to be skipped.
- [ ] Run `pytest tests/core/ocr/test_server_installer_marker.py -q`; expect missing function failure.
- [ ] Implement first-run MirrorChyan choice, masked CDK, progress/waiting rows, retry/Git/exit, safe cancellation, root-local redacted logs, and root-relative launch.
- [ ] Write the OCR marker only after verified placement; make Python skip only when the marker is valid.
- [ ] Run Python and CTest suites plus `BlueArchiveAutoScript --help`; expect PASS and no user-directory files.
- [ ] Commit: `feat(installer): add TUI workflow and OCR handoff`.

### Task 9: Four-platform Actions builds and GitHub Releases

**Files:**
- Create: `.github/workflows/installer-release.yml`
- Modify: `deploy/installer/README.md`

**Interfaces:**
- Matrix: Windows x86_64, Linux x86_64, macOS x86_64, macOS arm64.
- Triggers: installer-related pull requests, `workflow_dispatch`, and `v*` tags.
- Assets: four named executables plus `SHA256SUMS`.

- [ ] Add workflow structure and run the repository YAML linter; expect failure until matrix/release steps are complete.
- [ ] Implement fixed runner labels, vcpkg cache, build, focused CTest, normalized asset names, checksums, and artifact uploads.
- [ ] Publish with `contents: write` only for `v*` or explicit manual release input; create/update the tag's GitHub Release idempotently and fail on missing files.
- [ ] Re-run YAML validation and inspect the event conditions; expect PASS.
- [ ] Commit: `ci: build and release C++ installer`.

### Task 10: Real migration and E:\tmp portability verification

**Files:**
- Create: `deploy/installer/tests/manual/migrate_legacy_sample.ps1`
- Create: `deploy/installer/tests/manual/verify_portable_move.ps1`
- Modify: `deploy/installer/README.md`

**Interfaces:**
- Migration script copies `D:\Amusement\BAAS_NEW` to a unique test directory and never modifies the source.
- Move script requires explicit `-ConfirmMove` and targets `E:\tmp\BAAS_NEW-portable`.

- [ ] Write assertions for migrated dual-schema TOML, valid main/OCR Git HEADs, OCR executable/marker, root-local uv paths, and moved venv Python.
- [ ] Run scripts in `-WhatIf`; expect no mutation and report legacy missing conditions.
- [ ] Implement safe copy, installer execution with launch disabled, post-migration checks, explicit move, uv path queries, dependency import, BAAS smoke launch, and old-path scan.
- [ ] Run the real migration on the copy, then move the verified copy to `E:\tmp`; expect all checks PASS after the old copied path is absent.
- [ ] Commit: `test(installer): verify legacy portable migration`.

## Final verification

- Run all CTest installer tests and the focused Python OCR marker test.
- Build the Windows Release executable locally.
- Validate workflow YAML and asset names.
- Audit each design requirement against code, tests, workflow, and migration output.
- Confirm the original `D:\Amusement\BAAS_NEW` was not modified.

### Task 11: Full-session TUI and local recovery verification

**Files:**
- Modify: `deploy/installer/CMakeLists.txt`
- Modify: `deploy/installer/include/baas_installer/tui.hpp`
- Modify: `deploy/installer/src/tui.cpp`
- Modify: `deploy/installer/src/main.cpp`
- Modify: `deploy/installer/include/baas_installer/process.hpp`
- Modify: `deploy/installer/src/process.cpp`
- Modify: `deploy/installer/src/git.cpp`
- Modify: `deploy/installer/tests/test_tui.cpp`
- Create: `deploy/installer/tests/test_process.cpp`
- Create: `deploy/installer/tests/manual/verify_local_migration.ps1`

**Interfaces:**
- `InstallerViewModel` owns setup, running, success, and failure screens plus thread-safe task rows.
- `run_tui(paths, install)` keeps one FTXUI event loop alive for the complete installer session.
- `run_process(spec)` captures child stdout/stderr into `<root>/log/installer.log` instead of inheriting the terminal.
- Windows startup enables UTF-8 input/output and virtual-terminal processing before FTXUI starts.

- [x] Add failing model tests for initial setup, parallel main/OCR progress, ordered deployment, uv progress, and terminal success/failure states.
- [x] Run the focused TUI test and verify it fails because the full-session view model API is absent.
- [x] Add a failing process test proving child output is captured and cannot reach the parent TUI stream.
- [x] Run the focused process test and verify the inherited-output implementation fails it.
- [x] Link FTXUI and implement one full-screen event loop with an in-TUI MirrorChyan form, task rows, aggregate progress, current detail, bounded log pane, retry, and exit controls.
- [x] Run installation work on a worker thread and post progress events back to FTXUI; represent unknown byte totals with a spinner and known totals with a determinate bar.
- [x] Configure Windows UTF-8/VT mode and compile source as UTF-8; keep Git, curl, tar, and uv output out of the console and append decoded diagnostic text to the root-local log.
- [x] Re-run focused tests and the full CTest suite; expect PASS with no direct progress printing remaining.
- [x] Build the Windows Release executable and copy `D:\Amusement\BAAS_NEW` to a fresh local D-drive test directory without changing the source.
- [x] Run the new installer against that fresh copy and assert exit code zero, main deployment, OCR placement, uv/Python locality, dependency sync, valid `setup.toml`, valid marker, and no paths outside the copied root.
- [x] Commit: `fix(installer): deliver full TUI and verified local install`.
