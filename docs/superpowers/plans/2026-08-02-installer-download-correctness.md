# Installer Download Correctness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make repository and runtime acquisition fast, cached, shallow, bounded, leak-free, and correctly presented in the full-screen TUI.

**Architecture:** Keep MirrorChyan and Git as independent repository backends. Add an installation-local source-ranking store shared by Git and runtime downloads, replace partial Git clones with a single depth-one fetch, and attach Git compaction plus staging cleanup to the transaction lifecycle. Accept portable UV by executable behavior instead of a fixed digest, and render the approved Unicode banner through FTXUI's display-width centering.

**Tech Stack:** C++20, FTXUI 6.1.9, nlohmann/json 3.11.3, Git CLI/libgit2, libcurl, CMake/CTest.

## Global Constraints

- `setup.toml` is the only installer configuration file; do not introduce `config.toml`.
- All state and caches stay below the executable-relative installation root; source rankings live at `.baas-installer/source-ranking-v1.json`.
- MirrorChyan behavior stays independent; Git work starts only after its repository preparation explicitly falls back to Git.
- Main and OCR preparation stay concurrent, with OCR deployed only after main; OCR lives at `core/ocr/baas_ocr_client/bin`.
- Every source measurement launches all candidates in that category concurrently; a candidate that has not returned a valid result in ten seconds is unavailable for that run.
- Git measurement latency is time-to-valid-remote-SHA, and that SHA is reused without a duplicate query.
- Git full installs and updates use depth one and retain only the current commit after successful transaction completion.
- Portable UV archives have no fixed SHA verification; acceptance requires extraction and a successful installed `uv --version`.
- Preserve unrelated `.vscode/`, `build/`, and `build-vcpkg/` worktree contents.

---

### Task 1: Installation-local source ranking store

**Files:**
- Modify: `deploy/installer/include/baas_installer/sources.hpp`
- Modify: `deploy/installer/src/sources.cpp`
- Modify: `deploy/installer/tests/test_sources.cpp`

**Interfaces:**
- Consumes: `SourceKind`, candidate URL lists, and a probe returning a `RankedSource` observation.
- Produces: `source_kind_name(SourceKind)`, `load_source_ranking(path, kind, candidates)`, `save_source_ranking(path, kind, ranking)`, and `rank_sources(candidates, probe, 10s)` with fields `url`, `latency_ms`, `failures`, `commit`, `preferred`, and `available`.

- [ ] **Step 1: Write failing persistence and concurrency tests**

Extend `test_sources.cpp` so two category-specific rankings are concurrently saved to one JSON file, reloaded independently, and remain intact after the containing installation directory is renamed. Add a timed probe fixture whose three callbacks increment an atomic active count, sleep for 30 ms, and return literal latencies; assert `max_active > 1`, all three candidates were invoked, unavailable candidates sort after available candidates, and candidate-list changes invalidate a loaded ranking.

```cpp
const auto main = load_source_ranking(cache, SourceKind::MainGit, {"fast", "slow"});
const auto ocr = load_source_ranking(cache, SourceKind::OcrGit, {"ocr"});
if (main.size() != 2 || ocr.size() != 1 || !main.front().preferred) return 1;
```

- [ ] **Step 2: Run the source test and verify RED**

Run: `ctest --test-dir build-vcpkg -C Release -R "^sources$" --output-on-failure`

Expected: compilation fails because the category-aware cache APIs and observation fields do not exist.

- [ ] **Step 3: Implement the category-aware atomic JSON store**

Use `nlohmann::json` to read/write a schema containing `schema_version: 1` and an object keyed by `main_git`, `ocr_git`, `uv`, `cpython`, and `pypi`. Guard the complete read-modify-write operation with one process-local mutex because main and OCR write concurrently. Write `<path>.new`, flush/close it, then replace the target atomically. Treat malformed or mismatched candidate sets as a cache miss. Keep unavailable observations in JSON but exclude them from the returned real-attempt list for that run.

- [ ] **Step 4: Run focused and full source tests**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-sources && ctest --test-dir build-vcpkg -C Release -R "^sources$" --output-on-failure`

Expected: source test passes with all candidate probes concurrent and both category entries preserved.

- [ ] **Step 5: Commit the source store**

```powershell
git add -- deploy/installer/include/baas_installer/sources.hpp deploy/installer/src/sources.cpp deploy/installer/tests/test_sources.cpp
git commit -m "feat(installer): persist concurrent source rankings"
```

### Task 2: Bounded hidden process execution

**Files:**
- Modify: `deploy/installer/src/process.cpp`
- Modify: `deploy/installer/tests/test_process.cpp`

**Interfaces:**
- Consumes: existing `ProcessSpec::timeout` for both hidden and PTY subprocesses.
- Produces: `run_process(ProcessSpec)` that terminates a timed-out child with exit code `124` on Windows, Linux, and macOS while preserving captured output.

- [ ] **Step 1: Write a failing hidden-timeout test**

Add a child test mode that emits `started`, blocks longer than 500 ms, and would create a marker only after the delay. Execute it with a 100 ms `ProcessSpec::timeout`; assert elapsed time is below 400 ms, exit code is `124`, output contains `started`, and the late marker is absent.

- [ ] **Step 2: Run the process test and verify RED**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-process && ctest --test-dir build-vcpkg -C Release -R "^process$" --output-on-failure`

Expected: hidden execution waits for the child and violates the elapsed-time assertion.

- [ ] **Step 3: Implement timeout-aware hidden subprocess capture**

On Windows, read the output pipe on a thread and wait on the process handle with `spec.timeout`; terminate with code 124 on timeout before joining the reader. On Unix, replace `popen` for this path with `fork`, redirected pipes, nonblocking reads, `waitpid(WNOHANG)`, and `poll`, mirroring the PTY timeout loop without allocating a pseudo-terminal. Preserve environment overrides and working directory behavior.

- [ ] **Step 4: Verify hidden and PTY process behavior**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-process && ctest --test-dir build-vcpkg -C Release -R "^process$" --output-on-failure`

Expected: both timeout and existing PTY chunk tests pass.

- [ ] **Step 5: Commit bounded execution**

```powershell
git add -- deploy/installer/src/process.cpp deploy/installer/tests/test_process.cpp
git commit -m "fix(installer): enforce hidden process timeouts"
```

### Task 3: Parallel remote-SHA selection and depth-one Git repositories

**Files:**
- Modify: `deploy/installer/include/baas_installer/git.hpp`
- Modify: `deploy/installer/src/git.cpp`
- Modify: `deploy/installer/src/main.cpp`
- Modify: `deploy/installer/tests/test_git.cpp`
- Modify: `deploy/installer/tests/test_workflow.cpp`

**Interfaces:**
- Consumes: source candidates, `SourceKind::MainGit` or `SourceKind::OcrGit`, `.baas-installer/source-ranking-v1.json`, target revision, and the existing observer.
- Produces: `GitRemoteHead { source, commit, latency_ms, available }`, cached `select_git_remote(...)`, single-fetch `prepare_git_repository(...)`, and `finalize_git_repository(path, backend, error)`.

- [ ] **Step 1: Write failing Git behavior tests**

Use real local bare repositories plus an injected remote-head probe to assert all uncached candidates become active concurrently, a 10,000 ms timeout is supplied, the selected probe SHA is not queried again, and cache reuse probes only the preferred source. Record visible Git commands through an injected executor and assert fresh preparation contains exactly one `fetch`, includes `--depth=1` and `--no-tags`, contains no `clone` and no `--filter=blob:none`, and checks out locally.

Extend the real repository fixture to create three commits, prepare/update/finalize, then assert:

```cpp
command({"git", "-C", live.string(), "rev-parse", "--is-shallow-repository"}); // output true
command({"git", "-C", live.string(), "rev-list", "--count", "HEAD"});          // output 1
```

Add a workflow fixture where MirrorChyan-style prepared results succeed and counters prove no Git selector or finalizer callback ran.

- [ ] **Step 2: Run Git/workflow tests and verify RED**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-git baas-installer-test-workflow && ctest --test-dir build-vcpkg -C Release -R "^(git|workflow)$" --output-on-failure`

Expected: tests fail because selection is sequential, partial clone is present, and no finalizer exists.

- [ ] **Step 3: Implement cached parallel SHA selection**

Implement each Git probe as `git ls-remote <source> <revision>` using a hidden `ProcessSpec` with a ten-second timeout. Validate exactly 40 hexadecimal characters before marking the result available. On cache miss, execute every candidate probe through `rank_sources` concurrently and persist observations; on cache hit, probe only the preferred source, falling back to a concurrent round over remaining candidates if it fails. Reuse the selected observation's SHA for local comparison and fetch.

- [ ] **Step 4: Replace partial clone with one shallow fetch**

For Git CLI full preparation, run `git init <staging>`, then one visible `git -C <staging> fetch --depth=1 --no-tags <source> <revision>`, followed by local `checkout --detach --force FETCH_HEAD`. For existing repositories, run the same one shallow fetch against the live repository without changing its worktree until apply. If Git CLI is unavailable, use libgit2 depth-one clone into staging for both full and update fallback so replacing the managed repository cannot retain historical objects.

- [ ] **Step 5: Implement post-success one-layer finalization**

For Git CLI, detach HEAD at the prepared commit, delete installer-created refs, expire all reflogs, and run `git gc --prune=now`; verify the repository remains shallow and `rev-list --count HEAD` is one. Register finalization only from the Git apply lambda in `main.cpp`; do not execute it for MirrorChyan results. Preserve the previous commit until transaction success so rollback can reset it.

- [ ] **Step 6: Run focused tests and inspect command traces**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-git baas-installer-test-workflow && ctest --test-dir build-vcpkg -C Release -R "^(git|workflow)$" --output-on-failure`

Expected: tests pass; each changed repository has one fetch and one reachable commit, unchanged repositories have one SHA query and no fetch, and MirrorChyan fixtures invoke no Git operations.

- [ ] **Step 7: Commit Git acquisition changes**

```powershell
git add -- deploy/installer/include/baas_installer/git.hpp deploy/installer/src/git.cpp deploy/installer/src/main.cpp deploy/installer/tests/test_git.cpp deploy/installer/tests/test_workflow.cpp
git commit -m "fix(installer): use cached depth-one git acquisition"
```

### Task 4: Transaction staging cleanup

**Files:**
- Modify: `deploy/installer/include/baas_installer/transaction.hpp`
- Modify: `deploy/installer/src/transaction.cpp`
- Modify: `deploy/installer/tests/test_transaction.cpp`

**Interfaces:**
- Consumes: transaction-owned `tmp/installer/<id>` paths and commit actions registered by Git.
- Produces: `add_commit_action(std::function<void()>)`, cleanup in both `commit()` and `rollback()`, and `cleanup_abandoned_transactions(paths)` constrained by containment plus `journal.log` ownership.

- [ ] **Step 1: Write failing lifecycle tests**

Assert that rollback removes its staging root, commit removes its staging root, commit actions execute only on commit, rollback actions execute only on rollback, and constructor/startup cleanup removes a journal-bearing abandoned child while retaining an unjournaled sibling. Include a path-containment fixture proving a path outside `tmp/installer` remains untouched.

- [ ] **Step 2: Run the transaction test and verify RED**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-transaction && ctest --test-dir build-vcpkg -C Release -R "^transaction$" --output-on-failure`

Expected: rollback staging remains and commit-action APIs are missing.

- [ ] **Step 3: Implement owned cleanup and commit actions**

Execute commit actions before marking the transaction settled. If a commit action throws, leave the transaction rollback-capable. At the end of both successful commit and rollback, remove the exact resolved staging root. Startup cleanup may enumerate only direct children of resolved `paths.tmp_dir / "installer"`; remove a directory only if it remains below that root and contains `journal.log`.

- [ ] **Step 4: Verify transaction cleanup**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-transaction && ctest --test-dir build-vcpkg -C Release -R "^transaction$" --output-on-failure`

Expected: all lifecycle, ownership, and containment assertions pass.

- [ ] **Step 5: Commit transaction cleanup**

```powershell
git add -- deploy/installer/include/baas_installer/transaction.hpp deploy/installer/src/transaction.cpp deploy/installer/tests/test_transaction.cpp
git commit -m "fix(installer): clean transaction staging reliably"
```

### Task 5: Runtime source cache and executable UV acceptance

**Files:**
- Modify: `deploy/installer/include/baas_installer/uv_environment.hpp`
- Modify: `deploy/installer/src/uv_environment.cpp`
- Modify: `deploy/installer/tests/test_uv_environment.cpp`

**Interfaces:**
- Consumes: category-aware source cache, ten-second concurrent probes, PTY executor, and installation-local UV paths.
- Produces: `ensure_portable_uv` that accepts only an extracted executable whose `--version` exits zero and cached runtime rankings for UV, CPython, and PyPI.

- [ ] **Step 1: Write failing UV acceptance and cache tests**

Create a clean temporary installation with a fake PTY executor: `curl` writes bytes that deliberately do not match the removed pinned digest, `tar` creates the expected UV executable, and `<installed-uv> --version` returns zero. Assert one source is downloaded and accepted. Add a second fixture where the first extracted executable returns nonzero and the next succeeds. Add cache fixtures proving an existing preferred runtime source avoids a full probe round and a failed preferred source triggers all remaining probes concurrently.

- [ ] **Step 2: Run the UV test and verify RED**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-uv && ctest --test-dir build-vcpkg -C Release -R "^uv$" --output-on-failure`

Expected: the fake archive is rejected by pinned SHA before extraction.

- [ ] **Step 3: Remove fixed UV archive digest validation**

Delete `expected_uv_sha256()` from the public header and implementation and remove its test. After download, clear the attempted UV directory, extract, locate/copy the executable, set executable permissions, and run exactly `<installation-root>/toolkit/uv/uv[.exe] --version` through `run_visible`. On failure, remove the attempted executable/directory and continue; on success, persist the source and return immediately.

- [ ] **Step 4: Apply cached parallel ranking to runtime categories**

Pass `paths.state_dir / "source-ranking-v1.json"` to UV, CPython, and PyPI selection. Cache hits try only the preferred source; cache failure runs every remaining candidate concurrently with ten-second timeouts. Do not probe when UV/Python/dependency state already proves no download or resolution is required.

- [ ] **Step 5: Run UV and dependency-state tests**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-uv baas-installer-test-dependency-state && ctest --test-dir build-vcpkg -C Release -R "^(uv|dependency-state)$" --output-on-failure`

Expected: differing archive bytes are accepted by working `uv --version`; failed executables fall back once; unchanged dependency state performs no runtime probe.

- [ ] **Step 6: Commit runtime acquisition changes**

```powershell
git add -- deploy/installer/include/baas_installer/uv_environment.hpp deploy/installer/src/uv_environment.cpp deploy/installer/tests/test_uv_environment.cpp
git commit -m "fix(installer): accept usable uv and cache runtime sources"
```

### Task 6: Compact centered Unicode BAAS banner

**Files:**
- Modify: `deploy/installer/src/tui.cpp`
- Modify: `deploy/installer/tests/test_tui.cpp`

**Interfaces:**
- Consumes: existing per-element FTXUI centering helper.
- Produces: the approved six exact Unicode rows, each centered independently by display columns.

- [ ] **Step 1: Update the TUI test first**

Replace old ASCII title assertions with all six literal approved rows. Compute centers from rendered screen cells rather than UTF-8 byte length, and assert the first, middle, and final banner rows plus project URL differ in center by at most half a terminal cell. Assert no old `____  ___` title remains.

- [ ] **Step 2: Run the TUI test and verify RED**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-tui && ctest --test-dir build-vcpkg -C Release -R "^tui$" --output-on-failure`

Expected: approved Unicode rows are absent.

- [ ] **Step 3: Replace the title rows**

Render these exact rows through the existing `centered(text(row))` helper:

```text
██████╗  █████╗  █████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝
██████╔╝███████║███████║███████╗
██╔══██╗██╔══██║██╔══██║╚════██║
██████╔╝██║  ██║██║  ██║███████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
```

- [ ] **Step 4: Run TUI and localization tests**

Run: `cmake --build build-vcpkg --config Release --target baas-installer-test-tui baas-installer-test-localization && ctest --test-dir build-vcpkg -C Release -R "^(tui|localization)$" --output-on-failure`

Expected: Unicode title is present and centered in both language modes.

- [ ] **Step 5: Commit the banner**

```powershell
git add -- deploy/installer/src/tui.cpp deploy/installer/tests/test_tui.cpp
git commit -m "style(installer): center compact Unicode banner"
```

### Task 7: Full verification and disposable smoke tests

**Files:**
- Verify: `deploy/installer/`
- Verify: generated Release executable and logs only; do not commit smoke artifacts.

**Interfaces:**
- Consumes: completed implementation from Tasks 1-6.
- Produces: fresh Windows and Linux evidence for build, tests, download count, shallow depth, cleanup, migration, and launch.

- [ ] **Step 1: Run formatting/diff and full local test suite**

Run:

```powershell
git diff --check
cmake --build build-vcpkg --config Release
ctest --test-dir build-vcpkg -C Release --output-on-failure
```

Expected: build exits zero and all registered tests pass.

- [ ] **Step 2: Create a new disposable Windows smoke directory**

Use a new explicitly named child below the approved local test area, copy only the Release installer into it, and run `--auto-exit --no-launch`. Inspect the unified log and assert one `Receiving objects` sequence for main, one for OCR, one successful UV archive transfer, no `pinned SHA-256` message, Git repositories report shallow=true/count=1, OCR executable is under `core/ocr/baas_ocr_client/bin`, and `tmp/installer` has no transaction child.

- [ ] **Step 3: Verify second-run cache behavior and launch**

Run the same installer again. Assert the cached preferred source is queried without a full candidate probe round, unchanged remote SHA causes no fetch, dependency SHA cache skips resolution, and BAAS plus OCR can be launched from the installed tree.

- [ ] **Step 4: Verify on the supplied Linux host**

Transfer the matching Linux Release artifact to a new child of `/home/kiramei/Workspace/Tests/BAAS`, run the same clean and second-run checks, and verify `git rev-parse --is-shallow-repository`, `git rev-list --count HEAD`, UV, OCR placement, and absence of residual transaction staging. Do not display credentials in commands or logs.

- [ ] **Step 5: Remove disposable smoke directories with required confirmation**

Resolve and report the exact Windows and Linux smoke paths before deletion. Delete only after the applicable confirmation, then verify both paths are absent. Do not touch the user's `.secret`, existing installation, or unrelated build directories.

- [ ] **Step 6: Review branch diff and update the existing PR**

Run `git status --short`, `git diff upstream/master...HEAD --stat`, and inspect the complete installer diff. Push `feat/cpp-tui-installer` to `origin` only after verification, then confirm the existing PR targets `upstream/master` and its checks start successfully.
