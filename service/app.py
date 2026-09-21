from __future__ import annotations

import contextlib
import logging
import os
import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from .api.http import router as http_router
from .api.state import context
from .api.ws_control import router as control_router
from .api.ws_provider import router as provider_router
from .api.ws_remote import router as remote_router
from .api.ws_sync import router as sync_router
from .api.ws_trigger import router as trigger_router
from .transport.pipe_server import PipeTransportServer


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await context.startup()
    pipe_server = None
    pipe_name = os.getenv("BAAS_PIPE_NAME", "").strip()
    if pipe_name:
        pipe_server = PipeTransportServer(pipe_name, context)
        await pipe_server.start()
    try:
        yield
    finally:
        if pipe_server is not None:
            await pipe_server.close()
        await context.shutdown()


app = FastAPI(title="BAAS Service Mode", lifespan=lifespan)


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    logger = logging.getLogger("baas.http")
    started = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    logger.debug("HTTP request started method=%s path=%s client=%s", request.method, request.url.path, client)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "HTTP request failed method=%s path=%s client=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            client,
            (time.perf_counter() - started) * 1000,
        )
        raise
    logger.debug(
        "HTTP request completed method=%s path=%s status=%s client=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        client,
        (time.perf_counter() - started) * 1000,
    )
    return response

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origin_regex=os.getenv(
        "BAAS_SERVICE_CORS_ORIGIN_REGEX",
        r"^https?://(localhost|tauri\.localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$",
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    http_router,
    control_router,
    sync_router,
    provider_router,
    trigger_router,
    remote_router,
):
    app.include_router(router)

# TODO: Temporarily commented
# app.mount("/", StaticFiles(directory="service/dist", html=True), name="static")
