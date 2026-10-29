# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""One SDK for Lab and Triangulum devices."""

from ._core._version import __version__
from ._core.diagnostics import DisconnectEvent
from .api import SpinQNMRLink
from .catalogue import ExperimentDescriptor, get_experiment, list_experiments
from .config import LabSettings, SDKSettings, TriangulumSettings, load_settings
from .devices import DeviceCapabilities, DeviceType, LabDevice, TriangulumDevice
from .errors import (
    ConfigurationError,
    DeviceNotReadyError,
    ExperimentFailedError,
    ExperimentRejectedError,
    ExperimentTerminatedError,
    ExperimentTimeoutError,
    ModeMismatchError,
    SDKError,
    SubmissionOutcomeUnknownError,
)
from .experiments import ExperimentResult, PreparedExperiment
from .models import Circuit, ExperimentParameters, Gate, Gradient, Pulse, parameters_for

__all__ = [
    "__version__",
    "SpinQNMRLink",
    "DeviceType",
    "DeviceCapabilities",
    "DisconnectEvent",
    "LabDevice",
    "TriangulumDevice",
    "LabSettings",
    "TriangulumSettings",
    "SDKSettings",
    "load_settings",
    "ExperimentDescriptor",
    "get_experiment",
    "list_experiments",
    "ExperimentResult",
    "PreparedExperiment",
    "ExperimentParameters",
    "parameters_for",
    "Pulse",
    "Gradient",
    "Gate",
    "Circuit",
    "SDKError",
    "ConfigurationError",
    "DeviceNotReadyError",
    "ModeMismatchError",
    "ExperimentFailedError",
    "ExperimentRejectedError",
    "ExperimentTerminatedError",
    "ExperimentTimeoutError",
    "SubmissionOutcomeUnknownError",
]
