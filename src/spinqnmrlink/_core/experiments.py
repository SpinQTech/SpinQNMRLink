# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Protocol-preserving experiment orchestration for SpinQNMRLink."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import math
import time
from typing import Any, Dict, Mapping, Optional




logger = logging.getLogger("spinq.experiments")


def _json_safe(value: Any) -> Any:
    """Convert supported scientific values without silently stringifying data."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("experiment result contains a non-finite float")
        return value
    if isinstance(value, complex):
        return {"real": _json_safe(value.real), "imag": _json_safe(value.imag)}
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        non_string_keys = [key for key in value if not isinstance(key, str)]
        if non_string_keys:
            raise TypeError("experiment result mappings require string keys")
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        raise TypeError("experiment result sets have no stable JSON ordering")
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return _json_safe(tolist())
    item = getattr(value, "item", None)
    if callable(item):
        return _json_safe(item())
    raise TypeError(
        f"experiment result value is not JSON serializable: {type(value).__name__}"
    )


def serialize_result_document(
    document: Mapping[str, Any], *, indent: Optional[int] = 2
) -> str:
    """Serialize a result document without lossy implicit string conversion."""

    if not isinstance(document, Mapping):
        raise TypeError("result document must be a mapping")
    return json.dumps(
        _json_safe(document),
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
    )
