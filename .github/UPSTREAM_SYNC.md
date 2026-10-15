# Upstream synchronization

The fork appends upstream changes to `master`. Synchronization does not rebase,
rewrite published commits, or create merge commits. GitHub and CNB updates use
ordinary pushes, so a concurrent update or divergent mirror is rejected.

`.github/upstream-sync.json` records the last imported upstream commit. This is
the authoritative synchronization position: imported commits have new IDs, so
GitHub's ancestry-based ahead/behind counts do not describe the imported content.

For each new commit on upstream's first-parent history, the synchronizer performs
a three-way content merge using the previous upstream snapshot as its base. It
preserves fork changes and creates one single-parent import commit, including an
updated checkpoint. Upstream merge commits contribute their complete first-parent
diff; their merge topology is not copied into the fork.

The script prepares the entire batch before advancing the local checkout. A
conflict, invalid checkpoint, rewritten upstream history, or dirty checkout stops
the import. The workflow tests the resulting snapshot before pushing. Failed
tests and rejected ordinary pushes leave the remote branch unchanged.

## Current checkpoint

The initial checkpoint is upstream `1139aec53ae32337ddd5f82f0ad07133123cc42c`
(PR #598). Its installer removal was already applied to the fork in `5438e89a`.
The checkpoint records that verified equivalence without replaying older fork
commits that previously added the now-removed OCR installer handoff.

## Resolving a conflict

Inspect the failed import in an isolated checkout. Apply and review the upstream
changes against the fork's current content, then update the checkpoint only after
all changes through that upstream commit have been accounted for. Commit the
resolution, run the synchronization and backend tests, and push normally. Do not
advance the checkpoint merely to silence a failed synchronization.

Upstream contributions should continue to use focused branches based directly on
upstream, with only the intended feature commits.
