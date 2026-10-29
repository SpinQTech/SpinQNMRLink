# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Errors describing device and task outcomes without conflating them."""


class SDKError(RuntimeError):
    """Base SDK error."""


class ConfigurationError(SDKError, ValueError):
    """Invalid or missing configuration."""


class DeviceNotReadyError(SDKError):
    """A device is not connected, authenticated and synchronized."""


class ModeMismatchError(SDKError):
    """The authoritative Lab mode differs from the experiment mode."""


class TaskError(SDKError):
    """Task error retaining available identity and last known remote state."""

    def __init__(self, message, *, task_id=None, status=None):
        super().__init__(message)
        self.task_id = task_id
        self.status = status


class ExperimentRejectedError(TaskError):
    """The server explicitly rejected the submission."""


class ExperimentFailedError(TaskError):
    """The remote task or local result processing failed."""


class ExperimentTerminatedError(TaskError):
    """The remote task was terminated."""


class ExperimentTimeoutError(TaskError, TimeoutError):
    """Local waiting expired; this does not prove remote task termination."""

    def __init__(self, message, *, task_id=None, status=None, phase=None):
        super().__init__(message, task_id=task_id, status=status)
        self.phase = phase


class SubmissionOutcomeUnknownError(TaskError):
    """Submission acknowledgement was lost; the task must not be replayed."""
