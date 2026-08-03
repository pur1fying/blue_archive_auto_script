# Installer Full-Screen, Cache, and Download Ranking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a full-viewport bilingual installer that persists `setup.toml` immediately, safely survives directory moves, skips unchanged dependency work by SHA-256, ranks required downloads including CNB, and embeds the Windows icon.

**Architecture:** Keep orchestration in `workflow.cpp` and `uv_environment.cpp`, but extract reusable SHA-256 operations and dependency-state validation into focused modules. Keep source policy in `sources.cpp`, add injectable concurrent probes for deterministic tests, and make TUI rendering a pure function that can be rendered into a fixed FTXUI screen. Windows icon packaging is a platform-only resource plus a consumer-level extraction test.

**Tech Stack:** C++20, CMake 3.25, FTXUI, libcurl, libarchive, libgit2, nlohmann/json, CTest, Win32 resources, PowerShell integration scripts, GitHub Actions.

## Global Constraints

- Only executable-adjacent `setup.toml`; never create `config.toml`.
- Persist `setup.toml` before repository preparation or any network probe begins.
- Persist repository SHA/version fields only after deployment verification and dependency synchronization succeed.
- Keep uv, CPython, virtualenv, caches, source rankings, temporary data, and dependency stamps below the installation root.
- Use PTY chunk capture for user-visible external commands; in-process HTTP probes may report sanitized events directly.
- Exclude `MAIN_REPO_SRC_DEV` and every `baas-cdn.kiramei.workers.dev` URL.
- Preserve MirrorChyan > installed Git CLI > libgit2 repository fallback behavior.
- Do not print, commit, copy, or persist MirrorChyan credentials or remote-machine credentials.
- Preserve unrelated untracked `.vscode/`, `build/`, and `build-vcpkg/` content.

---

## File Structure

- `deploy/installer/include/baas_installer/digest.hpp`: SHA-256 byte/string/file interfaces shared by package verification and dependency state.
- `deploy/installer/src/digest.cpp`: dependency-free SHA-256 implementation moved from MirrorChyan.
- `deploy/installer/include/baas_installer/dependency_state.hpp`: dependency stamp, portable-environment validation, and relocation-repair interfaces.
- `deploy/installer/src/dependency_state.cpp`: canonical fingerprint generation, atomic stamp persistence, and managed `pyvenv.cfg` repair.
- `deploy/installer/include/baas_installer/sources.hpp`: source ranking and injectable probe contracts.
- `deploy/installer/src/sources.cpp`: CNB source policy and concurrent stable ranking.
- `deploy/installer/include/baas_installer/uv_environment.hpp`: uv synchronization interfaces and optional probe injection for tests.
- `deploy/installer/src/uv_environment.cpp`: demand-driven uv/CPython/PyPI ranking and dependency-cache orchestration.
- `deploy/installer/include/baas_installer/tui.hpp`: pure render interface and project identity constants.
- `deploy/installer/src/tui.cpp`: full-viewport setup/install renderers and restored header.
- `deploy/installer/src/workflow.cpp`: immediate configuration save and cache-hit progress protocol.
- `deploy/installer/src/installer.rc`: Windows executable icon resource.
- `deploy/installer/tests/test_digest.cpp`: standard SHA-256 vectors and file verification.
- `deploy/installer/tests/test_dependency_state.cpp`: cache stamp and moved-installation behavior.
- `deploy/installer/tests/test_sources.cpp`: CNB presence, retired-source absence, stable concurrent ranking.
- `deploy/installer/tests/test_uv_environment.cpp`: zero-command cache hits and demand-driven probe families.
- `deploy/installer/tests/test_workflow.cpp`: `setup.toml` exists before preparation and SHA durability.
- `deploy/installer/tests/test_tui.cpp`: full-screen rendering and bilingual identity content.
- `deploy/installer/tests/test_icon.cpp`: Windows consumer test for embedded icon extraction.
- `deploy/installer/tests/manual/verify_renamed_installation.ps1`: disposable whole-directory rename validation.
- `deploy/installer/CMakeLists.txt`: new modules, tests, and Windows resource compilation.
- `deploy/installer/README.md` and `deploy/installer/README_CN.md`: cache, relocation, source-ranking, and UI behavior.

---

### Task 1: Persist setup.toml at installation start

**Files:**
- Modify: `deploy/installer/src/workflow.cpp`
- Modify: `deploy/installer/tests/test_workflow.cpp`

**Interfaces:**
- Consumes: `save_config_atomic(const InstallerConfig&, const InstallPaths&)`.
- Produces: `install_or_update(...)` guarantees a durable starting configuration before either preparation callback runs.

- [ ] **Step 1: Write the failing workflow test**

Add a case whose first preparation callback asserts the file already exists and parses with the selected CDK while both repository SHAs still equal their previous values:

```cpp
bool setup_seen_before_prepare = false;
services.prepare_main = [&](auto&) {
    const auto persisted = baas_installer::load_config(paths);
    setup_seen_before_prepare = std::filesystem::exists(paths.setup_toml) &&
        persisted.mirrorc_cdk == "selected-cdk" &&
        persisted.main_sha == "old-main" && persisted.ocr_sha == "old-ocr";
    return unchanged_main();
};
```

Also return a preparation failure and assert `setup.toml` remains while the old SHA values are unchanged.

- [ ] **Step 2: Verify RED**

Run:

```powershell
cmake --build build --config Release --target baas-installer-test-workflow
ctest --test-dir build -C Release -R '^workflow$' --output-on-failure
```

Expected: FAIL because the configuration is currently saved only after uv synchronization.

- [ ] **Step 3: Implement the minimal early save**

After service validation and before constructing `InstallTransaction`, save the current configuration and convert write exceptions into `WorkflowResult`:

```cpp
try {
    save_config_atomic(config, paths);
} catch (const std::exception& exception) {
    return {false, exception.what()};
}
InstallTransaction transaction(paths);
```

Retain the existing final save after assigning both successful repository versions.

- [ ] **Step 4: Verify GREEN**

Run the workflow test and then all existing tests. Expected: workflow passes and no existing transactional SHA test regresses.

- [ ] **Step 5: Commit**

```powershell
git add deploy/installer/src/workflow.cpp deploy/installer/tests/test_workflow.cpp
git commit -m "fix(installer): persist setup before deployment starts"
```

---

### Task 2: Extract SHA-256 and implement dependency state

**Files:**
- Create: `deploy/installer/include/baas_installer/digest.hpp`
- Create: `deploy/installer/src/digest.cpp`
- Create: `deploy/installer/include/baas_installer/dependency_state.hpp`
- Create: `deploy/installer/src/dependency_state.cpp`
- Create: `deploy/installer/tests/test_digest.cpp`
- Create: `deploy/installer/tests/test_dependency_state.cpp`
- Modify: `deploy/installer/src/mirrorchyan.cpp`
- Modify: `deploy/installer/include/baas_installer/mirrorchyan.hpp`
- Modify: `deploy/installer/CMakeLists.txt`

**Interfaces:**
- Produces: `std::string sha256_bytes(std::string_view)`, `std::string sha256_file(const path&)`, and `bool verify_sha256(const path&, std::string_view)`.
- Produces: `DependencyState inspect_dependency_state(const InstallPaths&, const InstallerConfig&, const path& requirements)`.
- Produces: `bool repair_managed_venv_after_move(const InstallPaths&, const InstallerConfig&, std::string& error)`.
- Produces: `void save_dependency_stamp_atomic(const DependencyStamp&, const InstallPaths&)`.

- [ ] **Step 1: Write failing digest vectors**

Use literal, independently known SHA-256 values:

```cpp
if (sha256_bytes("") != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") return 1;
if (sha256_bytes("abc") != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") return 1;
```

Write `abc` to a temporary file and assert the file digest and verification result.

- [ ] **Step 2: Verify digest RED**

Configure/build the new target. Expected: compilation fails because the digest API does not exist.

- [ ] **Step 3: Move the compact SHA-256 implementation**

Move the existing `Sha256` implementation out of `mirrorchyan.cpp` into `digest.cpp`, expose the three interfaces, and update MirrorChyan to consume `digest.hpp`. Do not change package-verification behavior.

- [ ] **Step 4: Verify digest GREEN**

Run `ctest -R '^(digest|mirrorchyan)$'`. Expected: both tests pass.

- [ ] **Step 5: Write failing dependency-state tests**

Create a disposable root containing requirements, lock, managed marker, managed Python placeholder, virtualenv Python placeholder, and `pyvenv.cfg` with an old root:

```text
home = D:\Old\BAAS\toolkit\uv\cpython\cpython-3.9.0-windows-x86_64-none
version_info = 3.9.0
```

Assert:

- changing requirements bytes changes the input digest;
- portable-root name does not participate in the digest;
- a matching stamp reports `cache_hit == true`;
- a missing lock, interpreter, marker, or mismatched digest reports `cache_hit == false`;
- relocation repair rewrites the old managed path to the current root;
- an external custom-runtime path is never rewritten;
- stamp writes replace an existing stamp atomically.

- [ ] **Step 6: Verify dependency-state RED**

Expected: compilation fails because `dependency_state.hpp` does not exist.

- [ ] **Step 7: Implement canonical stamps and safe relocation repair**

Use a versioned record:

```text
schema=1
input_sha256=<64 lowercase hex>
lock_sha256=<64 lowercase hex>
python=3.9.0
runtime=portable
```

Build the input digest from explicit length-prefixed fields so concatenation is unambiguous. Treat a venv as installer-managed only when `.baas-installer-managed` matches the configured Python. Rewrite only `home`, `executable`, and `command` values that contain `/toolkit/uv/cpython/` or `\toolkit\uv\cpython\`; preserve every other line. Write both repaired config and stamp through sibling `.new` files followed by atomic replacement.

- [ ] **Step 8: Verify dependency-state GREEN**

Run `ctest -R '^(digest|dependency-state|mirrorchyan)$'`. Expected: all pass.

- [ ] **Step 9: Commit**

```powershell
git add deploy/installer/CMakeLists.txt deploy/installer/include/baas_installer/digest.hpp deploy/installer/src/digest.cpp deploy/installer/include/baas_installer/dependency_state.hpp deploy/installer/src/dependency_state.cpp deploy/installer/src/mirrorchyan.cpp deploy/installer/include/baas_installer/mirrorchyan.hpp deploy/installer/tests/test_digest.cpp deploy/installer/tests/test_dependency_state.cpp
git commit -m "feat(installer): add portable dependency state cache"
```

---

### Task 3: Add concurrent on-demand source ranking and CNB

**Files:**
- Modify: `deploy/installer/include/baas_installer/sources.hpp`
- Modify: `deploy/installer/src/sources.cpp`
- Modify: `deploy/installer/tests/test_sources.cpp`

**Interfaces:**
- Produces: `rank_sources(...)` probes candidates concurrently, retains original order for equal latency, and omits failed endpoints.
- Produces: uv source list including the complete CNB release base and CPython source list including the CNB download base.

- [ ] **Step 1: Write failing policy and concurrency tests**

Assert exact CNB membership and retired-source absence for every list. For concurrency, use an atomic active counter and a barrier-like probe:

```cpp
std::atomic<int> active{0};
std::atomic<int> max_active{0};
auto ranked = rank_sources({"slow", "fast", "failed"}, [&](const std::string& url) {
    const int current = ++active;
    max_active.store(std::max(max_active.load(), current));
    std::this_thread::sleep_for(std::chrono::milliseconds(40));
    --active;
    if (url == "failed") return -1LL;
    return url == "fast" ? 5LL : 25LL;
});
```

Assert `max_active > 1`, `fast` ranks first, and failed candidates are absent.

- [ ] **Step 2: Verify RED**

Run the sources test. Expected: CNB membership and concurrency assertions fail.

- [ ] **Step 3: Implement CNB policy and concurrent ranking**

Insert:

```text
https://cnb.cool/kiramei/baas-tauri/-/releases/download/uv-down
https://cnb.cool/kiramei/baas-tauri/-/releases/download
```

Use one `std::async(std::launch::async, ...)` per candidate, collect results in candidate order, then stable-sort successful results by latency.

- [ ] **Step 4: Verify GREEN**

Run the sources test repeatedly to prove deterministic ordering, then run the full suite.

- [ ] **Step 5: Commit**

```powershell
git add deploy/installer/include/baas_installer/sources.hpp deploy/installer/src/sources.cpp deploy/installer/tests/test_sources.cpp
git commit -m "feat(installer): rank CNB and fallback download sources"
```

---

### Task 4: Integrate cache hits, relocation, and demand-driven probes into uv

**Files:**
- Modify: `deploy/installer/include/baas_installer/uv_environment.hpp`
- Modify: `deploy/installer/src/uv_environment.cpp`
- Modify: `deploy/installer/tests/test_uv_environment.cpp`
- Modify: `deploy/installer/src/tui.cpp`
- Modify: `deploy/installer/src/localization.cpp`
- Modify: `deploy/installer/include/baas_installer/localization.hpp`

**Interfaces:**
- Consumes: dependency-state APIs from Task 2 and ranked sources from Task 3.
- Produces: injectable `UvSourceProbe` so tests observe which source families were benchmarked.
- Produces: cache-hit progress detail `dependencies unchanged; skipped` localized by the TUI.

- [ ] **Step 1: Write failing zero-work cache-hit test**

Prepare a valid managed environment and matching dependency stamp. Supply an executor and source probe that count calls. Assert:

```cpp
if (!sync_portable_uv(paths, config, error, observer, executor, probe)) return 1;
if (process_calls != 0 || probe_calls != 0) {
    std::cerr << "matching dependency stamp must perform no uv work or probes\n";
    return 1;
}
```

Move the root directory, rerun, and assert the same zero-call result plus a corrected `pyvenv.cfg`.

- [ ] **Step 2: Verify cache-hit RED**

Expected: existing implementation invokes at least four uv commands and the moved environment fails.

- [ ] **Step 3: Write failing demand matrix tests**

Use the injectable probe and executor to assert:

| State | uv probes | CPython probes | PyPI probes |
|---|---:|---:|---:|
| valid stamp | 0 | 0 | 0 |
| uv missing | >0 | only if Python also missing | >0 |
| uv present, Python missing | 0 | >0 | >0 |
| environment present, requirements changed | 0 | 0 | >0 |

Also assert source download/install attempts follow measured latency order and fall through after a simulated failure.

- [ ] **Step 4: Verify demand-matrix RED**

Expected: current fixed-order implementation does not probe and cannot satisfy the matrix.

- [ ] **Step 5: Implement HTTP probing and ranked uv download**

With libcurl, perform HEAD with a five-second timeout and follow redirects; retry with `Range: bytes=0-0` if HEAD is rejected. Join uv bases with the platform archive name before ranking. Keep the official Astral uv URL as a fallback and verify every downloaded archive using the pinned digest.

When libcurl is unavailable in the lightweight fallback build, preserve candidate order and continue using PTY-backed curl for the actual transfer; tests inject probes and do not require network.

- [ ] **Step 6: Implement managed Python presence and CPython ranking**

Skip `uv python install` when the managed CPython executable already exists. Otherwise rank base release endpoints, set `UV_PYTHON_INSTALL_MIRROR` for each candidate, and try `uv python install` in ranked order. Preserve the official source as final fallback.

- [ ] **Step 7: Implement dependency cache flow**

Order the sync function as:

```cpp
repair_managed_venv_after_move(paths, config, repair_error);
const auto state = inspect_dependency_state(paths, config, requirements);
if (state.cache_hit) {
    if (observer) observer("uv", "cache", "Dependency SHA unchanged; uv skipped\r");
    return true;
}
```

On a miss, rank PyPI, compile, sync, and atomically save the new stamp. Remove the unconditional `uv cache clean`. If a compiled lock matches its recorded digest but only the environment needs repair, reuse the lock without resolving again.

- [ ] **Step 8: Add localized cache/probe progress**

Add exact workflow details and message IDs for source testing, cache hit, dependency resolving, and dependency syncing. Keep raw child output unchanged while localizing installer-owned status text.

- [ ] **Step 9: Verify GREEN**

Run:

```powershell
cmake --build build --config Release --target baas-installer-test-uv baas-installer-test-localization baas-installer-test-tui
ctest --test-dir build -C Release -R '^(uv|dependency-state|sources|localization|tui)$' --output-on-failure
```

Then run the full suite. Expected: all pass and the cache-hit test records zero process/probe calls.

- [ ] **Step 10: Commit**

```powershell
git add deploy/installer/include/baas_installer/uv_environment.hpp deploy/installer/src/uv_environment.cpp deploy/installer/tests/test_uv_environment.cpp deploy/installer/src/tui.cpp deploy/installer/src/localization.cpp deploy/installer/include/baas_installer/localization.hpp
git commit -m "fix(installer): skip unchanged portable dependencies"
```

---

### Task 5: Render the TUI across the full viewport with restored identity

**Files:**
- Modify: `deploy/installer/include/baas_installer/tui.hpp`
- Modify: `deploy/installer/src/tui.cpp`
- Modify: `deploy/installer/include/baas_installer/localization.hpp`
- Modify: `deploy/installer/src/localization.cpp`
- Modify: `deploy/installer/tests/test_tui.cpp`
- Modify: `deploy/installer/tests/test_localization.cpp`

**Interfaces:**
- Produces: `ftxui::Element render_installer_view(const InstallerSnapshot&, Language, const TuiControls&)` or an equivalently pure renderer usable by both `run_tui` and tests.
- Produces: exact five-line ASCII title and localized welcome strings.

- [ ] **Step 1: Write failing fixed-screen render tests**

Render setup and installation snapshots into `ftxui::Screen::Create(Dimension::Fixed(100), Dimension::Fixed(40))`. Assert the four corners contain border cells rather than spaces, content reaches row 39 and column 99, and the log pane expands beyond the previous fourteen-line constant.

Assert the screen text contains all five title lines plus:

```text
Welcome to BlueArchive Auto Script!
欢迎使用蔚蓝档案自动脚本！
Developed by pur1fying
LICENSE: GPL-3.0
https://github.com/pur1fying/blue_archive_auto_script
Official QQ Group: 658302636
```

Each language snapshot must contain only its selected welcome line.

- [ ] **Step 2: Verify RED**

Expected: the centered minimum-size panel and old one-line title fail the viewport and identity assertions.

- [ ] **Step 3: Extract the renderer and fill the viewport**

Replace `center`, `GREATER_THAN`, and fixed visible-log padding with a full-width/full-height bordered `vbox`. Keep the header and task rows intrinsic, and give the unified log `flex` so it consumes the remaining rows. Determine visible log rows from the rendered region rather than a constant fourteen-line window.

- [ ] **Step 4: Restore project identity and localization**

Use the exact ASCII title supplied in the design and message-catalog entries for the two welcome strings. Render author, license, repository, and QQ group as stable dim footer/header metadata.

- [ ] **Step 5: Verify GREEN and inspect visually**

Run TUI/localization tests. Launch the local Release binary in a terminal at small and large dimensions; capture screenshots only if they contain no secret input. Confirm resize behavior, full borders, readable title, flexible logs, and no dedicated Git panel.

- [ ] **Step 6: Commit**

```powershell
git add deploy/installer/include/baas_installer/tui.hpp deploy/installer/src/tui.cpp deploy/installer/include/baas_installer/localization.hpp deploy/installer/src/localization.cpp deploy/installer/tests/test_tui.cpp deploy/installer/tests/test_localization.cpp
git commit -m "feat(installer): fill terminal with restored BAAS identity"
```

---

### Task 6: Embed and verify the Windows icon

**Files:**
- Create: `deploy/installer/src/installer.rc`
- Create: `deploy/installer/tests/test_icon.cpp`
- Modify: `deploy/installer/CMakeLists.txt`

**Interfaces:**
- Produces: Windows resource ID `IDI_BAAS_ICON` backed by `../logo.ico`.
- Produces: Windows-only CTest `icon` consuming the built installer path.

- [ ] **Step 1: Write the failing icon consumer test**

On Windows, accept the installer path as `argv[1]` and inspect the executable's own resource table rather than accepting the shell's default file icon:

```cpp
const HMODULE image = LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_AS_DATAFILE);
if (image == nullptr || FindResourceW(image, MAKEINTRESOURCEW(101), RT_GROUP_ICON) == nullptr) return 1;
FreeLibrary(image);
```

Register the test with `$<TARGET_FILE:BlueArchiveAutoScript>`. The pre-change executable should fail to expose a custom executable icon resource.

- [ ] **Step 2: Verify RED on Windows**

Build and run `ctest -R '^icon$'`. Expected: FAIL before the `.rc` file is linked.

- [ ] **Step 3: Add the Windows resource**

Create:

```rc
#define IDI_BAAS_ICON 101
IDI_BAAS_ICON ICON "../logo.ico"
```

Under `if(WIN32)`, enable RC language, add `src/installer.rc` to `BlueArchiveAutoScript`, build `test_icon.cpp`, and register the consumer test. Do not add RC to non-Windows targets.

- [ ] **Step 4: Verify GREEN**

Rebuild Release, run the icon test, and inspect the copied release asset with the same test. Expected: both expose one loadable icon.

- [ ] **Step 5: Commit**

```powershell
git add deploy/installer/src/installer.rc deploy/installer/tests/test_icon.cpp deploy/installer/CMakeLists.txt
git commit -m "fix(installer): embed BAAS icon in Windows release"
```

---

### Task 7: Documentation and local Windows integration

**Files:**
- Create: `deploy/installer/tests/manual/verify_renamed_installation.ps1`
- Modify: `deploy/installer/README.md`
- Modify: `deploy/installer/README_CN.md`

**Interfaces:**
- Produces: a disposable rename test that never mutates its source installation.

- [ ] **Step 1: Add the integration script**

Accept `-SourcePath`, `-TargetPath`, and `-InstallerPath`. Resolve all three absolute paths and reject a target outside its explicitly named parent. Copy the source, run the installer once, rename the complete target, run again with `--auto-exit --no-launch`, then assert:

- exit code zero;
- `setup.toml` existed before the first network log event;
- second-run log contains the dependency-cache hit;
- second run contains no `pip compile`, `pip sync`, or source-benchmark event;
- `.venv/pyvenv.cfg` contains the renamed root and not the prior disposable root;
- managed Python imports representative dependencies; and
- no managed uv path escapes the renamed root.

Delete only the validated disposable targets in `finally`; never alter `SourcePath`.

- [ ] **Step 2: Update English and Chinese README behavior**

Document immediate `setup.toml`, dependency-stamp location, no-op cache behavior, rename repair, CNB plus fallback ranking, and Windows icon packaging.

- [ ] **Step 3: Run fresh Windows verification**

Run both the lightweight and vcpkg/static Release builds and complete CTest suites. Then run the migration and rename scripts against a fresh copy of `D:\Amusement\BAAS_NEW`. Expected: cache miss on first install, cache hit after rename, successful dependency import, and successful BAAS launch.

- [ ] **Step 4: Scan for secret leakage**

Scan tracked diff, installer logs, build metadata, and disposable outputs for known secret candidates without printing candidate values. Report only counts and pass/fail. Confirm `.secret` and remote credentials are absent from `git status`, `git diff`, and artifacts.

- [ ] **Step 5: Commit**

```powershell
git add deploy/installer/tests/manual/verify_renamed_installation.ps1 deploy/installer/README.md deploy/installer/README_CN.md
git commit -m "docs(installer): document cached portable migration"
```

---

### Task 8: Linux host, CI, PR, and release-asset verification

**Files:**
- Modify only if a real platform defect is found: `.github/workflows/installer-release.yml` and the smallest affected installer source/test files.

**Interfaces:**
- Consumes: authorized Linux test directory `/home/kiramei/Workspace/Tests/BAAS`.
- Produces: fresh Linux integration evidence, green four-platform CI, and updated PR branch.

- [ ] **Step 1: Verify SSH without exposing credentials**

Try existing key/agent authentication first with non-interactive SSH options. If password authentication is required, supply it only through a transient process environment and an askpass mechanism that contains no secret literal; do not place it in a command argument, file, log, shell history, or repository.

- [ ] **Step 2: Prepare the authorized Linux test directory**

Resolve the remote target exactly, verify it is `/home/kiramei/Workspace/Tests/BAAS`, and restrict any replacement or cleanup to that directory. Upload the Linux installer and test fixtures, preserving any unrelated remote content unless it belongs to the disposable installer test.

- [ ] **Step 3: Run Linux integration**

Build/test on the host when toolchains are available, then run first install and renamed-directory cache verification. Assert Linux selects `requirements-linux.txt`, all uv/XDG/temp paths remain under the moved root, unchanged dependencies skip uv work, and the OCR server resides under `core/ocr/baas_ocr_client/bin`.

- [ ] **Step 4: Run final local verification**

Run `git diff --check`, both local build/test matrices, the Windows migration/rename test, icon extraction, and secret scans from fresh outputs. Record exact pass counts and commands.

- [ ] **Step 5: Push and inspect PR CI**

Push `feat/cpp-tui-installer`, verify the PR still targets `upstream/master`, and wait for Windows x64, Linux x64, macOS x64, and macOS arm64 jobs. Fix only evidence-backed failures with a failing regression test first.

- [ ] **Step 6: Verify artifacts and review state**

Confirm the supported Release artifacts remain Windows x64, Linux x64, and macOS arm64; verify the Windows artifact contains the icon. Check that no new unresolved review thread remains and that a PR event does not publish a GitHub Release.

- [ ] **Step 7: Commit any platform-only fixes and report**

If no fix is required, do not create an empty commit. Otherwise commit the focused regression and implementation together. Report commits, tests, CI run URL, integration outcomes, and secret-scan pass/fail without printing credentials.
