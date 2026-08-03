# Installer Update, PTY, and I18n Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the native installer perform real no-op/incremental/full main and OCR updates, expose complete PTY-derived logs in a bilingual TUI, and exit immediately after launching BAAS.

**Architecture:** Repository preparation produces an immutable `PreparedRepository` for each independently selected MirrorChyan/Git backend, then a barrier feeds the existing main-before-OCR transaction. External terminal-oriented tools publish raw chunks through a platform PTY into one normalized, redacted event log consumed by the TUI and disk sink. Installer-owned messages are keys resolved by an automatically detected Chinese/English catalog.

**Tech Stack:** C++20, CMake/CTest, FTXUI 6.1.9, libcurl, libgit2, Windows ConPTY, POSIX `forkpty`/`openpty`, existing transaction/config/uv components.

## Global Constraints

- The branch remains based on `upstream/master`; do not rebase onto `origin/master`.
- Only `setup.toml` exists; do not introduce `config.toml`.
- Backend order is MirrorChyan, installed Git CLI across all ranked sources, then libgit2 across all ranked sources.
- Main and OCR prepare concurrently, then main deploys before OCR under `core/ocr/baas_ocr_client/bin`.
- A matching local and remote Git SHA must not execute fetch.
- MirrorChyan supports full and incremental packages for both `BAAS_repo` and platform-specific `BAAS_Cpp`.
- Do not use `MAIN_REPO_SRC_DEV` or `https://baas-cdn.kiramei.workers.dev`.
- All managed uv, Python, cache, temporary, and state paths remain under the install root.
- User-visible external commands use ConPTY on Windows and `forkpty`/`openpty` on POSIX; only quiet machine-readable probes may use captured pipes.
- Never print, copy, commit, embed, or pass the MirrorChyan test secret on a command line.
- Preserve unrelated untracked `.vscode/` and `build/` content.

---

### Task 1: Localized normalized event log

**Files:**
- Create: `deploy/installer/include/baas_installer/localization.hpp`
- Create: `deploy/installer/src/localization.cpp`
- Create: `deploy/installer/include/baas_installer/logging.hpp`
- Create: `deploy/installer/src/logging.cpp`
- Create: `deploy/installer/tests/test_localization.cpp`
- Create: `deploy/installer/tests/test_logging.cpp`
- Modify: `deploy/installer/CMakeLists.txt`

**Interfaces:**
- Produces: `enum class Language { English, SimplifiedChinese };`
- Produces: `Language detect_language(const LocaleInputs&)` and `std::string message(Language, MessageId)`.
- Produces: `LogEvent { timestamp, task, backend, severity, text, replace_last }`.
- Produces: `ChunkDecoder::consume(std::string_view)` and `ChunkDecoder::finish()` returning normalized logical-line updates.
- Produces: `Redactor::add_secret(std::string)` and `Redactor::redact(std::string_view)`.

- [ ] **Step 1: Add failing localization tests**

Test `zh-CN`, `zh_CN.UTF-8`, and Windows language ID `0x0804` as Chinese; test empty, `en_US`, and `ja_JP` as English. Assert the task labels and failure actions exist in both catalogs.

- [ ] **Step 2: Run the localization target and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-localization`

Expected: failure because the target and localization interfaces do not exist.

- [ ] **Step 3: Implement locale detection and complete message catalogs**

Use `LocaleInputs { std::string lc_all, lc_messages, lang; unsigned long windows_ui_language; }`. Normalize `_` to `-`, lowercase the prefix, and select Chinese only when the language prefix equals `zh`. Provide keys for every setup label, task label, state, error action, and launch result currently rendered by `tui.cpp`.

- [ ] **Step 4: Add failing chunk and redaction tests**

Feed chunks that split the UTF-8 bytes for `下载`, contain `\x1b[31m`, OSC title sequences, `12%\r34%\r`, `abc\bD\n`, a registered secret, `?cdk=value`, `Authorization: Bearer value`, and `Cookie: x=value`. Assert one replaceable `34%` line, one committed `abD` line, valid UTF-8, and no sensitive values.

- [ ] **Step 5: Implement decoder, event formatter, redactor, and thread-safe event store**

Keep incomplete UTF-8 and escape sequences between calls. Treat bare `\r` as replacement, `\r\n` as one commit, and backspace as deletion of the previous Unicode code point. Add `EventLog::publish(LogEvent)`, `snapshot()`, and `set_sink(path)`; apply redaction before memory and file sinks.

- [ ] **Step 6: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-localization baas-installer-test-logging; ctest --test-dir build -C Release -R "localization|logging" --output-on-failure`

Expected: both tests pass.

Commit: `feat(installer): add localized normalized logging`

---

### Task 2: Cross-platform PTY process runner

**Files:**
- Modify: `deploy/installer/include/baas_installer/process.hpp`
- Modify: `deploy/installer/src/process.cpp`
- Modify: `deploy/installer/tests/test_process.cpp`
- Modify: `deploy/installer/CMakeLists.txt`

**Interfaces:**
- Extend `ProcessSpec` with `bool use_pty`, `std::filesystem::path working_directory`, `std::chrono::milliseconds timeout`, and `std::function<void(std::string_view)> on_chunk`.
- Preserve `ProcessResult run_process(const ProcessSpec&)` for hidden probes.
- Produce `ProcessResult run_terminal_process(const ProcessSpec&)` for visible commands.

- [ ] **Step 1: Add a failing PTY behavior test**

Launch the test executable in helper mode so it emits ANSI color, split UTF-8 bytes, and carriage-return progress only when stdout is a terminal. Assert `on_chunk` receives raw chunks, the child detects a terminal, environment overrides work, and the exit code is retained.

- [ ] **Step 2: Run the process test and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-process; ctest --test-dir build -C Release -R process --output-on-failure`

Expected: failure because `run_terminal_process` and `use_pty` are absent.

- [ ] **Step 3: Implement ConPTY**

Dynamically use `CreatePseudoConsole`, inheritable pipes, `STARTUPINFOEXW`, `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE`, raw `ReadFile` chunks, timeout termination, working directory, and the existing UTF-8 environment block. Do not add the CDK or any logger secret to the environment.

- [ ] **Step 4: Implement POSIX PTY**

Use `forkpty`, apply working directory and environment in the child, call `execvp` directly without a shell, read the master fd until EOF, and translate `waitpid` status. Link `util` only on platforms that require it.

- [ ] **Step 5: Keep hidden probes separate and make visible failures observable**

Retain pipe capture for `run_process`; route each raw PTY chunk exclusively through `on_chunk`, while optionally accumulating bounded diagnostic output in `ProcessResult.output`.

- [ ] **Step 6: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-process; ctest --test-dir build -C Release -R process --output-on-failure`

Expected: the PTY helper test passes on Windows; POSIX behavior is compiled and exercised by CI.

Commit: `feat(installer): capture tool output through PTY`

---

### Task 3: Git no-op and incremental update planner

**Files:**
- Modify: `deploy/installer/include/baas_installer/git.hpp`
- Modify: `deploy/installer/src/git.cpp`
- Modify: `deploy/installer/tests/test_git.cpp`

**Interfaces:**
- Produce `enum class RepositoryMode { Unchanged, Incremental, Full };`.
- Produce `RepositoryProbe { bool valid; std::string head; }` from `probe_repository(path)`.
- Produce `GitResult prepare_git_repository(sources, live_path, staging_path, revision, ProcessObserver)` with resolved commit and mode.
- Produce `bool apply_git_update(const GitResult&, live_path, InstallTransaction&, error)`.
- Produce `using ProcessObserver = std::function<void(std::string_view task, std::string_view backend, std::string_view chunk)>;`, shared with uv integration.

- [ ] **Step 1: Add local-remote no-op tests**

Create a bare remote and working clone in the test temp directory. Instrument the command executor and assert equal local/remote heads invoke `ls-remote` but never `fetch` or `clone`, returning `RepositoryMode::Unchanged` and the real local SHA.

- [ ] **Step 2: Run the Git test and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-git; ctest --test-dir build -C Release -R git --output-on-failure`

Expected: failure because the preparation interfaces do not exist.

- [ ] **Step 3: Implement valid-repository probes and lightweight remote lookup**

Use hidden `rev-parse --is-inside-work-tree`, `rev-parse HEAD`, and `ls-remote <source> <revision>`. Try all sources with installed Git CLI before any libgit2 remote-head lookup. Return unchanged immediately on equal SHAs.

- [ ] **Step 4: Add changed-remote and corrupt-repository tests**

Advance the bare remote, then assert preparation fetches but leaves the live head unchanged until apply. Assert apply reaches the new SHA and retains `.git`. For invalid `.git`, assert preparation performs a full staged clone.

- [ ] **Step 5: Implement incremental fetch and full clone paths**

Fetch the resolved SHA into the live repository without checkout during preparation; store old/new SHAs in `GitResult`. Run visible clone/fetch commands with `run_terminal_process`. Apply incremental mode with transactional old-head recording and hard reset; deploy full mode from staging.

- [ ] **Step 6: Correct backend ordering and libgit2 parity**

Change clone and remote lookup loops to Git CLI over every source, followed by libgit2 over every source. Implement libgit2 list-heads, fetch/clone, and checkout with the same result modes.

- [ ] **Step 7: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-git; ctest --test-dir build -C Release -R git --output-on-failure`

Expected: no-op, incremental, corrupt-repository, and backend-order tests pass.

Commit: `feat(installer): add real incremental Git updates`

---

### Task 4: MirrorChyan main/OCR full and incremental packages

**Files:**
- Modify: `deploy/installer/include/baas_installer/mirrorchyan.hpp`
- Modify: `deploy/installer/src/mirrorchyan.cpp`
- Modify: `deploy/installer/tests/test_mirrorchyan.cpp`
- Modify: `deploy/installer/vcpkg.json`
- Modify: `deploy/installer/CMakeLists.txt`

**Interfaces:**
- Produce `MirrorResource { Main, Ocr }` and `mirror_latest_url(resource, platform, cdk, current_version, channel)`.
- Produce `MirrorPackage { RepositoryMode mode; version; archive; extracted_root; changes; }`.
- Produce `prepare_mirror_package(...)` and `apply_mirror_package(..., InstallTransaction&, error)`.
- Produce `MirrorChanges { vector<path> added, modified, deleted; }`.

- [ ] **Step 1: Add failing resource and response tests**

Assert main URLs use `BAAS_repo`, OCR URLs use `BAAS_Cpp` plus exact `windows-x64`, `linux-x64`, `macos-x64`, or `macos-arm64`, and CDKs remain URL-encoded without entering error strings.

- [ ] **Step 2: Add failing package safety tests**

Build small ZIP fixtures for a full tree and an incremental `changes.json`. Assert valid add/modify/delete parsing and rejection of absolute, drive-qualified, `..`, missing-source, malformed manifest, and bad SHA-256 inputs.

- [ ] **Step 3: Run the MirrorChyan test and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-mirrorchyan; ctest --test-dir build -C Release -R mirrorchyan --output-on-failure`

Expected: failure because resource selection and package application are absent.

- [ ] **Step 4: Implement in-process HTTP and archive extraction**

Use libcurl for latest/download requests and libarchive for ZIP inspection/extraction. Keep CDK only in request memory, pass response text directly to parsing, and report sanitized status/error objects. Validate SHA-256 before opening the archive and validate all paths before extracting or applying.

- [ ] **Step 5: Implement full/incremental preparation and bounded fallback**

Recognize `update_type`; for a requested incremental update that returns full, retry ten times with 500 ms delays and accept the final validated full package. Represent current-version responses as `RepositoryMode::Unchanged` without downloading.

- [ ] **Step 6: Implement transactional application**

For incremental mode, journal and apply deletions, additions, and modifications. For full mode, deploy the first child directory. Move `.git` into transaction backup only during commit and restore it on rollback.

- [ ] **Step 7: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-mirrorchyan; ctest --test-dir build -C Release -R mirrorchyan --output-on-failure`

Expected: both resources, both package modes, retry, validation, and path-safety tests pass.

Commit: `feat(installer): support MirrorChyan main and OCR updates`

---

### Task 5: Prepared repository workflow and atomic state

**Files:**
- Modify: `deploy/installer/include/baas_installer/workflow.hpp`
- Modify: `deploy/installer/src/workflow.cpp`
- Modify: `deploy/installer/include/baas_installer/transaction.hpp`
- Modify: `deploy/installer/src/transaction.cpp`
- Modify: `deploy/installer/tests/test_workflow.cpp`
- Modify: `deploy/installer/tests/test_transaction.cpp`

**Interfaces:**
- Produce `PreparedRepository { RepositoryMode mode; std::string backend; std::string version; std::string prepare_error; std::function<bool(InstallTransaction&, std::string&)> apply; }`; rollback remains owned by `InstallTransaction`.
- Change services to `prepare_main() -> PreparedRepository` and `prepare_ocr() -> PreparedRepository`.
- Keep `install_or_update(config, paths, services)` as the orchestration entry point.

- [ ] **Step 1: Add failing workflow state tests**

Assert preparation runs concurrently; a failure joins the peer and performs zero live mutations; successful preparation applies main before OCR; unchanged units perform no apply; config receives both versions only after verify and uv succeed.

- [ ] **Step 2: Add failing rollback tests**

Force OCR apply, verify, and uv failures separately. Assert prior main/OCR bytes and committed heads are restored, moved `.git` directories return, and prior `setup.toml` SHA/version fields remain byte-identical.

- [ ] **Step 3: Run workflow and transaction tests to confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-workflow baas-installer-test-transaction; ctest --test-dir build -C Release -R "workflow|transaction" --output-on-failure`

Expected: new ordering and rollback assertions fail.

- [ ] **Step 4: Implement immutable preparation results and barrier**

Run main/OCR producers via `std::async`, collect both results, cancel only through shared cooperative state, and enter commit only when both succeed. Emit checking, skipped, ready, applying, complete, fallback, and failed events with task/backend metadata.

- [ ] **Step 5: Extend transaction journal and atomic config commit**

Journal Git old heads, Mirror file backups, created paths, deleted paths, and `.git` moves. Apply main then OCR, verify, sync uv, set both in-memory versions, and call `save_config_atomic` once. On failure, reverse every applied journal entry.

- [ ] **Step 6: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-workflow baas-installer-test-transaction; ctest --test-dir build -C Release -R "workflow|transaction" --output-on-failure`

Expected: concurrency, order, no-op, persistence, and rollback tests pass.

Commit: `refactor(installer): orchestrate prepared repository updates`

---

### Task 6: Unified bilingual TUI and immediate exit

**Files:**
- Modify: `deploy/installer/include/baas_installer/tui.hpp`
- Modify: `deploy/installer/src/tui.cpp`
- Modify: `deploy/installer/tests/test_tui.cpp`

**Interfaces:**
- `InstallerViewModel(Language, shared_ptr<EventLog>, bool setup_required)` owns localized task snapshots and scroll state.
- `append_event(LogEvent)` updates the unified log, replacing the last logical line when requested.
- `run_tui(...)` exits the FTXUI loop on successful BAAS launch; launch failure remains retryable.

- [ ] **Step 1: Add failing TUI model tests**

Assert Chinese and English labels, static running marker, real-progress-only gauge, more than eight retained history lines, carriage-return replacement, scroll offsets, no `Succeeded` page transition, and launch-success exit request.

- [ ] **Step 2: Run the TUI test and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-tui; ctest --test-dir build -C Release -R tui --output-on-failure`

Expected: failure because the existing model truncates logs, animates a spinner, and shows a success page.

- [ ] **Step 3: Implement the unified log layout**

Remove ticker/frame state and `spinner(...)`. Render task states with fixed symbols and a large bordered log pane tagged `[time][task][backend][level]`. Tail-follow by default; add keyboard and mouse scrolling without splitting Git into a separate panel.

- [ ] **Step 4: Localize every installer-owned string**

Replace literal Chinese text and English-detail substring inference with `MessageId` and explicit status/progress events. Leave decoded child output unchanged except redaction and tagging.

- [ ] **Step 5: Implement launch-success exit behavior**

Represent installation commit and BAAS launch as separate outcomes. Keep the failure view for launch retry without transaction rollback. Post the FTXUI exit closure immediately after a successful detached launch; remove the success screen and manual Exit requirement.

- [ ] **Step 6: Run focused tests and commit**

Run: `cmake --build build --config Release --target baas-installer-test-tui; ctest --test-dir build -C Release -R tui --output-on-failure`

Expected: bilingual model/layout and launch-flow tests pass with no spinner.

Commit: `feat(installer): unify bilingual live TUI logs`

---

### Task 7: Production wiring, uv logs, migration, and CI

**Files:**
- Modify: `deploy/installer/src/main.cpp`
- Modify: `deploy/installer/src/uv_environment.cpp`
- Modify: `deploy/installer/include/baas_installer/uv_environment.hpp`
- Modify: `deploy/installer/tests/test_uv_environment.cpp`
- Modify: `deploy/installer/tests/manual/verify_local_migration.ps1`
- Modify: `deploy/installer/README.md`
- Modify: `deploy/installer/README_CN.md`
- Modify: `.github/workflows/build-installer.yml`

**Interfaces:**
- Main constructs one redacted `EventLog`, process observer, main preparer, and OCR preparer.
- uv synchronization accepts the shared `ProcessObserver` and uses PTY for every visible uv command.
- Detached launch returns success independently from the committed installation result.

- [ ] **Step 1: Add failing uv observer tests**

Inject a fake process executor and assert every visible uv install/venv/pip command requests PTY, passes the root-local environment map, and forwards chunks to the observer. Assert quiet version/path probes stay hidden.

- [ ] **Step 2: Run uv tests and confirm failure**

Run: `cmake --build build --config Release --target baas-installer-test-uv; ctest --test-dir build -C Release -R uv --output-on-failure`

Expected: failure because uv does not accept the shared observer or require PTY.

- [ ] **Step 3: Wire production repository selection and logging**

Replace direct curl/tar and always-clone lambdas in `main.cpp` with main/OCR preparers. For each unit, try MirrorChyan when configured, then Git CLI, then libgit2. Send every status and raw chunk to the same event log; never log request URLs containing `cdk`.

- [ ] **Step 4: Route uv through PTY and keep all paths portable**

Pass the observer into `sync_portable_uv`, use `run_terminal_process` for visible commands, and retain every existing `UV_*`, `XDG_*`, temp, venv, Python, and cache override rooted at the executable directory.

- [ ] **Step 5: Update migration and documentation**

Make the migration script copy the source install, never mutate it, validate no-fetch behavior when heads match, validate OCR placement and Git/Mirror metadata rules, validate root-local uv state, launch BAAS, and record sanitized evidence. Document bilingual locale selection, unified PTY logs, update modes, and immediate exit.

- [ ] **Step 6: Run the full local test suite**

Run: `cmake --build build --config Release; ctest --test-dir build -C Release --output-on-failure`

Expected: every installer test passes.

- [ ] **Step 7: Run local Git integration and disposable migration**

Run the local bare-remote no-op/update integration. Then run `verify_local_migration.ps1` against a fresh copy of `D:\Amusement\BAAS_NEW`, never the original. Verify the normalized log contains Git and uv output, contains no spinner artifacts, and BAAS launch closes the installer.

- [ ] **Step 8: Run the explicitly configured MirrorChyan integration safely**

Read the operator-provided secret file only inside the test process. Exercise main and OCR in disposable roots, then scan repository diff, logs, captured test output, staging, and build artifacts byte-for-byte for the secret. Print only the boolean scan result and sanitized resource outcomes.

- [ ] **Step 9: Commit production integration**

Commit: `feat(installer): integrate incremental bilingual installer`

- [ ] **Step 10: Push and verify four-platform CI**

Push `feat/cpp-tui-installer`, wait for Windows x86_64, Linux x86_64, macOS x86_64, and macOS arm64 tests/builds, and inspect sanitized logs on any failure. Confirm the tag-only job still publishes executables and `SHA256SUMS` as GitHub Release assets.
