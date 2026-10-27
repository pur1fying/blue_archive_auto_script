"""Write metadata into a release tree before discarding its .git directory.

Uses only the standard library, works with depth-one CI checkouts, and never
fetches Git objects. GITHUB_TOKEN is optional and only sent to GitHub's API.
"""
from __future__ import annotations

import argparse
import os
import runpy
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--repository", choices=("pur1fying/blue_archive_auto_script", "Kiramei/baas-dev"), required=True)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    if not 1 <= args.limit <= 500:
        parser.error("--limit must be between 1 and 500")
    root = args.root.resolve()
    history = runpy.run_path(str(Path(__file__).resolve().parents[1] / "service/update/history.py"))
    local = history["_local_history"](root, args.repository, args.limit, validate_reference=False)
    entries = local["entries"] if local else []
    if not local or local["partial"]:
        # Anchor a shallow build's metadata to its actual packaged commit, not a
        # branch that may move while the release job is running.
        anchor = local["current"] if local else "master"
        try:
            fetched, _, partial, _ = history["_fetch_github"](args.repository, anchor, args.limit, os.getenv("GITHUB_TOKEN"))
            if fetched:
                entries = fetched
            if partial:
                print("Some GitHub metadata pages are unavailable; packaging the available metadata only.")
        except history["HistoryUnavailable"]:
            if not entries:
                raise SystemExit("Commit metadata unavailable; refusing an empty release manifest") from None
            print("GitHub metadata unavailable; packaging the existing local commit metadata only.")
    document = {"schema": 1, "repository": args.repository, "reference": "master", "entries": entries}
    history["_write_json"](root / history["MANIFEST_NAME"], document)
    print(f"Packaged {len(entries)} commit metadata rows (no Git objects or patches).")


if __name__ == "__main__":
    main()
