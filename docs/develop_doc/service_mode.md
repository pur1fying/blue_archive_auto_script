# Service Mode

BAAS service mode is started through `main.service.py`. The entry file name and uvicorn target remain stable:

```bash
python main.service.py --host 0.0.0.0 --port 8190 --log-level info
```

The supported CLI flags are `--host`, `--port`, `--reload`, and `--log-level`.

## Architecture

`service.app:app` is the public ASGI entrypoint. It only assembles FastAPI, CORS, lifespan, and route modules. Long-lived dependencies are held by `service.api.state.context`.

Route ownership:

- `service/api/http.py`: auth remember/logout and health.
- `service/api/ws_control.py`: control-channel authentication, heartbeat, password change, and auth revocation.
- `service/api/ws_sync.py`: config/event/gui/setup snapshots, JSON patch acknowledgements, config list, and filesystem push messages.
- `service/api/ws_provider.py`: log/status provider stream and static/status request replies.
- `service/api/ws_trigger.py`: command response websocket.
- `service/api/commands.py`: command dispatch from trigger messages into `ServiceRuntime`.
- `service/api/ws_remote.py`: scrcpy websocket proxy.
- `service/api/security.py`: shared origin policy, encrypted JSON frame helpers, control auth, and business-channel resume.
- `service/auth/`: owns password state, sessions, remember tokens, signing keys, ChaCha control frames, and secretstream transport.
- `service/conf/`: owns safe config path resolution, config initialization, resource path lookup, snapshots, patching, and filesystem watching.
- `service/update/`: owns setup.toml I/O, remote SHA checks, CDK validation, and update execution.
- `service/remote/`: owns scrcpy client, server jar asset, proxy callback setup, and cleanup.
- `service/types.py`: owns Pydantic message contracts shared by websocket routes.
- `service/utils/`: owns generic diff and log forwarding helpers.

## Public Interfaces

HTTP endpoints:

- `POST /auth/remember`: verifies a remember-session proof and sets `baas_remember`.
- `POST /auth/logout`: deletes `baas_remember`.
- `GET /health`: returns service status and auth public state.

WebSocket endpoints:

- `/ws/control`: `client_hello` -> `server_hello` -> initialize/authenticate/resume control messages. Sends `auth_ok`, heartbeat, pong, and auth revocation messages.
- `/ws/sync`: resumes a business session for channel `sync`. Supports `pull`, `patch`, and `list`; emits `snapshot`, `patch_ack`, `config_list`, and filesystem `patch` pushes.
- `/ws/provider`: resumes channel `provider`. Sends initial log history and runtime status; supports `static_request` and `status_request`.
- `/ws/trigger`: resumes channel `trigger`. Accepts `CommandMessage` and returns `command_response` with the original command and timestamp.
- `/ws/remote`: resumes channel `remote`, reads remote config, and proxies encrypted or plain scrcpy bytes according to the existing `decrypt` flag.

`/ws/remote_test` was a debug endpoint and is intentionally removed.

## Message Flow

Business websockets share the same resume pattern:

1. Client sends `client_hello`.
2. Server replies `server_hello`.
3. Client sends encrypted `resume_proof`.
4. Server replies encrypted `resume_ok` with `server_header`.
5. Client sends encrypted `stream_ready` with `client_header`.
6. The route switches to encrypted binary JSON frames through `SecretStreamBox`.

## Development Checks

```bash
python -m compileall -q service
python -m pytest tests/service
```

The service test suite uses lightweight fake contexts for protocol contracts so OCR, devices, and emulator state are not required for normal route tests.

Compatibility checks should continue to cover these imports:

```python
from service.auth import ServiceAuthManager
from service.conf.manager import ConfigManager
from service.runtime import ServiceRuntime
from service.update import check_for_update, read_setup_toml
from service.remote import ScrcpyClient
```
