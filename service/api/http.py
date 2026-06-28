from __future__ import annotations

import time
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, HTTPException, Request, Response
import requests

from service.auth import AuthenticationError, b64d

from .security import cookie_secure
from .state import REMEMBER_COOKIE_MAX_AGE, REMEMBER_COOKIE_NAME, context

router = APIRouter()


@router.post("/auth/remember")
async def remember_auth(request: Request, response: Response, payload: dict[str, Any]) -> Dict[str, Any]:
    try:
        session_id = str(payload.get("session_id", ""))
        proof = b64d(str(payload.get("proof", "")))
        session = context.auth_manager.verify_remember_proof(session_id=session_id, proof=proof)
        token, expires_at = context.auth_manager.issue_remember_token(session)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    max_age = max(0, min(REMEMBER_COOKIE_MAX_AGE, int(expires_at - time.time())))
    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=cookie_secure(request),
        samesite="lax",
        path="/",
    )
    return {"ok": True, "expires_at": expires_at}


@router.post("/auth/logout")
async def logout_auth(request: Request, response: Response) -> Dict[str, Any]:
    response.delete_cookie(
        REMEMBER_COOKIE_NAME,
        httponly=True,
        secure=cookie_secure(request),
        samesite="lax",
        path="/",
    )
    return {"ok": True}


@router.get("/health")
async def health() -> Dict[str, Any]:
    statuses = context.runtime.current_status()
    auth_state = context.auth_manager.password_state
    return {
        "ok": True,
        "statuses": statuses,
        "auth": {
            "initialized": auth_state.initialized,
            "pwd_epoch": auth_state.pwd_epoch,
            "server_sign_public_key": context.auth_manager.server_public_key_b64(),
        },
    }


@router.post("/android/active-config")
async def android_active_config(payload: dict[str, Any]) -> Dict[str, Any]:
    config_id = str(payload.get("config_id") or "").strip()
    if not config_id:
        raise HTTPException(status_code=400, detail="config_id is required")
    return context.runtime.set_android_active_config(config_id)


@router.post("/android/toggle")
async def android_toggle() -> Dict[str, Any]:
    return await context.runtime.toggle_android_active_config()


@router.get("/android/wiki")
async def android_wiki(path: str = "/docs/zh/") -> Dict[str, Any]:
    parsed = urlparse(path)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https" or parsed.netloc != "baas.kiramei.cn":
            raise HTTPException(status_code=400, detail="unsupported wiki host")
        target = path
    else:
        normalized_path = "/" + path.lstrip("/")
        if not normalized_path.startswith("/docs/"):
            normalized_path = "/docs/zh/"
        target = urljoin("https://baas.kiramei.cn", normalized_path)
    try:
        response = requests.get(target, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"url": target, "html": response.text}
