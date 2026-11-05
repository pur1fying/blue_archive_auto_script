from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, root_validator, validator


class ServiceBaseModel(BaseModel):
    """Compatibility base for both Pydantic v1 and v2 runtimes."""

    def model_dump(self, *args, **kwargs):
        super_model_dump = getattr(super(), "model_dump", None)
        if callable(super_model_dump):
            return super_model_dump(*args, **kwargs)
        return self.dict(*args, **kwargs)


class PatchOperation(ServiceBaseModel):
    """JSON Patch operation sent over sync channels.

    Attributes:
        op: Operation name. Supports add, remove, and replace.
        path: JSON Pointer path within the target resource.
        value: New value for add/replace. Omitted for remove.
    """

    op: Literal["add", "remove", "replace"]
    path: str
    value: Union[Any, None] = None

    @validator("path")
    def validate_path(cls, value: str) -> str:
        if value != "" and not value.startswith("/"):
            raise ValueError("json-pointer paths must start with '/' or be empty")
        return value


class SyncPullMessage(ServiceBaseModel):
    """Request a full resource snapshot from the sync websocket.

    Attributes:
        type: Literal message discriminator, always ``pull``.
        resource: Resource family to load.
        resource_id: Config id for config/event resources; otherwise None.
        is_include_diff_baseline: Legacy flag accepted from both old and new field names.
    """

    type: Literal["pull"]
    resource: Literal["config", "event", "gui", "static", "setup_toml"]
    resource_id: Optional[str] = None
    is_include_diff_baseline: bool = Field(
        default=False,
        description="Whether to return baseline timestamp",
    )

    @root_validator(pre=True)
    def accept_legacy_include_diff_baseline(cls, values):
        if (
            isinstance(values, dict)
            and "is_include_diff_baseline" not in values
            and "include_diff_baseline" in values
        ):
            values["is_include_diff_baseline"] = values["include_diff_baseline"]
        return values


class SyncPatchMessage(ServiceBaseModel):
    """Apply a patch to a mutable resource through the sync websocket.

    Attributes:
        type: Literal message discriminator, always ``patch``.
        resource: Mutable resource family.
        resource_id: Config id for config/event resources; otherwise None.
        timestamp: Frontend snapshot timestamp used for conflict detection.
        ops: JSON Patch operations to apply.
    """

    type: Literal["patch"]
    resource: Literal["config", "event", "gui", "setup_toml"]
    resource_id: Optional[str] = None
    timestamp: float
    ops: List[PatchOperation]


class ProviderRequest(ServiceBaseModel):
    """Request provider-side static or status data.

    Attributes:
        type: Provider request kind.
        resource_id: Optional future extension point for resource-specific requests.
    """

    type: Literal["static_request", "status_request"]
    resource_id: Optional[str] = None


class CommandMessage(ServiceBaseModel):
    """Command envelope accepted by `/ws/trigger`.

    Attributes:
        type: Literal message discriminator, always ``command``.
        command: Runtime command name.
        timestamp: Client timestamp echoed in the command response.
        config_id: Target config id for config-scoped commands.
        payload: Command-specific arguments.
    """

    type: Literal["command"]
    command: str
    timestamp: float
    config_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HandshakeResponse(ServiceBaseModel):
    """Legacy handshake response model retained for typed consumers."""

    type: Literal["handshake_response"]
    response: str
    timestamp: float


class SyncPushPayload(ServiceBaseModel):
    """Backend-to-frontend sync push payload.

    Attributes:
        type: Literal message discriminator, always ``patch``.
        resource: Resource family that changed.
        resource_id: Config id for config/event resources; otherwise None.
        timestamp: Backend snapshot timestamp.
        ops: Patch operations representing the change.
        origin: Source that produced the change.
    """

    type: Literal["patch"] = "patch"
    resource: Literal["config", "event", "gui", "static", "setup_toml"]
    resource_id: Optional[str] = None
    timestamp: float
    ops: List[PatchOperation]
    origin: Literal["backend", "filesystem", "frontend"] = "backend"
