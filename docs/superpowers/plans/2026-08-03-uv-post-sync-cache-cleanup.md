# UV Post-Synchronization Cache Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove installation-local UV download caches after a real dependency compile and sync succeeds, without touching caches on a dependency-SHA no-op run.

**Architecture:** Add one focused cleanup function beside the UV environment construction code and call it only from the successful non-cache-hit tail of `sync_portable_uv`. The existing injected process executor remains the test seam; filesystem fixtures prove the cache lifecycle without mocking deletion.

**Tech Stack:** C++20, `std::filesystem`, CMake/CTest, FTXUI installer test harness.

## Global Constraints

- Remove only `toolkit/uv/cache`, `toolkit/uv/python-cache`, `toolkit/uv/xdg/cache`, and `tmp/uv`.
- Preserve UV, installed CPython, `.venv`, compiled requirements, source ranking, credentials/configuration, and `.baas-installer/dependencies-v1.sha256`.
- Clean only after successful `pip compile`, `pip sync`, managed marker persistence, and dependency SHA persistence.
- A dependency SHA cache hit must execute no UV command and must not alter existing cache contents.
- A failed compile or sync must retain caches for retry.
- Do not read or copy `.secret`.

---

### Task 1: Specify Cache Lifecycle With Failing Tests

**Files:**
- Modify: `deploy/installer/tests/test_uv_environment.cpp`

**Interfaces:**
- Consumes: `bool sync_portable_uv(const InstallPaths&, const InstallerConfig&, std::string&, ProcessObserver, UvProcessExecutor, UvSourceProbe)`
- Produces: Regression assertions for successful cleanup, cache-hit preservation, and sync-failure preservation.

- [ ] **Step 1: Create disposable cache sentinels before the first successful synchronization**

Add a helper near the existing path helpers:

```cpp
std::vector<std::filesystem::path> disposable_uv_caches(
    const baas_installer::InstallPaths& paths) {
    return {
        paths.toolkit_dir / "uv" / "cache",
        paths.toolkit_dir / "uv" / "python-cache",
        paths.toolkit_dir / "uv" / "xdg" / "cache",
        paths.tmp_dir / "uv",
    };
}

void seed_cache_sentinels(const baas_installer::InstallPaths& paths) {
    for (const auto& directory : disposable_uv_caches(paths)) {
        std::filesystem::create_directories(directory);
        std::ofstream(directory / "download.cache") << "cached";
    }
}
```

Call `seed_cache_sentinels(test_paths)` before the first `sync_portable_uv` invocation. After it returns true, assert every directory from `disposable_uv_caches(test_paths)` is absent, while the UV executable, managed Python, `.venv`, compiled requirements, source-ranking file, and dependency stamp still exist.

- [ ] **Step 2: Verify the new success assertion fails before production code changes**

Run:

```powershell
& 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build --config Release --target baas-installer-test-uv --parallel 8
& .\build\Release\baas-installer-test-uv.exe
```

Expected: FAIL with `successful dependency synchronization retained disposable UV caches`.

- [ ] **Step 3: Add cache-hit preservation coverage**

After the first successful run, recreate the four sentinels. Run the existing SHA-hit invocation and assert all sentinel files still exist, alongside the existing assertions that no commands or probes ran.

- [ ] **Step 4: Add synchronization-failure preservation coverage**

Create a fresh disposable fixture whose executor succeeds for `pip compile` and fails for `pip sync`. Seed all four cache sentinels, call `sync_portable_uv`, assert it returns false, and assert every sentinel remains.

- [ ] **Step 5: Run the UV test and confirm only the missing cleanup behavior is red**

Run the two commands from Step 2.

Expected: the success cleanup assertion fails; cache-hit and failure-preservation assertions pass.

### Task 2: Implement Required Post-Sync Cleanup

**Files:**
- Modify: `deploy/installer/src/uv_environment.cpp`
- Modify: `deploy/installer/README.md`
- Modify: `deploy/installer/README_CN.md`
- Test: `deploy/installer/tests/test_uv_environment.cpp`

**Interfaces:**
- Consumes: `UvEnvironment::cache_dir`, `InstallPaths::toolkit_dir`, `InstallPaths::tmp_dir`, and the existing `ProcessObserver`.
- Produces: Internal `bool clear_uv_download_caches(const InstallPaths&, const UvEnvironment&, std::string&)`.

- [ ] **Step 1: Add the minimal cleanup helper**

In the anonymous namespace of `uv_environment.cpp`, add:

```cpp
bool clear_uv_download_caches(const InstallPaths& paths, const UvEnvironment& environment,
                              std::string& error) {
    const std::array directories{
        environment.cache_dir,
        paths.toolkit_dir / "uv" / "python-cache",
        paths.toolkit_dir / "uv" / "xdg" / "cache",
        paths.tmp_dir / "uv",
    };
    for (const auto& directory : directories) {
        std::error_code remove_error;
        fs::remove_all(directory, remove_error);
        if (remove_error) {
            error = "dependency synchronization succeeded but UV cache cleanup failed for '" +
                    directory.generic_string() + "': " + remove_error.message();
            return false;
        }
    }
    return true;
}
```

Add `#include <array>`.

- [ ] **Step 2: Invoke cleanup only after durable dependency state**

At the end of `sync_portable_uv`, immediately after `save_dependency_stamp_atomic(...)` succeeds, call:

```cpp
if (!clear_uv_download_caches(paths, environment, error)) return false;
if (observer) observer("uv", "cache", "Disposable UV caches cleared\n");
```

Do not add cleanup to the SHA-hit branch or any error branch.

- [ ] **Step 3: Run the focused UV test and verify green**

Run the commands from Task 1 Step 2.

Expected: PASS.

- [ ] **Step 4: Document the lifecycle**

Update both installer READMEs to state that a real successful dependency resolution/sync clears package, Python-download, XDG, and temporary UV caches, while a dependency-SHA no-op run leaves caches untouched.

- [ ] **Step 5: Run the complete Release suite**

```powershell
& 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build --config Release --parallel 8
& 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build -C Release --output-on-failure
```

Expected: all 16 tests pass.

- [ ] **Step 6: Commit implementation**

```powershell
git add -- deploy/installer/src/uv_environment.cpp deploy/installer/tests/test_uv_environment.cpp deploy/installer/README.md deploy/installer/README_CN.md
git commit -m "fix(installer): clear uv caches after dependency sync"
```

### Task 3: Fresh Installation Verification and Delivery

**Files:**
- Verify only: a new `D:\Amusement\BAAS_SMOKE_20260803_006` installation directory
- Verify only: PR 539 checks and artifacts

**Interfaces:**
- Consumes: `build/Release/BlueArchiveAutoScript.exe` and the branch created by Tasks 1-2.
- Produces: Windows smoke evidence, pushed commit, and four-platform CI evidence.

- [ ] **Step 1: Run a new empty-directory Windows smoke installation**

Copy only the Release installer into the unused `_006` directory and run `--auto-exit --no-launch`. Assert the four disposable cache directories are absent, UV/CPython/`.venv`/dependency stamp exist, and main/OCR retain one shallow commit with no refs or unreachable objects.

- [ ] **Step 2: Run the no-op and rename checks**

Run the installer a second time and assert Git transfers, dependency probes, and UV commands are zero. Rename to `_006_RENAMED`, run again, and verify representative Python imports resolve inside the renamed root. Preserve the smoke directory pending explicit deletion approval.

- [ ] **Step 3: Push and monitor PR 539**

Push `feat/cpp-tui-installer`, wait for Windows, Linux, macOS x64, and macOS arm64 checks to succeed, and confirm the PR remains mergeable against `upstream/master`.

- [ ] **Step 4: Report exact evidence**

Report the commit, PR URL, test counts, cache paths removed, smoke directory retained, and four-platform CI status. Do not claim completion before all checks finish.
