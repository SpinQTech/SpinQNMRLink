# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Stable experiment identities independent of device connection state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass(frozen=True)
class ExperimentDescriptor:
    """One protocol-backed experiment and its operating prerequisites."""

    key: str
    device_type: str
    mode: Optional[str]
    experiment_type: str
    model: str
    title: str
    title_zh: str
    purpose: str
    purpose_zh: str
    calibrated: bool
    result_fields: Tuple[str, ...]


_ENTRIES = json.loads((Path(__file__).parent / "_core/catalogue.json").read_text(encoding="utf-8"))
_CATALOGUE = tuple(
    ExperimentDescriptor(**{k: v for k, v in entry.items() if k != "preset_key"}) for entry in _ENTRIES
)


def list_experiments(device_type=None, *, mode=None) -> Tuple[ExperimentDescriptor, ...]:
    """List all experiments offline; mode optionally selects TWO or THREE."""
    value = getattr(device_type, "value", device_type)
    if value not in (None, "lab", "triangulum"):
        raise ValueError("device_type must be lab or triangulum")
    mode = getattr(mode, "name", mode)
    if mode not in (None, "TWO", "THREE"):
        raise ValueError("mode must be TWO or THREE")
    return tuple(
        x
        for x in _CATALOGUE
        if (value is None or x.device_type == value)
        and (mode is None or x.mode is None or x.mode == mode)
    )


def get_experiment(key: str) -> ExperimentDescriptor:
    """Resolve an exact experiment key from the catalogue."""
    for item in _CATALOGUE:
        if item.key == key:
            return item
    raise KeyError("Unknown experiment: {}".format(key))


def _preset_key(key):
    get_experiment(key)
    return next(x["preset_key"] for x in _ENTRIES if x["key"] == key)
