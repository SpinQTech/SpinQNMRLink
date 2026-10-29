# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Tolerant normalization of protocol-defined common JSON payloads."""

from __future__ import annotations

from typing import Any, Dict

from ..utils.types import MachineType


_RESPONSE_IDS = {
    MachineType.MSG_RES_USER_LOGIN,
    MachineType.MSG_RES_USER_LOGOUT,
    MachineType.MSG_RES_ADD_EXP_TASK_RES,
    MachineType.MSG_RES_TERMINATE_EXP_TASK_RES,
}

_TASK_DATA_IDS = {
    MachineType.MSG_POST_EXP_STEP_CHANGED,
    MachineType.MSG_POST_EXP_DATA_UPDATED,
    MachineType.MSG_POST_EXP_FINISHED,
}

_CHART_BOUNDARY_IDS = {
    MachineType.MSG_POST_EXP_CHART_UPDATED_STARTED,
    MachineType.MSG_POST_EXP_CHART_UPDATED_FINISHED,
}


def normalize_common_json(msg_id: str, payload: Any) -> Dict[str, Any]:
    """Copy a common payload, preserve unknown keys and fill optional fields.

    Missing required response fields are assigned conservative failure values;
    malformed success must never be inferred from absent data.
    """
    data = dict(payload) if isinstance(payload, dict) else {}

    if msg_id in _RESPONSE_IDS:
        data.setdefault("code", 999)
        data.setdefault("message", "")
        if msg_id == MachineType.MSG_RES_USER_LOGIN:
            data.setdefault("sessionId", "")
        if msg_id in (
            MachineType.MSG_RES_ADD_EXP_TASK_RES,
            MachineType.MSG_RES_TERMINATE_EXP_TASK_RES,
        ):
            data.setdefault("taskId", None)
    elif msg_id == MachineType.MSG_POST_EXP_QUEUE_UPDATE:
        if not isinstance(data.get("queue"), list):
            data["queue"] = []
        data.setdefault("currentTaskId", None)
    elif msg_id == MachineType.MSG_POST_EXP_REMOVED:
        data.setdefault("taskId", None)
    elif msg_id == MachineType.MSG_POST_EXP_STARTED:
        data.setdefault("taskId", "")
        if not isinstance(data.get("queue"), list):
            data["queue"] = []
    elif msg_id in _TASK_DATA_IDS:
        data.setdefault("taskId", "")
        data.setdefault("data", None)
    elif msg_id in _CHART_BOUNDARY_IDS:
        data.setdefault("taskId", "")
        for field in ("group", "path", "qubit", "step"):
            data.setdefault(field, None)
    elif msg_id == MachineType.MSG_POST_INFO:
        data.setdefault("connected", False)
        data.setdefault("lockState", False)
        data.setdefault("temperature", 0.0)
    elif msg_id == MachineType.MSG_POST_PARAM:
        for field in (
            "pulseParam",
            "ppsParam",
            "sampleParam",
            "lockParam",
            "shimmingParam",
        ):
            if not isinstance(data.get(field), dict):
                data[field] = {}
        data.setdefault("currentShimming", 0.0)
    elif msg_id == MachineType.MSG_POST_SAMPLE_CALIBRATION:
        data.setdefault("sampleLock", None)
        data.setdefault("calibrateResult", None)

    return data
