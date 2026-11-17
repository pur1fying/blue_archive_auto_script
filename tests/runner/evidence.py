import copy
import json
import queue
import threading
from datetime import datetime, timezone

from tests.support.privacy import redact


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


class RecordingQueue:
    """Logger destination inside the test host, not a recognition monkey patch."""
    def __init__(self, recorder, config_id, baas):
        self.recorder, self.config_id, self.baas = recorder, config_id, baas

    def put(self, record, block=True, timeout=None):
        self.recorder.log(self.config_id, self.baas, record)


class Recorder:
    def __init__(self, directory, cases, secrets=(), capacity=128):
        self.directory = directory
        self.cases = {c["case_id"]: c for c in cases}
        self.secrets = secrets
        self.active = {}
        self.messages = {key: [] for key in self.cases}
        self.system_dropped = 0
        self.lock = threading.RLock()
        self.closed = False
        self.queue = queue.Queue(capacity)
        for case in cases:
            case["ocr_evidence"] = {"status": "not_observed", "calls": 0, "missing": 0, "groups": []}
        from tests.support.ocr_evidence import OcrArtifacts
        self.ocr_artifacts = OcrArtifacts(self)
        self.writer = threading.Thread(target=self._write, name="test-evidence", daemon=True)
        self.writer.start()

    def bind(self, config_id, case_id):
        with self.lock:
            self.active[config_id] = case_id

    def unbind(self, config_id):
        with self.lock:
            self.active.pop(config_id, None)

    def log(self, config_id, baas, record):
        with self.lock:
            case_id = self.active.get(config_id)
        if case_id is None:
            return
        message = str(record.get("message", ""))
        key_frame = ("Stage ended with matched" in message or "Lesson status" in message
                     or message.startswith("Ocr ") or "available :" in message)
        self.capture(case_id, message, getattr(baas, "latest_img_array", None) if key_frame else None,
                     record.get("level", 1), required=key_frame)

    def system(self, record):
        try:
            with self.lock:
                if self.closed:
                    self.system_dropped += 1
                    return
                self.queue.put_nowait({"case_id": None, "frame": None, "time": now(),
                    "label": redact(str(record.get("message", "")), self.secrets), "level": record.get("level", 1)})
        except Exception:
            self.system_dropped += 1

    def capture(self, case_id, label, frame=None, level=1, required=False):
        # Take a copy at the actual logging point. Never fetch another screenshot,
        # wait for animation, retry recognition, or change a production result.
        try:
            item = {"case_id": case_id, "label": redact(str(label), self.secrets),
                    "level": level, "time": now(), "frame": None if frame is None else frame.copy()}
            with self.lock:
                if self.closed:
                    self.cases[case_id]["evidence_dropped"] += 1
                    return
                if required and frame is None:
                    self.cases[case_id]["evidence_dropped"] += 1
                self.messages[case_id].append(item["label"])
                self.queue.put_nowait(item)
        except Exception:
            with self.lock:
                self.cases[case_id]["evidence_dropped"] += 1

    def ocr_gap(self, message, case_id=None):
        with self.lock:
            owners = [case_id] if case_id is not None else list(self.active.values())
            for owner in owners:
                summary = self.cases[owner]["ocr_evidence"]
                summary["missing"] += 1
                summary["status"] = "incomplete"
                summary.setdefault("issues", []).append(redact(message, self.secrets))

    def capture_ocr(self, case_id, frame, entry):
        try:
            with self.lock:
                if self.closed:
                    self.ocr_gap("OCR evidence arrived after the recorder closed", case_id)
                    return
                self.queue.put_nowait({"kind": "ocr", "case_id": case_id, "frame": frame, "entry": entry})
        except Exception as exc:
            self.ocr_gap("OCR evidence could not be queued: " + type(exc).__name__, case_id)

    def _write(self):
        indices = {}
        while True:
            item = self.queue.get()
            try:
                if item is None:
                    return
                case_id = item.pop("case_id")
                frame = item.pop("frame")
                if item.get("kind") == "ocr":
                    self.ocr_artifacts.write(case_id, frame, item["entry"])
                    continue
                directory = self.directory / case_id if case_id is not None else self.directory
                directory.mkdir(exist_ok=True)
                if frame is not None:
                    import cv2
                    indices[case_id] = indices.get(case_id, 0) + 1
                    name = f"frame-{indices[case_id]:05d}.png"
                    ok, encoded = cv2.imencode(".png", frame)
                    if not ok:
                        raise RuntimeError("Screenshot encoding failed")
                    (directory / name).write_bytes(encoded.tobytes())
                    item["image"] = f"{case_id}/{name}"
                with (directory / ("events.jsonl" if case_id is not None else "startup.jsonl")).open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
                if case_id is None:
                    continue
                with self.lock:
                    case = self.cases[case_id]
                    case["log"] = f"{case_id}/events.jsonl"
                    if "image" in item:
                        case["evidence"].append(item)
            except Exception:
                if item is not None:
                    with self.lock:
                        if case_id is None:
                            self.system_dropped += 1
                        else:
                            self.cases[case_id]["evidence_dropped"] += 1
                            if item.get("kind") == "ocr":
                                self.ocr_gap("OCR evidence could not be written", case_id)
            finally:
                self.queue.task_done()

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(list(self.cases.values()))

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closed = True
        self.queue.put(None)
        self.queue.join()
        self.writer.join()
