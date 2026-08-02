# Installer probe and header fix implementation plan

1. Update source-ranking tests to specify advisory failure ordering and all-failed retention.
2. Update UV tests to require real attempts after all probes fail.
3. Update TUI tests to compare the horizontal centers of differently sized header lines.
4. Run the focused tests and confirm that the new assertions fail for the current implementation.
5. Add a shared one-time libcurl initializer and use it before all easy handles and concurrent probes.
6. Retain failed probe candidates, add sanitized CURL/HTTP diagnostics, and remove probe-only terminal errors.
7. Center each header line independently.
8. Run focused tests, the full CTest suite, and a release build. Copy that Release executable into a brand-new disposable directory and perform a real clean-install smoke test there. Verify `setup.toml`, main checkout, OCR placement, portable UV/Python, and BAAS startup, then delete the disposable directory.
9. Commit and push the verified change to the existing PR branch.
