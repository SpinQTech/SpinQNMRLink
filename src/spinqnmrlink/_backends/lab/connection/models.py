# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Stable public data models for the communication SDK."""

from __future__ import annotations

from dataclasses import dataclass
import json
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from ..utils.types import QubitMode


@dataclass(frozen=True)
class QubitModeCapability:
    """Explain whether one qubit mode can be submitted right now.

    ``sdk_supported`` describes local SDK code capability. ``server_rejected``
    only becomes true after the authenticated server explicitly returns the
    protocol ``QUBIT_MODE_UNSUPPORTED`` error. A different
    ``authoritative_mode`` only means the server currently operates another
    business domain; it does not prove permanent lack of support.
    """

    mode: QubitMode
    sdk_supported: bool
    authoritative_mode: Optional[QubitMode]
    server_rejected: bool
    can_submit_now: bool
    reason: str


class TaskState(str, Enum):
    """Five server-authoritative task states defined by protocol v2.0."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True)
class Task:
    """Protocol Task model without interpreting experiment-specific params."""

    type: str
    id: str
    device_id: str
    params: str
    create_time: Optional[int] = None
    account: Optional[str] = None
    name: str = ""
    extra: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    state: Optional[str] = None

    @property
    def known_state(self) -> Optional[TaskState]:
        """Return the known state while preserving unknown raw state strings."""
        if self.state is None:
            return None
        try:
            return TaskState(self.state)
        except (TypeError, ValueError):
            return None

    @classmethod
    def from_dict(cls, value: Dict[str, Any], *, for_submission: bool = False) -> "Task":
        if not isinstance(value, dict):
            raise TypeError("task must be a dictionary")
        extra = value.get("extra")
        # An empty ``extra`` object must be valid JSON text when its field
        # is present. Normalize blank strings to an empty JSON object.
        if isinstance(extra, str) and not extra.strip():
            extra = "{}"
        task = cls(
            type=value.get("type") or "",
            id=value.get("id") or "",
            device_id=value.get("deviceId") or "",
            params=value.get("params") if value.get("params") is not None else "",
            create_time=value.get("createTime"),
            account=value.get("account"),
            name=value.get("name") or "",
            extra=extra,
            start_time=value.get("startTime"),
            end_time=value.get("endTime"),
            state=value.get("state"),
        )
        if for_submission:
            task.validate_submission()
        return task

    def validate_submission(self) -> None:
        missing = [
            name
            for name, value in (
                ("type", self.type),
                ("id", self.id),
                ("deviceId", self.device_id),
                ("params", self.params),
            )
            if not isinstance(value, str) or not value
        ]
        if missing:
            raise ValueError(f"Task submission is missing required fields: {', '.join(missing)}")
        if self.create_time is not None and (
            isinstance(self.create_time, bool) or not isinstance(self.create_time, int)
        ):
            raise ValueError("Task createTime must be an integer Unix timestamp in milliseconds")
        try:
            parsed_params = json.loads(self.params)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Task params must be valid JSON text") from exc
        if not isinstance(parsed_params, dict):
            raise ValueError("Task params JSON text must encode an object")
        if self.extra is not None:
            if not isinstance(self.extra, str):
                raise ValueError("Task extra must be JSON text or null")
            try:
                json.loads(self.extra)
            except json.JSONDecodeError as exc:
                raise ValueError("Task extra must be valid JSON text or null") from exc

    def to_submission_dict(self) -> Dict[str, Any]:
        """Return the client-owned fields accepted by c_add_exp_task_req."""
        self.validate_submission()
        result: Dict[str, Any] = {
            "type": self.type,
            "id": self.id,
            "deviceId": self.device_id,
            "name": self.name,
            "params": self.params,
        }
        if self.create_time is not None:
            result["createTime"] = self.create_time
        if self.account is not None:
            result["account"] = self.account
        if self.extra is not None:
            result["extra"] = self.extra
        return result


@dataclass(frozen=True)
class DeviceInfo:
    """Stable fields from s_post_device_info."""

    connected: bool
    lock_state: bool
    temperature: float

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "DeviceInfo":
        return cls(
            connected=bool(value.get("connected", False)),
            lock_state=bool(value.get("lockState", False)),
            temperature=float(value.get("temperature", 0.0)),
        )


@dataclass(frozen=True)
class ChartChunk:
    """One ordered ChartData chunk received from the service."""

    task_id: str
    group: str
    chart_name: str
    points: Tuple[Tuple[float, float], ...]
    path: Optional[str] = None
    qubit: Optional[str] = None
    step: Optional[str] = None

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "ChartChunk":
        return cls(
            task_id=str(value.get("taskId", "")),
            group=str(value.get("group", "")),
            chart_name=str(value.get("chart_name", "")),
            path=value.get("path") or None,
            qubit=value.get("qubit") or None,
            step=value.get("step") or None,
            points=tuple((float(point[0]), float(point[1])) for point in value.get("points", [])),
        )
