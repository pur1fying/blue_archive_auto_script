# Upstream synchronization

The fork merges upstream `master` into its own `master`. Original upstream commit
objects, hashes, and ancestry are preserved, alongside the fork's own commits.
When the histories have diverged, synchronization creates a normal merge commit.
When a fast-forward is possible, no extra merge commit is needed.

GitHub and CNB updates use ordinary pushes. Synchronization never rebases the
published fork or force-pushes either repository. A concurrent update or divergent
mirror is rejected.

The workflow fetches both repositories, checks out the current fork snapshot, and
runs `.github/scripts/sync_upstream.py`. The helper uses Git's normal merge
operation. It does not copy changes into replacement upstream commits or use a
separate synchronization checkpoint. Git ancestry and GitHub's ahead/behind
counts describe synchronization progress directly.

If upstream is already an ancestor of the fork, synchronization is a no-op.
Otherwise, the workflow verifies that both the previous fork commit and the exact
upstream commit remain ancestors of the result. Tests must pass before pushing.
Conflicts are aborted; failed merges, failed tests, and rejected pushes leave the
remote branch unchanged.

## Resolving a conflict

Create an isolated branch from the current fork `master`, fetch upstream, and
merge its latest `master`. Review and resolve conflicts while preserving the
intended fork behavior, then run the backend and synchronization tests. Commit
the merge and push normally. Do not replace the merge with copied patches if the
upstream commit hashes are to remain part of the fork's history.

Upstream contributions should continue to use focused branches based directly on
upstream, with only the intended feature commits. This keeps fork synchronization
merge commits out of unrelated upstream pull requests.

Earlier content-copy synchronization commits remain in published history. The
transition merge connects the original upstream history without rewriting those
existing commits; subsequent synchronizations preserve original hashes directly.
