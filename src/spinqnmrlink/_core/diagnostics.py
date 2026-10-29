# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Public connection-loss diagnostics, without authentication values."""

from dataclasses import dataclass
from typing import Any, Mapping, Tuple


@dataclass(frozen=True)
class DisconnectEvent:
    """Unexpected connection loss. Observers run away from receive threads."""

    device_type: str
    reason: str
    task_ids: Tuple[str, ...]
    occurred_at_utc: str
    diagnostics: Mapping[str, Any]


def safe_reason(reason, secrets):
    text = str(reason)
    for secret in sorted({value for value in secrets if value}, key=len, reverse=True):
        text = text.replace(secret, "<redacted>")
    return text
