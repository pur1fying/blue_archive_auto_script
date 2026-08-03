from __future__ import annotations

import ipaddress
import os
import time
import re
from html import escape
from typing import Any, Dict
from urllib.parse import quote, urljoin, urlparse

from fastapi import APIRouter, HTTPException, Request, Response
import requests

from service.auth import AuthenticationError, b64d
from service.system_logging import clear_system_logs, read_system_logs, system_log_files

from .security import cookie_secure
from .state import REMEMBER_COOKIE_MAX_AGE, REMEMBER_COOKIE_NAME, context

router = APIRouter()
WIKI_ORIGIN = "https://baas.kiramei.cn"


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


@router.get("/system/logs")
async def system_logs(
    request: Request,
    limit: int = 2000,
    level: str = "",
    query: str = "",
) -> Dict[str, Any]:
    _require_loopback(request)
    return {
        "entries": read_system_logs(
            context.project_root,
            limit=max(1, min(limit, 10000)),
            level=level or None,
            query=query or None,
        ),
        "files": system_log_files(context.project_root),
    }


@router.post("/system/logs/clear")
async def clear_logs(request: Request) -> Dict[str, Any]:
    _require_loopback(request)
    clear_system_logs(context.project_root)
    return {"ok": True}


@router.post("/android/active-config")
async def android_active_config(request: Request, payload: dict[str, Any]) -> Dict[str, Any]:
    _require_android_loopback(request)
    config_id = str(payload.get("config_id") or "").strip()
    if not config_id:
        raise HTTPException(status_code=400, detail="config_id is required")
    return context.runtime.set_android_active_config(config_id)


@router.post("/android/toggle")
async def android_toggle(request: Request) -> Dict[str, Any]:
    _require_android_loopback(request)
    try:
        return await context.runtime.toggle_android_active_config(
            set_log=context.ensure_runtime_logger_attached
        )
    except Exception as exc:
        return {"status": "error", "type": exc.__class__.__name__, "error": str(exc)}


@router.get("/android/wiki")
async def android_wiki(request: Request, path: str = "/docs/zh/") -> Dict[str, Any]:
    _require_android_loopback(request)
    target = _resolve_wiki_target(path)
    try:
        response = requests.get(target, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"url": target, "html": response.text}


@router.get("/android/wiki/proxy")
async def android_wiki_proxy(request: Request, path: str = "/") -> Response:
    _require_android_loopback(request)
    target = _resolve_wiki_target(path, allow_assets=True)
    try:
        upstream = requests.get(target, timeout=15)
        upstream.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    content_type = upstream.headers.get("content-type", "")
    if "text/html" in content_type:
        body = _rewrite_wiki_html(upstream.text)
        return Response(body, media_type="text/html; charset=utf-8")
    if "text/css" in content_type or target.endswith(".css"):
        body = _rewrite_wiki_css(upstream.text)
        return Response(body, media_type="text/css; charset=utf-8")

    media_type = content_type.split(";", 1)[0] or "application/octet-stream"
    return Response(upstream.content, media_type=media_type)


def _require_android_loopback(request: Request) -> None:
    if os.environ.get("BAAS_ANDROID") != "1":
        raise HTTPException(status_code=404, detail="Not found")
    _require_loopback(request)


def _require_loopback(request: Request) -> None:
    host = request.client.host if request.client else ""
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        if host == "localhost":
            return
    raise HTTPException(status_code=404, detail="Not found")


def _resolve_wiki_target(path: str, allow_assets: bool = False) -> str:
    parsed = urlparse(path)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https" or parsed.netloc != "baas.kiramei.cn":
            raise HTTPException(status_code=400, detail="unsupported wiki host")
        return path
    else:
        normalized_path = "/" + path.lstrip("/")
        if not allow_assets and not normalized_path.startswith("/docs/"):
            normalized_path = "/docs/zh/"
        return urljoin(WIKI_ORIGIN, normalized_path)


def _wiki_proxy_url(value: str) -> str:
    if not value or value.startswith("#") or value.startswith("mailto:") or value.startswith("tel:"):
        return value
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return value
    absolute = urljoin(WIKI_ORIGIN, value)
    parsed_absolute = urlparse(absolute)
    if parsed_absolute.netloc != "baas.kiramei.cn":
        return value
    path = parsed_absolute.path or "/"
    if parsed_absolute.query:
        path = f"{path}?{parsed_absolute.query}"
    if parsed_absolute.fragment:
        path = f"{path}#{parsed_absolute.fragment}"
    return f"/android/wiki/proxy?path={quote(path, safe='')}"


def _rewrite_wiki_html(html: str) -> str:
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<script\b[^>]*/>", "", html, flags=re.IGNORECASE)
    html = re.sub(
        r"<link\b(?=[^>]*\brel=[\"']preload[\"'])(?=[^>]*\bas=[\"']script[\"'])[^>]*>",
        "",
        html,
        flags=re.IGNORECASE,
    )

    def replace_attr(match: re.Match[str]) -> str:
        prefix, quote_char, value = match.group(1), match.group(2), match.group(3)
        return f'{prefix}{quote_char}{escape(_wiki_proxy_url(value), quote=True)}{quote_char}'

    html = re.sub(
        r"(\s(?:href|src|action)=)([\"'])(.*?)\2",
        replace_attr,
        html,
        flags=re.IGNORECASE,
    )

    html = re.sub(
        r"(<head[^>]*>)",
        r"\1"
        "<style>"
        "html,body{min-height:100%;background:#fff;}"
        "body{margin:0;}"
        "script{display:none!important;}"
        "#nd-subnav,#nd-sidebar,[data-sidebar-placeholder],[data-toc-popover]{display:none!important;}"
        "#nd-docs-layout{display:block!important;min-height:100vh!important;}"
        "#nd-docs-layout main{display:block!important;max-width:none!important;padding:24px!important;}"
        "#nd-docs-layout article{max-width:100%!important;padding-top:24px!important;}"
        ".baas-site-home{min-height:100%!important;}"
        "</style>",
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    return html


def _rewrite_wiki_css(css: str) -> str:
    return _rewrite_css_urls(_unwrap_css_layers(css))


def _rewrite_css_urls(css: str) -> str:
    def repl(match: re.Match[str]) -> str:
        quote_char = match.group(1) or ""
        value = match.group(2)
        if value.startswith("data:") or value.startswith("#"):
            return match.group(0)
        rewritten = _wiki_proxy_url(value)
        return f"url({quote_char}{rewritten}{quote_char})"

    return re.sub(r"url\(\s*(['\"]?)(.*?)\1\s*\)", repl, css)


def _unwrap_css_layers(css: str) -> str:
    output: list[str] = []
    i = 0
    quote_char = ""
    escaped = False
    in_comment = False

    while i < len(css):
        char = css[i]
        next_char = css[i + 1] if i + 1 < len(css) else ""

        if in_comment:
            output.append(char)
            if char == "*" and next_char == "/":
                output.append(next_char)
                in_comment = False
                i += 2
            else:
                i += 1
            continue

        if quote_char:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote_char:
                quote_char = ""
            i += 1
            continue

        if char == "/" and next_char == "*":
            output.append(char + next_char)
            in_comment = True
            i += 2
            continue
        if char in {"'", '"'}:
            output.append(char)
            quote_char = char
            i += 1
            continue

        if css.startswith("@layer", i) and not _css_identifier(css[i - 1] if i else ""):
            cursor = i + 6
            while cursor < len(css) and css[cursor].isspace():
                cursor += 1
            while cursor < len(css) and css[cursor] not in "{;":
                cursor += 1
            if cursor < len(css) and css[cursor] == ";":
                i = cursor + 1
                continue
            if cursor < len(css) and css[cursor] == "{":
                close = _find_css_block_end(css, cursor)
                output.append(_unwrap_css_layers(css[cursor + 1 : close]))
                i = close + 1
                continue

        output.append(char)
        i += 1

    return "".join(output)


def _find_css_block_end(css: str, open_index: int) -> int:
    depth = 0
    quote_char = ""
    escaped = False
    in_comment = False

    for i in range(open_index, len(css)):
        char = css[i]
        next_char = css[i + 1] if i + 1 < len(css) else ""
        if in_comment:
            if char == "*" and next_char == "/":
                in_comment = False
            continue
        if quote_char:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote_char:
                quote_char = ""
            continue
        if char == "/" and next_char == "*":
            in_comment = True
            continue
        if char in {"'", '"'}:
            quote_char = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(css) - 1


def _css_identifier(char: str) -> bool:
    return bool(char) and (char.isalnum() or char in {"_", "-"})
