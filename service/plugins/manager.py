from __future__ import annotations

import asyncio
import copy
import hashlib
import io
from itertools import islice
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import stat
import sys
import tempfile
import time
from typing import Any
import uuid
from zipfile import BadZipFile, ZipFile

from service.conf.paths import ConfigPathError, resolve_config_dir

from .errors import PluginError, require
from .schema import API_VERSION, CAPABILITIES, WINDOWS_RESERVED, identifier, json_size, validate_manifest, validate_value, with_defaults

MAX_ARCHIVE = 10 * 1024 * 1024
MAX_PACKAGE = 32 * 1024 * 1024
MAX_FILES = 256
MAX_JOBS = 128
ACTIVE = {"queued", "running"}


async def _blocking(function, *args):
    """Keep profile/file locks held until an in-flight disk mutation completes."""
    operation = asyncio.create_task(asyncio.to_thread(function, *args))
    try:
        return await asyncio.shield(operation)
    except asyncio.CancelledError:
        try:
            await operation
        finally:
            raise


def _read_json(path: Path, maximum: int) -> Any:
    require(not path.is_symlink() and path.is_file() and path.stat().st_size <= maximum,
            "INVALID_STORAGE", "Plugin metadata is missing, unsafe or too large.")
    try:
        def integer(value):
            if len(value) > 309:
                raise ValueError("oversized integer")
            return int(value)
        return json.loads(path.read_text(encoding="utf-8"), parse_int=integer,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (OSError, ValueError, RecursionError):
        raise PluginError("INVALID_STORAGE", "Plugin metadata is not valid JSON.") from None


class PluginManager:
    """JSON-only discovery, profile state and bounded disposable action workers."""

    def __init__(self, project_root: Path, runtime: Any, *, bundled_root: Path | None = None):
        self.root = Path(project_root).resolve()
        self.bundled_root = bundled_root or Path(__file__).parent / "bundled"
        self.external_root = self.root / "plugins"
        self.runtime = runtime
        self.__lock = None
        self.__slots = None
        self._jobs: dict[str, dict] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._requests: dict[tuple[str, str], tuple[str, bytes]] = {}
        self._cancelling: set[str] = set()
        self._android_workers = None

    @property
    def _lock(self):
        if self.__lock is None:
            self.__lock = asyncio.Lock()
        return self.__lock

    @property
    def _slots(self):
        if self.__slots is None:
            self.__slots = asyncio.Semaphore(2)
        return self.__slots

    def _profile(self, config_id: Any) -> Path:
        require(isinstance(config_id, str) and 0 < len(config_id) <= 128 and "\0" not in config_id
                and config_id == config_id.strip(),
                "INVALID_CONFIG", "A valid config ID is required.")
        require(not (self.root / "config").is_symlink(), "INVALID_CONFIG", "Unsafe config directory.")
        try:
            target = resolve_config_dir(self.root / "config", config_id)
        except (ConfigPathError, ValueError, OSError):
            raise PluginError("INVALID_CONFIG", "A valid config ID is required.") from None
        require(target.is_dir() and (target / "config.json").is_file()
                and not (target / "config.json").is_symlink(), "CONFIG_NOT_FOUND", "Config does not exist.")
        return target

    def _state(self, config_id: str) -> dict:
        path = self._profile(config_id) / "plugins.json"
        if not path.exists() and not path.is_symlink():
            return {"schema_version": 1, "plugins": {}}
        data = _read_json(path, 2 * 1024 * 1024)
        require(isinstance(data, dict) and data.get("schema_version") == 1 and isinstance(data.get("plugins"), dict),
                "INVALID_STORAGE", "Plugin profile state is invalid.")
        return data

    def _save(self, config_id: str, data: dict) -> None:
        directory = self._profile(config_id)
        target = directory / "plugins.json"
        require(not target.is_symlink(), "INVALID_STORAGE", "Unsafe plugin profile state.")
        encoded = json_size(data, 2 * 1024 * 1024)
        fd, temporary = tempfile.mkstemp(prefix=".plugins-", dir=directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _digest(directory: Path) -> str:
        """Trust is bound to every packaged byte, not just a mutable manifest."""
        digest = hashlib.sha256()
        size = 0
        entries = []
        for path in directory.rglob("*"):
            relative = path.relative_to(directory)
            require(len(relative.parts) <= 16 and len(relative.as_posix().encode()) <= 512,
                    "UNSAFE_PACKAGE", "Plugin package paths exceed their nesting or length limit.")
            entries.append(path)
            require(len(entries) <= MAX_FILES, "PACKAGE_TOO_LARGE", "Plugin package exceeds its file count limit.")
        for path in sorted(entries):
            require(not path.is_symlink(), "UNSAFE_PACKAGE", "Plugin packages cannot contain symbolic links.")
            if path.is_dir():
                continue
            require(path.is_file(), "UNSAFE_PACKAGE", "Plugin packages contain unsupported file types.")
            require("__pycache__" not in {part.casefold() for part in path.parts} and path.suffix.casefold() != ".pyc",
                    "UNSAFE_PACKAGE", "Plugin packages must contain source code, not bytecode caches.")
            size += path.stat().st_size
            require(size <= MAX_PACKAGE, "PACKAGE_TOO_LARGE", "Plugin package exceeds its limits.")
            name = path.relative_to(directory).as_posix().encode()
            content = path.read_bytes()
            digest.update(len(name).to_bytes(8, "big"))
            digest.update(name)
            digest.update(len(content).to_bytes(8, "big"))
            digest.update(content)
        return digest.hexdigest()

    def _discover(self) -> tuple[dict[str, dict], list[dict]]:
        found: dict[str, dict] = {}
        errors: list[dict] = []
        for source, root in (("builtin", self.bundled_root), ("external", self.external_root)):
            if not root.exists():
                continue
            if root.is_symlink() or not root.is_dir():
                errors.append({"source": source, "code": "UNSAFE_PACKAGE", "message": "Plugin directory is unsafe."})
                continue
            for directory in sorted(islice(root.iterdir(), 101)):
                if len(found) + len(errors) >= 100:
                    errors.append({"source": source, "code": "CATALOG_LIMIT", "message": "Plugin catalog exceeds 100 packages."})
                    break
                if directory.name.startswith("."):
                    continue
                diagnostic = {"source": source}
                try:
                    diagnostic["plugin_id"] = identifier(directory.name)
                    require(directory.is_dir() and not directory.is_symlink(), "UNSAFE_PACKAGE", "Plugin packages must be real directories.")
                    raw = _read_json(directory / "plugin.json", 262144)
                    if isinstance(raw, dict) and isinstance(raw.get("id"), str):
                        diagnostic["plugin_id"] = identifier(raw["id"])
                    manifest = validate_manifest(raw)
                    plugin_id = manifest["id"]
                    require(directory.name == plugin_id, "INVALID_ID", "Plugin directory and manifest ID must match.")
                    package = {"manifest": manifest, "source": source, "directory": directory, "digest": self._digest(directory)}
                    if plugin_id in found:
                        found[plugin_id]["error"] = {"code": "DUPLICATE_PLUGIN", "message": "Duplicate plugin ID; remove the conflicting package."}
                        raise PluginError("DUPLICATE_PLUGIN", "Duplicate plugin ID; remove the conflicting package.")
                    found[plugin_id] = package
                except PluginError as exc:
                    errors.append({**diagnostic, "code": exc.code, "message": str(exc)})
                except (OSError, ValueError, TypeError, KeyError, ArithmeticError, RecursionError):
                    errors.append({**diagnostic, "code": "INVALID_MANIFEST", "message": "Plugin manifest could not be read."})
        return found, errors

    def _package(self, plugin_id: Any) -> dict:
        identifier(plugin_id)
        packages, errors = self._discover()
        if plugin_id not in packages:
            diagnostic = next((e for e in errors if e.get("plugin_id") == plugin_id), None)
            if diagnostic:
                raise PluginError(diagnostic["code"], diagnostic["message"])
            raise PluginError("PLUGIN_NOT_FOUND", "Plugin does not exist.")
        package = packages[plugin_id]
        if package.get("error"):
            raise PluginError(package["error"]["code"], package["error"]["message"])
        return package

    @staticmethod
    def _record(state: dict, plugin_id: str) -> dict:
        record = state["plugins"].get(plugin_id, {})
        require(isinstance(record, dict) and type(record.get("revision", 0)) is int
                and record.get("revision", 0) >= 0 and isinstance(record.get("values", {}), dict),
                "INVALID_STORAGE", "Plugin profile state is invalid.")
        return record

    def _descriptor(self, package: dict, state: dict) -> dict:
        manifest = package["manifest"]
        record = self._record(state, manifest["id"])
        trusted = package["source"] == "builtin" or record.get("trusted_digest") == package["digest"]
        descriptor = {**copy.deepcopy(manifest), "source": package["source"],
                      "enabled": record.get("enabled") is True and trusted and not package.get("error"),
                      "trusted": trusted, "state": "error" if package.get("error") else "available"}
        descriptor["enabled"] = bool(descriptor["enabled"])
        if package.get("error"):
            descriptor["error"] = package["error"]
        elif record.get("enabled") is True and not trusted:
            descriptor["error"] = {"code": "TRUST_REQUIRED", "message": "Plugin changed; review and trust the new code before enabling it."}
        return descriptor

    async def catalog(self, config_id: str | None = None) -> dict:
        async with self._lock:
            state = await _blocking(self._state, config_id) if config_id is not None else {"plugins": {}}
            packages, errors = await _blocking(self._discover)
            return {"api_version": API_VERSION, "capabilities": list(CAPABILITIES),
                    "plugins": [self._descriptor(p, state) for p in packages.values()], "errors": errors}

    def _settings(self, config_id: str, package: dict, state: dict) -> dict:
        plugin_id = package["manifest"]["id"]
        record = self._record(state, plugin_id)
        values = with_defaults(package["manifest"]["settings_schema"], record.get("values", {}))
        # Empty defaults may lack required fields until a user supplies them.
        return {"plugin_id": plugin_id, "config_id": config_id, "revision": record.get("revision", 0), "values": values}

    async def settings(self, config_id: str, plugin_id: str) -> dict:
        async with self._lock:
            package = await _blocking(self._package, plugin_id)
            state = await _blocking(self._state, config_id)
            return self._settings(config_id, package, state)

    async def update_settings(self, config_id: str, payload: dict) -> dict:
        async with self._lock:
            plugin_id = payload.get("plugin_id")
            package = await _blocking(self._package, plugin_id)
            state = await _blocking(self._state, config_id)
            record = self._record(state, plugin_id)
            revision = payload.get("revision")
            require(type(revision) is int and revision == record.get("revision", 0),
                    "REVISION_CONFLICT", "Plugin settings changed; reload before saving.")
            require(isinstance(payload.get("values"), dict), "INVALID_SETTINGS", "Settings values must be an object.")
            values = with_defaults(package["manifest"]["settings_schema"], payload["values"])
            json_size(values)
            validate_value(package["manifest"]["settings_schema"], values)
            state["plugins"][plugin_id] = {**record, "values": values, "revision": revision + 1}
            await _blocking(self._save, config_id, state)
            return self._settings(config_id, package, state)

    async def set_enabled(self, config_id: str, payload: dict) -> dict:
        async with self._lock:
            plugin_id = payload.get("plugin_id")
            package = await _blocking(self._package, plugin_id)
            state = await _blocking(self._state, config_id)
            enabled = payload.get("enabled")
            require(type(enabled) is bool, "INVALID_REQUEST", "enabled must be a boolean.")
            require(not any(j["plugin_id"] == plugin_id and j["config_id"] == config_id and j["state"] in ACTIVE for j in self._jobs.values()),
                    "PLUGIN_BUSY", "Cancel running plugin actions before changing enablement.")
            record = self._record(state, plugin_id)
            if enabled and package["source"] == "external":
                require(record.get("trusted_digest") == package["digest"] or payload.get("trust_code") is True,
                        "TRUST_REQUIRED", "External plugins execute trusted Python code with your account's permissions; explicit trust is required.")
                record["trusted_digest"] = package["digest"]
            state["plugins"][plugin_id] = {**record, "enabled": enabled}
            await _blocking(self._save, config_id, state)
            return self._descriptor(package, state)

    def _job(self, config_id: str, job_id: Any) -> dict:
        self._profile(config_id)
        require(isinstance(job_id, str) and job_id in self._jobs and self._jobs[job_id]["config_id"] == config_id,
                "JOB_NOT_FOUND", "Plugin job does not exist for this config.")
        return self._jobs[job_id]

    def _transition(self, job: dict, state: str, **fields: Any) -> None:
        job.update(state=state, updated_at=int(time.time() * 1000), **fields)

    async def run(self, config_id: str, payload: dict, set_log=None) -> dict:
        async with self._lock:
            package = await _blocking(self._package, payload.get("plugin_id"))
            state = await _blocking(self._state, config_id)
            descriptor = self._descriptor(package, state)
            require(descriptor["enabled"], "PLUGIN_DISABLED", "Enable and trust this plugin before running it.")
            action = next((a for a in descriptor["actions"] if a["id"] == payload.get("action_id")), None)
            require(action is not None, "ACTION_NOT_FOUND", "Plugin action does not exist.")
            request_id = payload.get("request_id")
            try:
                require(isinstance(request_id, str) and str(uuid.UUID(request_id)) == request_id.lower(), "INVALID_REQUEST", "request_id must be a UUID.")
            except (ValueError, AttributeError):
                raise PluginError("INVALID_REQUEST", "request_id must be a UUID.") from None
            require(isinstance(payload.get("input", {}), dict), "INVALID_REQUEST", "Action input must be an object.")
            inputs = with_defaults(action["input_schema"], payload.get("input", {}))
            validate_value(action["input_schema"], inputs)
            settings = self._settings(config_id, package, state)["values"]
            validate_value(descriptor["settings_schema"], settings)
            fingerprint = json_size({"plugin_id": descriptor["id"], "action_id": action["id"], "input": inputs})
            key = (config_id, request_id)
            if key in self._requests:
                old_id, old_fingerprint = self._requests[key]
                require(fingerprint == old_fingerprint, "REQUEST_CONFLICT", "A request ID was already used with different input.")
                return copy.deepcopy(self._jobs[old_id])
            require(sum(j["state"] in ACTIVE for j in self._jobs.values()) < 8,
                    "JOB_QUEUE_FULL", "Plugin action queue is full.")
            if len(self._jobs) >= MAX_JOBS:
                oldest = next((i for i, j in self._jobs.items() if j["state"] not in ACTIVE), None)
                require(oldest is not None, "JOB_QUEUE_FULL", "Plugin job retention is full.")
                del self._jobs[oldest]
                self._requests = {k: v for k, v in self._requests.items() if v[0] != oldest}
            now = int(time.time() * 1000)
            job = {"id": str(uuid.uuid4()), "plugin_id": descriptor["id"], "action_id": action["id"],
                   "config_id": config_id, "state": "queued", "created_at": now, "updated_at": now}
            self._jobs[job["id"]] = job
            self._requests[key] = (job["id"], fingerprint)
            self._tasks[job["id"]] = asyncio.create_task(self._execute(job, package, action, inputs, settings, set_log), name="plugin-action")
            return copy.deepcopy(job)

    async def get_job(self, config_id: str, job_id: str) -> dict:
        async with self._lock:
            return copy.deepcopy(self._job(config_id, job_id))

    async def cancel(self, config_id: str, job_id: str, *, _internal=False) -> dict:
        async with self._lock:
            if _internal:
                job = self._jobs[job_id]
            else:
                job = self._job(config_id, job_id)
            task = self._tasks.get(job_id)
            if job["state"] in ACTIVE and task is not None and job_id not in self._cancelling:
                self._cancelling.add(job_id)
                task.cancel()
        if task is not None and not task.done():
            await asyncio.shield(asyncio.gather(task, return_exceptions=True))
        # A task cancelled before its first instruction does not run finally.
        if job["state"] in ACTIVE:
            self._transition(job, "cancelled")
        self._cancelling.discard(job_id)
        if task is not None and task.done():
            self._tasks.pop(job_id, None)
        return copy.deepcopy(job)

    async def stop_all(self) -> None:
        for job in list(self._jobs.values()):
            if job["state"] in ACTIVE:
                await self.cancel(job["config_id"], job["id"], _internal=True)

    async def stop_config(self, config_id: str) -> None:
        for job in list(self._jobs.values()):
            if job["config_id"] == config_id and job["state"] in ACTIVE:
                await self.cancel(config_id, job["id"], _internal=True)

    async def _execute(self, job: dict, package: dict, action: dict, inputs: dict, settings: dict, set_log) -> None:
        try:
            async with self._slots:
                # A queued job must not run a package changed since acceptance.
                require(await _blocking(self._digest, package["directory"]) == package["digest"], "PACKAGE_CHANGED", "Plugin changed while the action was queued.")
                self._transition(job, "running")
                if action["execution"] == "compute":
                    operation = self._compute(job, package, action, inputs, settings)
                else:
                    operation = self.runtime.run_plugin_device_task(job["config_id"], action["task_name"], set_log=set_log)
                timeout = action.get("timeout_seconds", 30 if action["execution"] == "compute" else 1800)
                operation = asyncio.create_task(operation)
                try:
                    result = await asyncio.wait_for(operation, timeout=timeout)
                except asyncio.CancelledError:
                    # Python 3.9.0 wait_for cancels its child without waiting for
                    # cleanup. Explicit ownership ensures worker/device teardown
                    # finishes before the public job becomes cancelled.
                    await asyncio.gather(operation, return_exceptions=True)
                    raise
                json_size(result)
                if "output_schema" in action:
                    try:
                        validate_value(action["output_schema"], result)
                    except PluginError:
                        raise PluginError("INVALID_RESULT", "Plugin result does not match its output schema.") from None
                self._transition(job, "succeeded", result=result)
        except asyncio.CancelledError:
            self._transition(job, "cancelled")
        except asyncio.TimeoutError:
            self._transition(job, "failed", error={"code": "ACTION_TIMEOUT", "message": "Plugin action timed out. Compute workers were terminated; device tasks may still be stopping."})
        except PluginError as exc:
            self._transition(job, "failed", error={"code": exc.code, "message": str(exc)})
        except Exception:
            self._transition(job, "failed", error={"code": "ACTION_FAILED", "message": "Plugin action failed; check host task status."})
        finally:
            self._tasks.pop(job["id"], None)

    async def _compute(self, job: dict, package: dict, action: dict, inputs: dict, settings: dict) -> Any:
        request = json_size({"entrypoint": action["entrypoint"], "input": inputs,
                             "context": {"api_version": 1, "plugin_id": job["plugin_id"], "config_id": job["config_id"], "settings": settings}}, 131072)
        if os.getenv("BAAS_ANDROID", "").lower() in {"1", "true", "yes", "on"}:
            from .android import AndroidWorkerPool

            if self._android_workers is None:
                self._android_workers = AndroidWorkerPool()
            content = await self._android_workers.run(job["id"], package["directory"], request, self._processes)
            return self._worker_result(content)
        # Keep OS essentials for supported Windows/Python installations, never BAAS secrets.
        environment = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL") if k in os.environ}
        launching = asyncio.create_task(asyncio.create_subprocess_exec(
            sys.executable, "-I", "-B", str(Path(__file__).with_name("worker.py")), str(package["directory"]),
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            cwd=package["directory"], env=environment, limit=131072,
            **({"start_new_session": True} if os.name == "posix" else {}),
        ))
        process = None
        close_windows_job = None
        try:
            try:
                process = await asyncio.shield(launching)
            except asyncio.CancelledError:
                process = await launching
                raise
            self._processes[job["id"]] = process
            if os.name == "nt":
                from .processes import windows_job
                close_windows_job = windows_job(process.pid)
            assert process.stdin is not None and process.stdout is not None
            process.stdin.write(request)
            await process.stdin.drain()
            process.stdin.close()
            chunks = []
            size = 0
            while True:
                chunk = await process.stdout.read(16384)
                if not chunk:
                    break
                size += len(chunk)
                require(size <= 131072, "RESULT_TOO_LARGE", "Plugin worker output exceeds its limit.")
                chunks.append(chunk)
            content = b"".join(chunks)
            await process.wait()
            require(process.returncode == 0, "WORKER_EXITED", "Plugin worker exited unexpectedly.")
            return self._worker_result(content)
        finally:
            # Own process group is stopped even when a plugin left child processes.
            if close_windows_job is not None:
                close_windows_job()
            if process is not None:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                elif process.returncode is None:
                    process.kill()
                await process.wait()
            self._processes.pop(job["id"], None)

    @staticmethod
    def _worker_result(content: bytes) -> Any:
        require(len(content) <= 131072, "RESULT_TOO_LARGE", "Plugin worker output exceeds its limit.")
        try:
            response = json.loads(content)
        except (ValueError, RecursionError):
            raise PluginError("INVALID_RESULT", "Plugin worker returned invalid JSON.") from None
        require(isinstance(response, dict), "INVALID_RESULT", "Plugin worker returned invalid data.")
        if response.get("ok") is not True:
            code = "RESULT_TOO_LARGE" if response.get("code") == "RESULT_TOO_LARGE" else "ACTION_FAILED"
            raise PluginError(code, "Plugin result exceeds 64 KiB." if code == "RESULT_TOO_LARGE" else "Plugin action failed.")
        result = response.get("result")
        json_size(result)
        return result

    async def install(self, archive: bytes | None) -> dict:
        async with self._lock:
            return await _blocking(self._install_sync, archive)

    def _install_sync(self, archive: bytes | None) -> dict:
        require(isinstance(archive, bytes) and 0 < len(archive) <= MAX_ARCHIVE,
                "INVALID_ARCHIVE", "A ZIP package of at most 10 MiB is required.")
        require(not self.external_root.is_symlink(), "UNSAFE_PACKAGE", "Plugin directory is unsafe.")
        self.external_root.mkdir(exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".install-", dir=self.external_root))
        try:
            try:
                with ZipFile(io.BytesIO(archive)) as zipped:
                    entries = zipped.infolist()
                    require(0 < len(entries) <= MAX_FILES and sum(i.file_size for i in entries) <= MAX_PACKAGE,
                            "PACKAGE_TOO_LARGE", "ZIP package exceeds its file or unpacked size limit.")
                    names = set()
                    filesystem_entries = set()
                    for info in entries:
                        path = PurePosixPath(info.filename)
                        mode = info.external_attr >> 16
                        raw_parts = info.filename.rstrip("/").split("/")
                        require(len(raw_parts) <= 16 and len(info.filename.encode()) <= 512,
                                "UNSAFE_ARCHIVE", "ZIP package paths exceed their nesting or length limit.")
                        canonical = "/".join(raw_parts).casefold()
                        for depth in range(1, len(raw_parts) + 1):
                            filesystem_entries.add("/".join(raw_parts[:depth]).casefold())
                        require(len(filesystem_entries) <= MAX_FILES, "PACKAGE_TOO_LARGE", "ZIP package exceeds its filesystem entry limit.")
                        require(not path.is_absolute() and ".." not in path.parts and "\\" not in info.filename
                                and ":" not in info.filename and "\0" not in info.orig_filename and canonical not in names
                                and all(part not in {"", ".", ".."} and part.rstrip(" .") == part
                                        and part.split(".")[0].casefold() not in WINDOWS_RESERVED for part in raw_parts)
                                and not info.flag_bits & 1 and not stat.S_ISLNK(mode)
                                and (stat.S_IFMT(mode) in {0, stat.S_IFREG, stat.S_IFDIR})
                                and "__pycache__" not in {part.casefold() for part in path.parts} and path.suffix.casefold() != ".pyc",
                                "UNSAFE_ARCHIVE", "ZIP package contains unsafe paths or unsupported entries.")
                        names.add(canonical)
                        target = temporary.joinpath(*path.parts)
                        if info.is_dir():
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with zipped.open(info) as source, target.open("xb") as destination:
                                shutil.copyfileobj(source, destination, 65536)
            except PluginError:
                raise
            except (BadZipFile, RuntimeError, OSError, ValueError, EOFError):
                raise PluginError("INVALID_ARCHIVE", "ZIP package could not be extracted.") from None
            manifest = validate_manifest(_read_json(temporary / "plugin.json", 262144))
            plugin_id = manifest["id"]
            existing, _ = self._discover()
            destination = self.external_root / plugin_id
            require(plugin_id not in existing and not destination.exists() and not destination.is_symlink(),
                    "PLUGIN_EXISTS", "A plugin with this ID already exists; uninstall it before replacing it.")
            self._digest(temporary)
            # Verify every compute entrypoint without importing any Python.
            for action in manifest["actions"]:
                if action["execution"] == "compute":
                    module = temporary.joinpath(*action["entrypoint"].split(":")[0].split("."))
                    require(module.with_suffix(".py").is_file() or (module / "__init__.py").is_file(),
                            "INVALID_ENTRYPOINT", "A declared compute module is missing.")
            os.replace(temporary, destination)
            return {**manifest, "source": "external", "enabled": False, "trusted": False, "state": "available"}
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    async def uninstall(self, plugin_id: str) -> dict:
        async with self._lock:
            identifier(plugin_id)
            require(not any(j["plugin_id"] == plugin_id and j["state"] in ACTIVE for j in self._jobs.values()),
                    "PLUGIN_BUSY", "Cancel running plugin actions before uninstalling this plugin.")
            return await _blocking(self._uninstall_sync, plugin_id)

    def _uninstall_sync(self, plugin_id: str) -> dict:
        require(not self.external_root.is_symlink(), "UNSAFE_PACKAGE", "Plugin directory is unsafe.")
        directory = self.external_root / plugin_id
        if not directory.exists():
            code = "BUILTIN_PLUGIN" if (self.bundled_root / plugin_id).exists() else "PLUGIN_NOT_FOUND"
            raise PluginError(code, "Bundled plugins cannot be uninstalled." if code == "BUILTIN_PLUGIN" else "Plugin does not exist.")
        require(directory.is_dir() and not directory.is_symlink(), "UNSAFE_PACKAGE", "Plugin directory is unsafe.")
        # Remove stale trust and settings in all real profiles before deletion.
        config_root = self.root / "config"
        if config_root.is_dir():
            for profile in config_root.iterdir():
                if profile.is_dir() and not profile.is_symlink() and (profile / "config.json").is_file():
                    state = self._state(profile.name)
                    if plugin_id in state["plugins"]:
                        del state["plugins"][plugin_id]
                        self._save(profile.name, state)
        shutil.rmtree(directory)
        return {"plugin_id": plugin_id, "uninstalled": True}
