# UV Acceptance and Banner Design

## Goal

Stop valid portable UV packages from being rejected and repeatedly downloaded, and replace the installer header with the approved compact BAAS banner centered in the terminal.

## UV acceptance

The installer will not calculate, download, pin, or compare a SHA-256 digest for the portable UV archive. The configured mirror assets are mutable, so a digest copied from one UV release cannot establish whether a differently versioned mirror asset is usable.

For each source in measured order, the installer will:

1. download the archive into the installation root's temporary directory;
2. extract it into the installation root's UV toolkit directory;
3. locate and install the platform UV executable;
4. run that exact executable with `--version` through the existing PTY process path;
5. accept the source immediately when the command exits successfully.

Download, extraction, executable discovery, or execution failure causes cleanup of that attempted UV installation before the next source is tried. A successful executable check stops source iteration, preventing another full archive download. Existing dependency-state SHA caching remains unchanged because it controls whether dependency resolution is needed; only UV archive verification is removed.

## Header

The installer will display this exact six-line banner:

```text
██████╗  █████╗  █████╗ ███████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝
██████╔╝███████║███████║███████╗
██╔══██╗██╔══██║██╔══██║╚════██║
██████╔╝██║  ██║██║  ██║███████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
```

Each banner row and each metadata row will be centered independently by FTXUI using terminal display columns. No manual byte-length or common-width padding will be used. This keeps UTF-8 box-drawing characters aligned and preserves centering when the viewport width changes.

## Error handling and observability

UV source failures remain visible in the unified installer log. The installer will distinguish download, extraction, executable discovery, and `uv --version` failures. It will not emit a SHA verification error. All UV subprocess output continues to arrive through PTY chunks.

## Verification

Automated regression tests will first demonstrate the current failures and then verify:

- a downloaded archive is accepted without a matching pinned digest when its extracted UV executable passes `--version`;
- an unusable extracted executable causes the next source to be attempted;
- the old and new banner rows cannot be confused, and all six approved rows render;
- independently centered Unicode rows share the viewport center.

After the automated suite and release build pass, a complete install will run in a new disposable directory. The smoke test must show one successful UV archive download, a successful local `uv --version`, dependency installation, OCR placement, and BAAS launch. The disposable directory will be removed after confirmation under the applicable deletion policy.
