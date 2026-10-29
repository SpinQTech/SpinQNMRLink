# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""SDK facade owning independent Lab and Triangulum device sessions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Union

from .config import SDKSettings, load_settings
from .devices import Device, DeviceType, LabDevice, TriangulumDevice
from .errors import ConfigurationError, SDKError


class SpinQNMRLink:
    """Manage one configured device of each type without connecting implicitly."""

    def __init__(self, settings: SDKSettings) -> None:
        if not isinstance(settings, SDKSettings):
            raise TypeError("settings must be SDKSettings")
        self._devices: Dict[DeviceType, Device] = {}
        if settings.lab is not None:
            self._devices[DeviceType.LAB] = LabDevice(settings.lab)
        if settings.triangulum is not None:
            self._devices[DeviceType.TRIANGULUM] = TriangulumDevice(settings.triangulum)
        if not self._devices:
            raise ConfigurationError("Configure lab and/or triangulum")

    @classmethod
    def from_config(cls, path: Union[str, Path]) -> "SpinQNMRLink":
        """Read configuration and create unconnected device objects."""
        return cls(load_settings(path))

    def device(self, device_type: Union[str, DeviceType]) -> Device:
        """Return the selected device; no automatic fallback between devices."""
        kind = DeviceType(device_type)
        if kind not in self._devices:
            raise ConfigurationError("{} is not configured".format(kind.value))
        return self._devices[kind]

    def close(self, *, timeout: float = 5.0) -> None:
        """Attempt cleanup of every device even if one cleanup fails."""
        failures = []
        for device in self._devices.values():
            try:
                device.close(timeout=timeout)
            except Exception as exc:
                failures.append(exc)
        if failures:
            raise SDKError("One or more devices could not be closed") from failures[0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.close()
        except Exception:
            if exc_type is None:
                raise
            logging.getLogger("spinqnmrlink").exception("SDK cleanup failed during error handling")
