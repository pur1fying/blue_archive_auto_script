from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import requests


MODEL_VERSION = "1.0.0"
RELEASE_TAG = "student-recognition-v" + MODEL_VERSION
RELEASE_BASE_URL = (
    "https://github.com/kosetsu905/blue_archive_auto_script_ai/"
    "releases/download/" + RELEASE_TAG
)
MODEL_FILES = ("student_encoder.onnx", "gallery.npz", "student_encoder.json")


class ModelDownloadError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksums(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and len(parts[0]) == 64:
            result[parts[1].lstrip("*")] = parts[0].lower()
    if set(result) != set(MODEL_FILES):
        raise ModelDownloadError("Release checksum manifest is incomplete")
    return result


def validate_model_dir(
    directory: Path,
    checksums: Optional[dict[str, str]] = None,
) -> bool:
    try:
        if any(not (directory / name).is_file() for name in MODEL_FILES):
            return False
        if checksums and any(sha256(directory / name) != checksums[name] for name in MODEL_FILES):
            return False
        metadata = json.loads((directory / "student_encoder.json").read_text(encoding="utf-8"))
        width = int(metadata["embedding_size"])
        gallery = np.load(directory / "gallery.npz", allow_pickle=False)
        embeddings = np.asarray(gallery["embeddings"], dtype=np.float32)
        ids = np.asarray(gallery["student_ids"])
        if embeddings.ndim != 2 or embeddings.shape[1] != width or len(ids) != len(embeddings):
            return False
        cv2.dnn.readNetFromONNX(str(directory / "student_encoder.onnx"))
        return True
    except (OSError, ValueError, KeyError, TypeError, cv2.error, json.JSONDecodeError):
        return False


def ensure_model_files(project_root: Path, timeout: float = 15.0) -> Path:
    cache_root = project_root / "config" / "cache" / "student_recognition"
    destination = cache_root / MODEL_VERSION
    checksum_path = destination / "SHA256SUMS"
    if checksum_path.is_file():
        try:
            checksums = parse_checksums(checksum_path.read_text(encoding="ascii"))
            if validate_model_dir(destination, checksums):
                return destination
        except (OSError, UnicodeError, ModelDownloadError):
            pass
    cache_root.mkdir(parents=True, exist_ok=True)
    try:
        checksum_response = requests.get(RELEASE_BASE_URL + "/SHA256SUMS", timeout=timeout)
        checksum_response.raise_for_status()
        checksums = parse_checksums(checksum_response.text)
        with tempfile.TemporaryDirectory(prefix=MODEL_VERSION + "-", dir=cache_root) as temporary:
            temporary_path = Path(temporary)
            for name in MODEL_FILES:
                response = requests.get(RELEASE_BASE_URL + "/" + name, timeout=timeout, stream=True)
                response.raise_for_status()
                target = temporary_path / name
                with target.open("wb") as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            stream.write(chunk)
                if sha256(target) != checksums[name]:
                    raise ModelDownloadError("Checksum mismatch for " + name)
            (temporary_path / "SHA256SUMS").write_text(checksum_response.text, encoding="ascii")
            if not validate_model_dir(temporary_path, checksums):
                raise ModelDownloadError("Downloaded model package is invalid")
            destination.mkdir(parents=True, exist_ok=True)
            for name in MODEL_FILES + ("SHA256SUMS",):
                os.replace(temporary_path / name, destination / name)
        return destination
    except (OSError, requests.RequestException, ModelDownloadError) as error:
        raise ModelDownloadError(str(error)) from error
