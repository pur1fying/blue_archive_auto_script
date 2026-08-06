"""Download and audit the checked-in Wikiru portrait seed library.

This is a development-only acquisition tool. It never trains a model and is
not imported by the normal application runtime. The downloaded bytes remain
copyrighted by their respective rights holders; see the source notice beside
the generated manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config.default_config import STATIC_DEFAULT_CONFIG


PAGE_URL = (
    "https://bluearchive.wikiru.jp/"
    "?%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC%E4%B8%80%E8%A6%A7"
)
OUTPUT_DIR = Path(__file__).with_name("data") / "wikiru_portraits"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
CAPTURE_DATE = "2026-08-06"
EXPECTED_REMOTE_IMAGES = 272
EXPECTED_TRAINING_IMAGES = 270
EXPECTED_IDENTITIES = 270
EXPECTED_DIMENSIONS = {(198, 198): 8, (200, 200): 262, (300, 300): 2}
USER_AGENT = "BlueArchiveAutoScript portrait data audit/1.0"
INVALID_FILENAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename_component(value: str) -> str:
    component = INVALID_FILENAME_CHARACTERS.sub("_", value).rstrip(" .")
    if not component:
        raise ValueError(f"Empty filename component after sanitizing {value!r}")
    return component


def wikiru_portrait_filename(row: dict, digest: str | None = None) -> str:
    checksum = digest or row["sha256"]
    form = row["form"].replace("_", "-")
    return (
        f"{_safe_filename_component(row['config_name'])}__wikiru__"
        f"{_safe_filename_component(form)}__{checksum[:8]}.png"
    )


def _normalize_jp(value: str) -> str:
    return re.sub(
        r"\s+",
        "",
        value.replace("（", "(").replace("）", ")"),
    )


DUAL_FORM_OVERRIDES = {
    _normalize_jp("ホシノ(臨戦)防御型"): {
        "config_name": "Hoshino (Battle)",
        "form": "primary_defense",
        "include_for_identity_training": True,
    },
    _normalize_jp("ホシノ(臨戦)攻撃型"): {
        "config_name": "Hoshino (Battle)",
        "form": "alternate_attack",
        "include_for_identity_training": False,
    },
    _normalize_jp("シュエリン(水着)"): {
        "config_name": "Shun (Swimsuit)",
        "form": "alternate",
        "include_for_identity_training": False,
    },
}


class _PortraitImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.casefold() != "img":
            return
        values = dict(attrs)
        if (
            values.get("width") == "60"
            and values.get("height") == "60"
            and values.get("data-src")
            and values.get("alt")
        ):
            self.images.append(values)


def _fetch(url: str, referer: str | None = None) -> tuple[bytes, dict[str, str]]:
    # Keep network modules out of the offline ``--check`` path.  The packaged
    # project Python runtime may omit ``_socket`` even though its image/JSON
    # tooling is sufficient to audit an already downloaded portrait library.
    import urllib.request

    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read(), dict(response.headers.items())
        except Exception as error:  # pragma: no cover - network-dependent retry
            last_error = error
    raise RuntimeError(f"Unable to download {url}: {last_error}")


def _source_jp_name(alt: str) -> str:
    stem = alt.removesuffix(".png")
    for suffix in (
        "_icon_立ち絵準拠",
        "_icon_v2",
        "_icon_2",
        "_icon2",
        "_仮icon",
        "_icon",
    ):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    if stem.endswith("_水着"):
        stem = f"{stem[:-3]}(水着)"
    return _normalize_jp(stem)


def _catalog_lookup() -> dict[str, str]:
    rows = json.loads(STATIC_DEFAULT_CONFIG)["student_names"]
    lookup: dict[str, str] = {}
    for row in rows:
        key = _normalize_jp(row["JP_name"])
        if key in lookup:
            raise ValueError(f"Duplicate Japanese catalog alias: {row['JP_name']}")
        lookup[key] = row["Global_name"]
    return lookup


def parse_page(page_bytes: bytes) -> list[dict]:
    parser = _PortraitImageParser()
    parser.feed(page_bytes.decode("utf-8"))
    if len(parser.images) != EXPECTED_REMOTE_IMAGES:
        raise ValueError(
            f"Wikiru page changed: expected {EXPECTED_REMOTE_IMAGES} portrait images, "
            f"found {len(parser.images)}"
        )

    catalog = _catalog_lookup()
    mapped: list[dict] = []
    unknown: list[str] = []
    for image in parser.images:
        source_name = _source_jp_name(image["alt"])
        override = DUAL_FORM_OVERRIDES.get(source_name)
        if override is None:
            config_name = catalog.get(source_name)
            if config_name is None:
                unknown.append(source_name)
                continue
            override = {
                "config_name": config_name,
                "form": "primary",
                "include_for_identity_training": True,
            }
        mapped.append(
            {
                "config_name": override["config_name"],
                "source_jp_name": source_name,
                "source_alt": image["alt"],
                "form": override["form"],
                "include_for_identity_training": override[
                    "include_for_identity_training"
                ],
                "source_url": urllib.parse.urljoin(PAGE_URL, image["data-src"]),
            }
        )

    if unknown:
        raise ValueError(
            "Unmapped Wikiru Japanese names; add confirmed CN/Global mappings first:\n"
            + "\n".join(sorted(unknown))
        )
    if len(mapped) != EXPECTED_REMOTE_IMAGES:
        raise ValueError(f"Mapped {len(mapped)} of {EXPECTED_REMOTE_IMAGES} images")
    selected = [row for row in mapped if row["include_for_identity_training"]]
    selected_names = {row["config_name"] for row in selected}
    if len(selected) != EXPECTED_TRAINING_IMAGES:
        raise ValueError(f"Expected {EXPECTED_TRAINING_IMAGES} selected images")
    if len(selected_names) != EXPECTED_IDENTITIES:
        raise ValueError(f"Expected {EXPECTED_IDENTITIES} selected identities")
    return mapped


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise ValueError("Downloaded portrait is not a PNG")
    return struct.unpack(">II", payload[16:24])


def _download_one(row: dict) -> tuple[dict, bytes]:
    payload, headers = _fetch(row["source_url"], PAGE_URL)
    if headers.get("Content-Type", "").split(";", 1)[0] != "image/png":
        raise ValueError(
            f"Unexpected content type for {row['source_url']}: "
            f"{headers.get('Content-Type')}"
        )
    width, height = _png_dimensions(payload)
    if (width, height) not in EXPECTED_DIMENSIONS:
        raise ValueError(
            f"Unexpected portrait dimensions for {row['source_url']}: {width}x{height}"
        )
    digest = hashlib.sha256(payload).hexdigest()
    complete = dict(row)
    complete.update(
        {
            "file": wikiru_portrait_filename(row, digest),
            "sha256": digest,
            "width": width,
            "height": height,
            "bytes": len(payload),
        }
    )
    return complete, payload


def download() -> dict:
    page_bytes, page_headers = _fetch(PAGE_URL)
    mapped = parse_page(page_bytes)
    with ThreadPoolExecutor(max_workers=8) as executor:
        downloaded = list(executor.map(_download_one, mapped))

    entries = [row for row, _ in downloaded]
    dimension_counts: dict[str, int] = {}
    for row in entries:
        key = f"{row['width']}x{row['height']}"
        dimension_counts[key] = dimension_counts.get(key, 0) + 1
    if {
        tuple(int(part) for part in key.split("x")): count
        for key, count in dimension_counts.items()
    } != EXPECTED_DIMENSIONS:
        raise ValueError(f"Unexpected Wikiru dimension distribution: {dimension_counts}")
    filenames = [row["file"] for row in entries]
    if len(filenames) != len(set(filenames)):
        raise ValueError("Wikiru returned duplicate portrait bytes")

    expected_files = set(filenames)
    if OUTPUT_DIR.exists():
        extra_files = {
            path.name for path in OUTPUT_DIR.glob("*.png")
        } - expected_files
        if extra_files:
            raise ValueError(
                "Unexpected existing Wikiru portrait files: "
                + ", ".join(sorted(extra_files))
            )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for row, payload in downloaded:
        path = OUTPUT_DIR / row["file"]
        if path.exists() and path.read_bytes() != payload:
            raise ValueError(f"Existing portrait does not match expected bytes: {path}")
        if not path.exists():
            path.write_bytes(payload)

    manifest = {
        "version": 1,
        "source_page": PAGE_URL,
        "capture_date": CAPTURE_DATE,
        "portrait_index_sha256": hashlib.sha256(
            json.dumps(
                mapped,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "page_etag": page_headers.get("ETag"),
        "page_last_modified": page_headers.get("Last-Modified"),
        "copyright_notice": (
            "The source site states that image copyrights belong to their rights "
            "holders and asks readers not to reproduce or reuse the images."
        ),
        "image_count": len(entries),
        "selected_training_image_count": sum(
            row["include_for_identity_training"] for row in entries
        ),
        "selected_identity_count": len(
            {
                row["config_name"]
                for row in entries
                if row["include_for_identity_training"]
            }
        ),
        "dimension_counts": dimension_counts,
        "entries": entries,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def check() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    if len(entries) != EXPECTED_REMOTE_IMAGES:
        raise ValueError(f"Manifest contains {len(entries)} images")
    expected_dimension_counts = {
        f"{width}x{height}": count
        for (width, height), count in EXPECTED_DIMENSIONS.items()
    }
    if manifest["dimension_counts"] != expected_dimension_counts:
        raise ValueError(
            f"Unexpected manifest dimension distribution: {manifest['dimension_counts']}"
        )
    seen_files: set[str] = set()
    selected_names: set[str] = set()
    selected_count = 0
    for row in entries:
        expected_filename = wikiru_portrait_filename(row)
        if row["file"] != expected_filename:
            raise ValueError(
                f"Non-auditable Wikiru portrait filename: {row['file']} "
                f"(expected {expected_filename})"
            )
        if row["file"] in seen_files:
            raise ValueError(f"Duplicate manifest file: {row['file']}")
        seen_files.add(row["file"])
        payload = (OUTPUT_DIR / row["file"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f"Portrait checksum mismatch: {row['file']}")
        if _png_dimensions(payload) != (row["width"], row["height"]):
            raise ValueError(f"Portrait dimension mismatch: {row['file']}")
        if row["include_for_identity_training"]:
            selected_count += 1
            selected_names.add(row["config_name"])
    if selected_count != EXPECTED_TRAINING_IMAGES:
        raise ValueError(f"Selected {selected_count} training images")
    if len(selected_names) != EXPECTED_IDENTITIES:
        raise ValueError(f"Selected {len(selected_names)} training identities")
    disk_files = {path.name for path in OUTPUT_DIR.glob("*.png")}
    if disk_files != seen_files:
        missing = sorted(seen_files - disk_files)
        extra = sorted(disk_files - seen_files)
        raise ValueError(f"Wikiru portrait file mismatch: missing={missing}, extra={extra}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the committed manifest and files without network access.",
    )
    args = parser.parse_args()
    manifest = check() if args.check else download()
    print(
        json.dumps(
            {
                "images": manifest["image_count"],
                "selected_images": manifest["selected_training_image_count"],
                "selected_identities": manifest["selected_identity_count"],
                "training_performed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
