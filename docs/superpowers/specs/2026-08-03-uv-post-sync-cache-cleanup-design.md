# UV Post-Synchronization Cache Cleanup Design

## Goal

Keep every UV-related file inside the installation root while avoiding retained download caches after a dependency resolution and synchronization completes successfully.

## Behavior

`sync_portable_uv` will clear disposable cache data only after the current run has successfully completed both `uv pip compile` and `uv pip sync` and has durably written `.baas-installer/dependencies-v1.sha256`.

The cleanup removes these installation-local directories:

- `toolkit/uv/cache`
- `toolkit/uv/python-cache`
- `toolkit/uv/xdg/cache`
- `tmp/uv`

It preserves the portable UV executable, installed CPython, `.venv`, source-ranking data, credentials/configuration, compiled requirements, and dependency SHA stamp.

When the dependency SHA is unchanged, UV remains fully skipped and existing cache directories are not touched. If resolution or synchronization fails, caches are retained so the retry can reuse already downloaded data.

## Error Handling

Cleanup is a required final stage of a real dependency synchronization. Failure to remove any selected cache directory returns an installation error that identifies the affected path. Successfully removed directories are not recreated at the end of the run; UV will recreate them when a future dependency change requires another synchronization.

## Tests

Automated tests will verify:

1. Successful compile, sync, and stamp persistence remove all four cache directories while preserving UV, CPython, `.venv`, ranking state, and the stamp.
2. A dependency SHA cache hit executes no UV commands and does not alter pre-existing cache contents.
3. Compile or sync failure does not clear caches.
4. Cleanup failure is reported as an error where the platform permits a deterministic failure fixture.

The normal Release suite, a fresh Windows installation, a second no-op run, and rename validation remain required before completion.
