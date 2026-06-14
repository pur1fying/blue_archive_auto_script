from __future__ import annotations

import contextlib
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .api.http import router as http_router
from .api.state import context
from .api.ws_control import router as control_router
from .api.ws_provider import router as provider_router
from .api.ws_remote import router as remote_router
from .api.ws_sync import router as sync_router
from .api.ws_trigger import router as trigger_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await context.startup()
    yield
    await context.shutdown()


app = FastAPI(title="BAAS Service Mode", lifespan=lifespan)

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
