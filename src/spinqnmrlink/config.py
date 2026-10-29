# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Typed connection settings. Reading settings never creates clients."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from .errors import ConfigurationError


class ConnectionSettings(BaseModel):
    """Common connection values, validated without accessing hardware."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535, strict=True)
    account: SecretStr
    password: SecretStr
    connection_timeout: float = Field(default=10.0, gt=0)
    request_timeout: float = Field(default=10.0, gt=0)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        if not value.strip():
            raise ValueError("host must be non-empty")
        return value.strip()

    @field_validator("account", "password", mode="before")
    @classmethod
    def resolve_secret(cls, value):
        if isinstance(value, str) and value.startswith("env:"):
            variable = value[4:].strip()
            if not variable or variable not in os.environ:
                raise ValueError("credential environment variable is not set")
            value = os.environ[variable]
        secret = value.get_secret_value() if isinstance(value, SecretStr) else value
        if not isinstance(secret, str) or not secret:
            raise ValueError("credentials must be non-empty strings")
        return value


class LabSettings(ConnectionSettings):
    """Lab transport, request, event and reconnect settings (seconds)."""

    transport: str = "tcp"
    websocket_path: str = "/ws"
    websocket_secure: bool = False
    heartbeat_interval: float = Field(default=15, gt=0)
    heartbeat_missed_periods: int = Field(default=2, ge=1, strict=True)
    auto_reconnect: bool = True
    reconnect_initial_delay: float = Field(default=1, ge=0)
    reconnect_max_delay: float = Field(default=30, ge=0)
    reconnect_multiplier: float = Field(default=2, ge=1)
    max_frame_length: int = Field(default=16 * 1024 * 1024, gt=0, strict=True)
    response_cache_size: int = Field(default=256, gt=0, strict=True)
    event_queue_size: int = Field(default=256, gt=0, strict=True)
    retain_chart_points: bool = True
    device_id: Optional[str] = None

    @field_validator("transport")
    @classmethod
    def validate_transport(cls, value):
        if value not in ("tcp", "websocket"):
            raise ValueError("transport must be tcp or websocket")
        return value


class TriangulumSettings(ConnectionSettings):
    """Triangulum JSON WebSocket settings; heartbeat intervals use seconds."""

    websocket_path: str = ""
    websocket_secure: bool = False
    heartbeat_interval: float = Field(default=10, gt=0)
    heartbeat_timeout: float = Field(default=30, gt=0)
    max_message_bytes: int = Field(default=32 * 1024 * 1024, gt=0, strict=True)

    @field_validator("websocket_path")
    @classmethod
    def validate_path(cls, value):
        if value and not value.startswith("/"):
            raise ValueError("websocket_path must be empty or start with /")
        return value


class SDKSettings(BaseModel):
    """At most one Lab and one Triangulum per SDK."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    lab: Optional[LabSettings] = None
    triangulum: Optional[TriangulumSettings] = None


def load_settings(path) -> SDKSettings:
    """Load SDK settings; error messages never include credential values."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        settings = SDKSettings.model_validate(document)
        if settings.lab is None and settings.triangulum is None:
            raise ValueError("configure lab and/or triangulum")
        return settings
    except (OSError, ValueError, TypeError):
        # Pydantic errors include input values, so do not forward their text.
        raise ConfigurationError(
            "Invalid SDK configuration; check fields and credential environment variables"
        ) from None
