from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PatchOperation(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str
    value: Union[Any, None] = None

    @field_validator("path")
    def validate_path(cls, value: str) -> str:
        if value != "" and not value.startswith("/"):
            raise ValueError("json-pointer paths must start with '/' or be empty")
        return value


class SyncPullMessage(BaseModel):
    type: Literal["pull"]
    resource: Literal["config", "event", "gui", "static"]
    resource_id: Optional[str] = None
    include_diff_baseline: bool = Field(default=False, description="Whether to return baseline timestamp")


class SyncPatchMessage(BaseModel):
    type: Literal["patch"]
    resource: Literal["config", "event", "gui"]
    resource_id: Optional[str] = None
    timestamp: float
    ops: List[PatchOperation]


class ProviderRequest(BaseModel):
    type: Literal["static_request", "status_request"]
    resource_id: Optional[str] = None


class CommandMessage(BaseModel):
    type: Literal["command"]
    command: str
    timestamp: float
    config_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HandshakeResponse(BaseModel):
    type: Literal["handshake_response"]
    response: str
    timestamp: float


class SyncPushPayload(BaseModel):
    type: Literal["patch"] = "patch"
    resource: Literal["config", "event", "gui"]
    resource_id: Optional[str] = None
    timestamp: float
    ops: List[PatchOperation]
    origin: Literal["backend", "filesystem", "frontend"] = "backend"
