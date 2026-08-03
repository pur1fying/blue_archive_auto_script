# BAAS Service Mode Internals

`main.service.py` starts uvicorn with `service.app:app`. Keep that import path stable.

## Layout

- `service/app.py`: FastAPI assembly, lifespan, CORS, and router registration.
- `service/api/http.py`: `/auth/remember`, `/auth/logout`, `/health`.
- `service/api/security.py`: websocket origin checks, handshake helpers, stream JSON helpers, and shared auth envelopes.
- `service/api/ws_control.py`: `/ws/control` authentication and password-control channel.
- `service/api/ws_sync.py`: `/ws/sync` config snapshot, patch, list, and filesystem push messages.
- `service/api/ws_provider.py`: `/ws/provider` logs, status, static snapshots, and provider requests.
- `service/api/ws_trigger.py` and `service/api/commands.py`: `/ws/trigger` command envelope and command dispatch.
- `service/api/ws_remote.py`: `/ws/remote` scrcpy websocket proxy.
- `service/context.py`: long-lived service dependencies.
- `service/runtime.py`: async-friendly facade over BAAS core runtime.
- `service/conf/manager.py`: config/resource persistence, patching, and filesystem watching.
- `service/conf/initializer.py`: config file creation and migration.
- `service/auth/`: authentication models, crypto helpers, encrypted channels, and `ServiceAuthManager`.
- `service/update/`: setup.toml I/O, update checks, CDK validation, and update execution.
- `service/remote/`: scrcpy client, jar asset, and websocket proxy lifecycle helpers.
- `service/types.py`: Pydantic message contracts shared by websocket routes.
- `service/utils/`: generic helpers such as JSON patch diffing and log queue forwarding.

## Compatibility Rules

- Do not rename `main.service.py`.
- Do not change `service.app:app`.
- Do not change the CLI flags `--host`, `--port`, `--reload`, or `--log-level`.
- Keep formal network contracts compatible for `/auth/remember`, `/auth/logout`, `/health`, `/ws/control`, `/ws/sync`, `/ws/provider`, `/ws/trigger`, and `/ws/remote`.
- `/ws/remote_test` was a debug-only endpoint and has been removed.
- `service.runtime` and `service.remote.scrcpy` are import-light; device-heavy dependencies load only when remote/device features are used.

## Testing

Run service tests with:

```bash
python -m pytest tests/service
```

Run a basic import/compile check with:

```bash
python -m compileall -q service
```
