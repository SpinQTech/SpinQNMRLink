# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Explicit, bounded experiment execution with truthful task outcomes."""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ._core.experiments import serialize_result_document
from ._core.task_timing import mark_execution_started
from .devices import DeviceType, _timeout
from .errors import (
    DeviceNotReadyError,
    ExperimentFailedError,
    ExperimentRejectedError,
    ExperimentTerminatedError,
    ExperimentTimeoutError,
    ModeMismatchError,
    SubmissionOutcomeUnknownError,
)


@dataclass(frozen=True)
class ExperimentResult:
    """Remote result plus reproducibility metadata; raw data is never synthesized."""

    device_type: DeviceType
    experiment_key: str
    task_id: Optional[str]
    status: str
    raw: Any
    metadata: Dict[str, Any]

    @property
    def data(self):
        return (
            self.raw.get("result")
            if self.device_type is DeviceType.LAB and isinstance(self.raw, dict)
            else self.raw
        )

    def to_dict(self):
        return dict(
            device_type=self.device_type.value,
            experiment_key=self.experiment_key,
            task_id=self.task_id,
            status=self.status,
            raw=self.raw,
            metadata=self.metadata,
        )

    def to_json(self, *, indent=2):
        return serialize_result_document(self.to_dict(), indent=indent)


@dataclass(frozen=True)
class PreparedExperiment:
    """An offline-validated definition bound to exactly one device object."""

    device: Any
    descriptor: Any
    parameters: Any

    @property
    def key(self):
        return self.descriptor.key

    def to_wire(self):
        return self.parameters.to_wire()

    def run(self, *, timeout: float, queue_timeout: Optional[float] = None) -> ExperimentResult:
        """Bound execution after STARTED; optionally bound queueing after acceptance.

        Neither timeout cancels or resubmits the remote task. Queueing is unlimited
        by default, but connection loss still interrupts the wait.
        """
        budget = _timeout(timeout)
        queue_budget = None if queue_timeout is None else _timeout(queue_timeout)
        device = self.device
        if not device._run_lock.acquire(blocking=False):
            raise RuntimeError("A device permits only one active SDK experiment")
        registered = False
        client = None
        mode_options = {}
        task_id = None
        submitted = False
        terminal = False
        try:
            device._check_ready(self.descriptor)
            if device._last_unresolved_task is not None:
                raise SubmissionOutcomeUnknownError(
                    "Previous task is unresolved; reconnect before starting another task",
                    task_id=device._last_unresolved_task,
                )
            client = device._client
            parameters = self.parameters.to_native()
            lab = device.device_type is DeviceType.LAB
            if lab:
                from ._backends.lab.utils.types import QubitMode

                mode_options = {"qubit_mode": QubitMode[self.descriptor.mode]}
            registration = dict(mode_options)
            if self.descriptor.mode == "THREE":
                registration.update(parameters=parameters, name=self.descriptor.title)
            experiment, _ = client.register_experiment(
                self.descriptor.experiment_type, **registration
            )
            registered = True
            experiment.parameters = parameters
            if lab:
                client.get_expMgr(**mode_options).current_experiment_params = parameters
            task_id = experiment.id
            start = datetime.now(timezone.utc).isoformat()
            submitted = True
            try:
                submission = (
                    client.run_experiment(**mode_options)
                    if lab
                    else client.run_experiment(timeout=device.settings.request_timeout)
                )
            except ExperimentRejectedError:
                terminal = True
                raise
            except Exception as exc:
                if not lab:
                    from ._backends.triangulum.protocol import SubmissionNotSentError

                    if isinstance(exc, SubmissionNotSentError):
                        submitted = False
                        raise
                if lab:
                    from ._backends.lab.connection.request import (
                        QubitModeMismatchError,
                        QubitModeUnsupportedError,
                    )

                    if isinstance(exc, QubitModeMismatchError):
                        submitted = False
                        raise ModeMismatchError("Lab mode changed before task submission") from exc
                    if isinstance(exc, QubitModeUnsupportedError):
                        submitted = False
                        raise ExperimentRejectedError(
                            "Requested Lab mode is unsupported by the server", task_id=task_id
                        ) from exc
                if isinstance(exc, ConnectionError):
                    raise SubmissionOutcomeUnknownError(
                        "Transport lost during submission; do not replay", task_id=task_id
                    ) from exc
                raise
            if submission is False:
                terminal = True
                raise ExperimentRejectedError("Submission was rejected", task_id=task_id)
            if lab:
                from ._backends.lab.connection.request import (
                    RequestOutcomeUnknownError,
                    RequestResponseTimeoutError,
                )

                try:
                    response = client.wait_for_request_response(
                        submission,
                        timeout=device.settings.request_timeout,
                    )
                except (RequestOutcomeUnknownError, RequestResponseTimeoutError) as exc:
                    raise SubmissionOutcomeUnknownError(
                        "Submission acknowledgement was not received; do not replay",
                        task_id=task_id,
                    ) from exc
                if not response.success:
                    terminal = True
                    raise ExperimentRejectedError(
                        "Server rejected task (code {})".format(response.raw_code), task_id=task_id
                    )
            acknowledged = time.monotonic()
            acknowledged_utc = datetime.now(timezone.utc).isoformat()
            while True:
                status = client.get_experiment_status(**mode_options)
                status = getattr(status, "value", status)
                now = time.monotonic()
                if status == "RUNNING":
                    mark_execution_started(experiment, monotonic=now)
                execution_start = getattr(experiment, "execution_started_monotonic", None)
                if status == "COMPLETED":
                    terminal = True
                    break
                if status in ("FAILED", "TERMINATED", "TIMEOUT"):
                    terminal = True
                    error = (
                        ExperimentTerminatedError
                        if status == "TERMINATED"
                        else ExperimentFailedError
                    )
                    raise error(
                        "Experiment result processing failed"
                        if getattr(experiment, "processing_error", None)
                        else "Remote experiment ended with {}".format(status),
                        task_id=task_id,
                        status=status,
                    )
                device._check_ready(self.descriptor)
                phase = "queue" if execution_start is None else "execution"
                deadline = (
                    None if queue_budget is None else acknowledged + queue_budget
                ) if execution_start is None else execution_start + budget
                if deadline is not None and now >= deadline:
                    raise ExperimentTimeoutError(
                        "Local {} waiting expired; remote task may still be pending or running".format(phase),
                        task_id=task_id,
                        status=status,
                        phase=phase,
                    )
                time.sleep(0.05 if deadline is None else min(0.05, max(0, deadline - now)))
            raw = client.get_experiment_result(**mode_options)
            finished = getattr(experiment, "execution_finished_monotonic", time.monotonic())
            finished_utc = getattr(experiment, "execution_finished_at_utc", None)
            return ExperimentResult(
                device.device_type,
                self.key,
                task_id,
                "COMPLETED",
                raw,
                {
                    "sdk_version": _version(),
                    "started_at_utc": start,
                    "submitted_at_utc": start,
                    "acknowledged_at_utc": acknowledged_utc,
                    "execution_started_at_utc": getattr(experiment, "execution_started_at_utc", None),
                    "finished_at_utc": finished_utc or datetime.now(timezone.utc).isoformat(),
                    "queue_duration_seconds": None if execution_start is None else max(0, execution_start - acknowledged),
                    "execution_duration_seconds": None if execution_start is None else max(0, finished - execution_start),
                    "parameters": _effective_parameters(parameters),
                    "qubit_mode": self.descriptor.mode,
                },
            )
        except DeviceNotReadyError as exc:
            if submitted:
                raise SubmissionOutcomeUnknownError(
                    "Connection lost while observing task; remote outcome is unknown",
                    task_id=task_id,
                ) from exc
            raise
        finally:
            handling_error = sys.exc_info()[0] is not None
            if submitted and not terminal:
                device._last_unresolved_task = task_id or "unknown"
            try:
                if registered and client is not None:
                    client.deregister_experiment(**mode_options)
            except Exception:
                if not handling_error:
                    raise
                logging.getLogger("spinqnmrlink").exception(
                    "Experiment cleanup failed during error handling"
                )
            finally:
                device._run_lock.release()


def _version():
    from ._core._version import __version__

    return __version__


def _effective_parameters(native):
    from .models import _from_native

    return _from_native(native).model_dump(mode="json")
