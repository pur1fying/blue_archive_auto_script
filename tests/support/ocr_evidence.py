"""Capture the actual OCR input and annotate full frames only in test reports."""
import copy
from functools import wraps
import hashlib
import inspect
import json
from pathlib import Path
import threading

from tests.runner.evidence import now
from tests.support.privacy import redact
from tests.support.serialization import json_default


def view_region(image):
    """Recover a rectangular NumPy view's coordinates without image matching."""
    import numpy as np
    if not isinstance(image, np.ndarray):
        return None, None
    root = image
    while isinstance(root.base, np.ndarray):
        root = root.base
    if root.ndim != 3 or image.ndim != 3 or root.shape[2] != image.shape[2]:
        return None, None
    if root.shape[1] * 9 != root.shape[0] * 16 or root.shape[0] < 720:
        return None, None
    if root.strides != image.strides or any(s <= 0 for s in image.strides):
        return None, None
    offset = image.ctypes.data - root.ctypes.data
    y, remainder = divmod(offset, root.strides[0])
    x, channel = divmod(remainder, root.strides[1])
    if channel or x + image.shape[1] > root.shape[1] or y + image.shape[0] > root.shape[0]:
        return None, None
    return root, [x, y, x + image.shape[1], y + image.shape[0]]


class OcrObserver:
    """Instance-local wrappers; forward the original arguments, result and error."""
    METHODS = ("get_region_res", "get_region_raw_res", "ocr_for_single_line", "ocr")

    def __init__(self, ocr, recorder, root):
        self.ocr, self.recorder, self.root = ocr, recorder, Path(root)
        self.local = threading.local()
        self.sessions = {}
        self.originals = {}

    def register(self, config_id, baas):
        self.sessions[config_id] = baas

    def install(self):
        for name in self.METHODS:
            original = getattr(self.ocr, name, None)
            if original is None:
                continue
            self.originals[name] = original
            setattr(self.ocr, name, self._wrap(name, original))
        return self

    def close(self):
        for name, original in self.originals.items():
            setattr(self.ocr, name, original)

    def _case(self, baas, source, logger):
        with self.recorder.lock:
            active = dict(self.recorder.active)
        collector = getattr(logger, "log_collector", None)
        config_id = getattr(collector, "config_id", None)
        if config_id in active:
            return active[config_id]
        for config_id, session in list(self.sessions.items()):
            if config_id in active and (session is baas or (source is not None and source is getattr(session, "latest_img_array", None))):
                return active[config_id]
        return next(iter(active.values())) if len(active) == 1 else None

    def _prepare(self, method, arguments):
        baas = arguments.get("baas")
        logger = arguments.get("_logger", getattr(baas, "logger", None))
        source, region, issue = None, None, ""
        if method == "get_region_res":
            source = getattr(baas, "latest_img_array", None)
            ratio = getattr(baas, "ratio", None)
            if ratio is not None:
                region = [int(v * ratio) for v in arguments["region"]]
        elif method == "get_region_raw_res":
            source = arguments.get("img")
            region = [int(v * arguments.get("ratio", 1)) for v in arguments["region"]]
        else:
            crop = arguments.get("origin_image")
            source, region = view_region(crop)
            if source is None:
                if crop is None and arguments.get("local_path"):
                    return None  # OCR model probes are not game-screen regions.
                issue = "Full-frame coordinates unavailable for a detached or transformed OCR input"
        case_id = self._case(baas, source, logger)
        if case_id is None:
            return None
        frame = None if source is None else source.copy()
        if frame is None:
            issue = issue or "The OCR call has no source screenshot"
        caller = inspect.currentframe().f_back
        while caller and (caller.f_code.co_filename == __file__ or caller.f_code.co_filename.replace('\\', '/').endswith('/core/ocr/ocr.py')):
            caller = caller.f_back
        site = {}
        if caller:
            file = Path(caller.f_code.co_filename)
            try:
                file = file.relative_to(self.root)
            except ValueError:
                pass
            site = {"file": str(file).replace('\\', '/'), "line": caller.f_lineno, "function": caller.f_code.co_name}
        entry = {"time": now(), "method": method, "label": arguments.get("log_info") or site.get("function", method),
                 "language": arguments.get("language"), "requested_region": arguments.get("region"),
                 "source_region": region, "source": site, "issue": issue}
        return case_id, frame, entry

    def _wrap(self, method, original):
        signature = inspect.signature(original)

        @wraps(original)
        def observed(*args, **kwargs):
            if getattr(self.local, "inside", False):
                return original(*args, **kwargs)
            prepared = None
            try:
                bound = signature.bind(*args, **kwargs)
                bound.apply_defaults()
                prepared = self._prepare(method, bound.arguments)
            except Exception as exc:
                self.recorder.ocr_gap("OCR observation could not capture input: " + type(exc).__name__)
            self.local.inside = True
            try:
                result = original(*args, **kwargs)
                if prepared:
                    prepared[2]["result"] = result
                return result
            except BaseException as exc:
                if prepared:
                    prepared[2]["error"] = {"type": type(exc).__name__, "message": str(exc)}
                raise
            finally:
                self.local.inside = False
                if prepared:
                    self.recorder.capture_ocr(*prepared)
        return observed


class OcrArtifacts:
    """Called on Recorder's writer thread, including encoding and annotation."""
    COLORS = [(40, 190, 40), (0, 150, 255), (220, 90, 190), (235, 170, 30)]

    def __init__(self, recorder):
        self.recorder = recorder
        self.groups = {}

    @staticmethod
    def _save_image(path, frame):
        import cv2
        ok, encoded = cv2.imencode(".png", frame)
        if not ok:
            raise RuntimeError("OCR evidence image encoding failed")
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(encoded.tobytes())
        temporary.replace(path)

    def write(self, case_id, frame, entry):
        import cv2
        summary = self.recorder.cases[case_id]["ocr_evidence"]
        directory = self.recorder.directory / case_id / "ocr"
        directory.mkdir(parents=True, exist_ok=True)
        entry = json.loads(json.dumps(redact(entry, self.recorder.secrets), default=json_default))
        with (directory / "calls.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        with self.recorder.lock:
            summary["calls"] += 1
            summary["log"] = f"{case_id}/ocr/calls.jsonl"
        if frame is None or frame.ndim != 3 or not entry.get("source_region"):
            with self.recorder.lock:
                summary["missing"] += 1
                summary["status"] = "incomplete"
            return
        height, width = frame.shape[:2]
        digest = hashlib.sha256(str(frame.shape).encode() + frame.tobytes()).hexdigest()
        key = case_id, digest
        if key not in self.groups:
            number = 1 + sum(k[0] == case_id for k in self.groups)
            stem = f"frame-{number:04d}"
            group = {"id": stem, "source_sha256": digest, "source_size": [width, height],
                     "display_size": [1280, 720], "resized_for_display": (width, height) != (1280, 720),
                     "original": f"{case_id}/ocr/{stem}-original.png",
                     "annotated": f"{case_id}/ocr/{stem}-regions.png", "calls": []}
            self.groups[key] = group
            self._save_image(self.recorder.directory / group["original"], frame)
        group = self.groups[key]
        # Match NumPy slice semantics (including truncation and clipping).
        x1, y1, x2, y2 = entry["source_region"]
        left, right, _ = slice(x1, x2).indices(width)
        top, bottom, _ = slice(y1, y2).indices(height)
        entry["effective_source_region"] = [left, top, right, bottom]
        entry["display_region"] = [round(left * 1280 / width), round(top * 720 / height),
                                   round(right * 1280 / width), round(bottom * 720 / height)]
        if right <= left or bottom <= top:
            entry["issue"] = "The effective OCR crop is empty"
            with self.recorder.lock:
                summary["missing"] += 1
        group["calls"].append(entry)
        canvas = frame.copy() if (width, height) == (1280, 720) else cv2.resize(frame, (1280, 720), interpolation=cv2.INTER_AREA)
        seen = set()
        for call in group["calls"]:
            label = str(call["label"])
            rect = tuple(call["display_region"])
            if (label, rect) in seen:
                continue
            seen.add((label, rect))
            color = self.COLORS[(len(seen) - 1) % len(self.COLORS)]
            x1, y1, x2, y2 = rect
            if x2 > x1 and y2 > y1:
                cv2.rectangle(canvas, (x1, y1), (x2 - 1, y2 - 1), color, 2)
            text = f"{len(seen)} {label}" if label.isascii() else f"OCR {len(seen)}"
            text = text[:42]
            size, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, .46, 1)
            tx = max(0, min(x1, 1278 - size[0]))
            ty = y1 - 5 if y1 >= size[1] + 8 else y2 + size[1] + 5
            ty = max(size[1] + 2, min(717 - baseline, ty))
            cv2.rectangle(canvas, (tx, ty - size[1] - 2), (tx + size[0] + 2, ty + baseline + 2), (20, 24, 30), -1)
            cv2.putText(canvas, text, (tx + 1, ty), cv2.FONT_HERSHEY_SIMPLEX, .46, color, 1, cv2.LINE_AA)
        self._save_image(self.recorder.directory / group["annotated"], canvas)
        metadata = directory / (group["id"] + ".json")
        temporary = metadata.with_suffix(".tmp")
        temporary.write_text(json.dumps(group, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temporary.replace(metadata)
        with self.recorder.lock:
            summary["status"] = "incomplete" if summary["missing"] else "captured"
            summary["groups"] = [copy.deepcopy(g) for (owner, _), g in self.groups.items() if owner == case_id]
