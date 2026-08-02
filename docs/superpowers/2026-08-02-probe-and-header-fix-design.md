# Installer probe and header fix design

## Problem

The Windows installer reports that every UV or PyPI source failed its probe even though the same URLs return HTTP 200 from the same machine. The title block is centered as one box, so its shorter lines are not individually centered.

## Confirmed cause

Source probes are launched concurrently with `std::async`. Their first operation is `curl_easy_init()`, but the installer never calls `curl_global_init()` before those threads start. libcurl requires global initialization before concurrent use. The current probe also collapses every CURL error and HTTP response into `-1`, then discards every failed probe; an empty ranking therefore prevents any real download attempt.

Direct requests with the Windows system proxy explicitly bypassed returned HTTP 200 for representative PyPI, Aliyun, GitHub UV, and CNB UV URLs. The system proxy is not the cause of this incident.

## Design

1. Add a process-lifetime, thread-safe libcurl initializer shared by probe and MirrorChyan HTTP code. Initialize it before starting concurrent probe tasks.
2. Keep successful probes first, ordered by latency. Retain failed probes afterward in their original order. A probe is advisory; only a real download or UV command may reject a source.
3. Log sanitized probe diagnostics: CURL result name/code and HTTP status only. Do not log proxy configuration, credentials, or response bodies.
4. Render every title/welcome/author line with its own horizontal centering decorator instead of centering the enclosing `vbox` as a single block.

## Verification

- Unit test that failed probes remain available after successful probes and that an all-failed ranking preserves all candidates.
- UV workflow test that all probe failures still lead to real source attempts.
- TUI snapshot-coordinate test that title lines have the expected independent horizontal centers.
- Build and run the full installer test suite, then copy the newly built Release executable into a brand-new disposable directory and complete a real end-to-end Windows installation. Verify `setup.toml`, the main checkout, OCR placement, the portable UV/Python environment, and BAAS startup; remove the disposable directory only after recording the result.
