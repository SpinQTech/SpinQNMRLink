# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Independent device objects and a minimal protocol adapter contract."""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Protocol, Tuple, Union

from ._core.diagnostics import DisconnectEvent, safe_reason
from .catalogue import ExperimentDescriptor, get_experiment, list_experiments
from .config import LabSettings, TriangulumSettings
from .errors import DeviceNotReadyError, ModeMismatchError

if TYPE_CHECKING:
    from ._backends.lab.connection.events import OrderedCallbackDispatcher
    from .experiments import PreparedExperiment
    from .models import ExperimentParameters


class DeviceType(str, Enum):
    LAB = "lab"
    TRIANGULUM = "triangulum"


@dataclass(frozen=True)
class DeviceCapabilities:
    """SDK features; authoritative_mode is unknown until synchronized."""

    device_type: DeviceType
    sdk_features: Tuple[str, ...]
    supported_modes: Tuple[str, ...]
    authoritative_mode: Optional[str] = None


class BackendProtocol(Protocol):
    """Contract for a backend session injected into a device."""

    def connect(self, **kwargs): ...
    def disconnect(self, **kwargs): ...
    def get_connection(self) -> bool: ...
    def get_experiment_status(self, **kwargs): ...


def _timeout(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError("timeout must be a finite positive number of seconds")
    return float(value)


class Device:
    """Shared lifecycle, catalogue and parameter validation."""

    device_type: DeviceType

    def __init__(
        self, settings: Union[LabSettings, TriangulumSettings], *, backend_factory=None
    ) -> None:
        expected = LabSettings if self.device_type is DeviceType.LAB else TriangulumSettings
        if not isinstance(settings, expected):
            raise TypeError("settings do not match the device type")
        self.settings = settings
        self._backend_factory = backend_factory
        self._client: Any = None
        self._run_lock = threading.Lock()
        self._lifecycle_lock = threading.RLock()
        self._last_unresolved_task = None
        self._disconnect_lock = threading.Lock()
        self._disconnect_observers: List[Callable[[DisconnectEvent], None]] = []
        self._disconnect_dispatcher: Optional[OrderedCallbackDispatcher] = None
        self._last_disconnect_event: Optional[DisconnectEvent] = None
        self._connection_generation = 0
        self._closing = False
        self._close_complete = threading.Event()
        self._close_complete.set()

    @property
    def last_disconnect_event(self) -> Optional[DisconnectEvent]:
        """Last unexpected loss, retained after close and reset by a new open."""
        return self._last_disconnect_event

    @property
    def last_disconnect_reason(self) -> Optional[str]:
        event = self._last_disconnect_event
        return None if event is None else event.reason

    def subscribe_disconnect(self, callback):
        """Subscribe to unexpected losses; return an unsubscribe function.

        Callbacks run on an SDK observer thread and should return promptly.
        Subscribing alone does not create a thread or open a connection.
        """
        if not callable(callback):
            raise TypeError("disconnect observer must be callable")
        with self._disconnect_lock:
            self._disconnect_observers.append(callback)

        def unsubscribe():
            with self._disconnect_lock:
                if callback in self._disconnect_observers:
                    self._disconnect_observers.remove(callback)

        return unsubscribe

    def _record_disconnect(self, generation, client, reason, diagnostics):
        from ._backends.lab.connection.events import OrderedCallbackDispatcher

        with self._disconnect_lock:
            if generation != self._connection_generation:
                return
            reason = safe_reason(reason, (self.settings.account.get_secret_value(),
                                         self.settings.password.get_secret_value(),
                                         getattr(client, "session_id", "")))
            details = dict(diagnostics)
            task_ids = tuple(details.pop("task_ids", ()))
            if not task_ids and self._last_unresolved_task:
                task_ids = (self._last_unresolved_task,)
            event = DisconnectEvent(self.device_type.value, reason, task_ids,
                                    datetime.now(timezone.utc).isoformat(), MappingProxyType(details))
            self._last_disconnect_event = event
            callbacks = tuple(self._disconnect_observers)
            if callbacks:
                if self._disconnect_dispatcher is None or self._disconnect_dispatcher.closed:
                    self._disconnect_dispatcher = OrderedCallbackDispatcher()
                dispatcher = self._disconnect_dispatcher
            else:
                return

        def deliver(value):
            for observer in callbacks:
                try:
                    observer(value)
                except Exception:
                    # One application's observer must not suppress the others.
                    continue

        dispatcher.submit(deliver, event)

    @property
    def is_ready(self) -> bool:
        client = self._client
        if client is None or not client.get_connection() or not client.is_logged_in:
            return False
        if self.device_type is DeviceType.LAB:
            return getattr(client.connection_state, "name", None) == "READY"
        return True

    @property
    def capabilities(self) -> DeviceCapabilities:
        """Describe SDK support without claiming server endpoint availability."""
        mode = None
        client = self._client
        if self.device_type is DeviceType.LAB and self.is_ready and client is not None:
            mode = getattr(client.get_qubit_mode(), "name", None)
        return DeviceCapabilities(
            self.device_type,
            ("tcp", "websocket", "physical", "circuit", "task_status")
            if self.device_type is DeviceType.LAB
            else ("websocket", "physical", "circuit", "task_status"),
            ("TWO", "THREE") if self.device_type is DeviceType.LAB else (),
            mode,
        )

    def list_experiments(self) -> Tuple[ExperimentDescriptor, ...]:
        """List all SDK experiments offline; filter by mode once ready."""
        return list_experiments(self.device_type, mode=self.capabilities.authoritative_mode)

    def create_experiment(
        self, key: str, *, parameters: Optional["ExperimentParameters"] = None
    ) -> "PreparedExperiment":
        """Prepare an experiment without connecting or submitting."""
        from .experiments import PreparedExperiment
        from .models import ExperimentParameters, parameters_for

        descriptor = get_experiment(key)
        if descriptor.device_type != self.device_type.value:
            raise ValueError("Experiment belongs to a different device type")
        reference = parameters_for(key)
        if parameters is None:
            parameters = reference
        if not isinstance(parameters, ExperimentParameters) or type(parameters) is not type(
            reference
        ):
            raise TypeError("parameters must have the exact model returned by parameters_for(key)")
        parameters.to_wire()
        return PreparedExperiment(self, descriptor, parameters)

    def _check_ready(self, descriptor):
        if not self.is_ready:
            raise DeviceNotReadyError(
                "Open and synchronize {} before running".format(self.device_type.value)
            )
        if descriptor.mode and self.capabilities.authoritative_mode != descriptor.mode:
            raise ModeMismatchError(
                "Experiment requires {}; server mode is {}".format(
                    descriptor.mode, self.capabilities.authoritative_mode
                )
            )

    def open(self, *, timeout: Optional[float] = None) -> "Device":
        """Connect, authenticate and (for Lab) synchronize, within a deadline."""
        budget = _timeout(self.settings.connection_timeout if timeout is None else timeout)
        with self._lifecycle_lock:
            if self._closing:
                raise RuntimeError("Cannot open a device while close is in progress")
            if self.is_ready:
                return self
            needs_cleanup = self._client is not None
        if needs_cleanup:
            self.close(timeout=min(5.0, budget))
        try:
            with self._lifecycle_lock:
                if self._closing:
                    raise RuntimeError("Cannot open a device while close is in progress")
                if self.is_ready:
                    return self
                self._client = self._make_backend()
                self._connection_generation += 1
                self._last_disconnect_event = None
                client, generation = self._client, self._connection_generation
                if hasattr(client, "set_disconnect_callback"):
                    client.set_disconnect_callback(
                        lambda reason, details: self._record_disconnect(generation, client, reason, details)
                    )
                self._last_unresolved_task = None
                deadline = time.monotonic() + budget
                if self.device_type is DeviceType.LAB:
                    self._client.connection.timeout = budget
                    connected = self._client.connect(auto_login=True)
                else:
                    connected = self._client.connect(timeout=budget)
                if not connected:
                    raise DeviceNotReadyError("Device connection failed")
                while not self.is_ready:
                    if not self._client.get_connection() or time.monotonic() >= deadline:
                        raise DeviceNotReadyError(
                            "Authentication or device synchronization failed/timed out"
                        )
                    time.sleep(min(0.05, max(0, deadline - time.monotonic())))
                return self
        except BaseException:
            self.close(timeout=min(5.0, budget))
            raise

    def close(self, *, timeout: float = 5.0) -> None:
        """Stop transport and workers; repeated close is harmless."""
        budget = _timeout(timeout)
        deadline = time.monotonic() + budget
        with self._lifecycle_lock:
            if self._closing:
                dispatcher = self._disconnect_dispatcher
                if dispatcher is not None and threading.current_thread() is dispatcher._thread:
                    # The owning closer is joining this callback. Its cleanup
                    # already covers this request; never wait on one another.
                    return
                already_closing = True
            else:
                already_closing = False
                self._closing = True
                self._close_complete.clear()
                client, self._client = self._client, None
        if already_closing:
            if not self._close_complete.wait(max(0, deadline - time.monotonic())):
                raise RuntimeError("Concurrent close exceeded the close deadline")
            return
        try:
            try:
                if client is not None:
                    client.disconnect(timeout=budget)
            finally:
                with self._disconnect_lock:
                    dispatcher = self._disconnect_dispatcher
                if dispatcher is not None:
                    closed = dispatcher.close(timeout=max(0, deadline - time.monotonic()))
                    if not closed and threading.current_thread() is not dispatcher._thread:
                        raise RuntimeError("Disconnect observer exceeded the close deadline")
        finally:
            with self._lifecycle_lock:
                self._closing = False
                self._close_complete.set()

    def _make_backend(self):
        if self._backend_factory is not None:
            return self._backend_factory(self.settings)
        if self.device_type is DeviceType.LAB:
            from ._backends.lab.spinqlablink import SpinQLabLink

            values = self.settings.model_dump()
            values["account"] = self.settings.account.get_secret_value()
            values["password"] = self.settings.password.get_secret_value()
            return SpinQLabLink(**values)
        from ._backends.triangulum.session import TriangulumSession

        assert isinstance(self.settings, TriangulumSettings)

        return TriangulumSession(self.settings)


class LabDevice(Device):
    """Lab device backed by the TCP/WebSocket protocol."""

    device_type = DeviceType.LAB


class TriangulumDevice(Device):
    """Triangulum device backed by the Python JSON WebSocket protocol."""

    device_type = DeviceType.TRIANGULUM
