# Shallow Git, Source Cache, and Transaction Cleanup Design

## Goal

Make Git-managed installation use one shallow network transfer, retain only the current commit after a successful update, reuse measured source rankings, and prevent failed installations from accumulating staging data.

## Git repository preparation

Main and OCR repositories remain independent and prepare concurrently. A full Git installation will use an initialized repository followed by one `git fetch --depth=1 --no-tags <source> <revision>` and a local detached checkout of `FETCH_HEAD`. It will not use a blobless partial clone, because that separates metadata transfer from the later checkout's blob transfer and displays two complete `Receiving objects` phases.

An existing Git installation will query the selected source with `ls-remote`. If the returned commit equals local `HEAD`, preparation returns unchanged and performs no fetch. Otherwise it fetches the selected revision with `--depth=1 --no-tags`, then the transaction applies the prepared commit. Both main and OCR Git repositories must report `true` from `git rev-parse --is-shallow-repository` and expose one commit from `git rev-list --count HEAD` after a successful installation.

Rollback safety temporarily requires the previous commit to remain reachable until every deployment, verification, UV, Python, and dependency step succeeds. Final Git cleanup therefore runs only after the installation transaction can no longer fail: remove installer-created temporary refs, expire reflogs, and prune unreachable objects. A failed transaction resets to the previous commit instead and does not prune rollback data prematurely.

## Persistent source ranking

Source state is stored under the protected, installation-relative directory `.baas-installer` in `source-ranking-v1.json`. It never uses a machine-global cache. Separate entries are maintained for main Git, OCR Git, UV, CPython, and PyPI. Each entry records the candidate URL, last measured latency, consecutive failure count, latest observed remote commit when applicable, and whether it was the most recent successful source.

The cache policy is cache-first and has no time-based expiry:

1. With no matching cache, or when the configured candidate set changes, probe all candidates concurrently, retain failed probes as fallbacks, save the complete ranking atomically, and try the fastest successful result first.
2. With a matching cache, try the most recently successful source first without probing every candidate. For Git, its required `ls-remote` freshness check also updates that source's observed commit and latency.
3. If the cached source's real operation fails, increment its persisted failure count, re-probe all candidates, replace the ranking, and try the refreshed order while excluding the already failed attempt.
4. On a successful real operation, persist the successful source as preferred and reset its consecutive failure count.

Cached Git commit values are hints and diagnostics only. They never replace the live `ls-remote` comparison required to decide that a repository is current.

## Transaction storage lifecycle

Every transaction owns exactly one child directory under `tmp/installer`. Both `commit()` and `rollback()` remove that directory after their work completes. The transaction destructor performs the same rollback cleanup when control leaves unexpectedly.

At startup, the installer scans only direct children of its own installation-relative `tmp/installer` directory. It removes an abandoned child only when the resolved path remains inside that directory and the child contains the installer's `journal.log`. Other directories and files are untouched. This recovers storage left by a process crash while constraining deletion to installer-owned staging.

During a clean installation, staging and live files may coexist briefly for transactional safety. No staging copy may remain after success or handled failure.

## Integration with approved UV and header changes

Portable UV archives have no fixed digest check. A source is accepted after extraction when the installed executable succeeds with `uv --version`; failure moves to the next cached/ranked source. Dependency requirement SHA caching remains separate and continues to skip unchanged dependency resolution.

The TUI uses the approved compact six-line BAAS banner from `2026-08-02-uv-acceptance-and-banner-design.md`, with each line independently centered by terminal display width.

## Verification

Automated tests must demonstrate these failures before production changes are made, then verify:

- a fresh Git preparation has one fetch operation, uses `--depth=1` and `--no-tags`, and does not use `--filter=blob:none`;
- an unchanged repository performs `ls-remote` but no fetch;
- an updated repository remains shallow with one reachable commit after successful finalization;
- cached ranking is reused without probing every source;
- a changed candidate set or failed cached source triggers a refreshed ranking;
- source state is written atomically below `.baas-installer` and survives moving the whole installation directory;
- rollback and commit remove their staging roots;
- startup cleanup rejects paths without an installer journal and paths outside `tmp/installer`;
- the UV and Unicode banner regression tests in the companion design pass.

A disposable clean-install smoke test must confirm one `Receiving objects` phase per Git repository, one successful UV archive download, correct OCR placement, dependency completion, shallow depth-one repositories, successful BAAS launch, and no residual transaction directory after completion. The smoke directory is removed only after the applicable deletion confirmation.
