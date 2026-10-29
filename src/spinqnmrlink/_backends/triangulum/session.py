# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Independent Triangulum authentication, heartbeat and task session in Python."""

import logging
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass, field

from ..._core.diagnostics import safe_reason
from ..._core.task_timing import mark_execution_finished, mark_execution_started
from ...errors import ExperimentRejectedError, SubmissionOutcomeUnknownError
from .protocol import (
    ProtocolError,
    SubmissionNotSentError,
    decode_message,
    decode_result,
    encode_message,
    redact,
    response_code,
    task_id,
    task_request,
)
from .transport import WebSocketTransport

logger = logging.getLogger(__name__)
TERMINAL = frozenset(("COMPLETED", "FAILED", "TERMINATED"))


@dataclass
class Task:
    id: str
    kind: str
    parameters: object
    state: str = "PENDING"
    acknowledgement: object = None
    pending_finish: object = None
    result: dict = field(default_factory=dict)
    wire: dict = field(default_factory=dict)
    processing_error: object = None


class TriangulumSession:
    """No singleton, native code or background resources before connect()."""

    def __init__(self, settings, *, transport_factory=WebSocketTransport):
        self.settings = settings
        self._transport_factory = transport_factory
        self._transport = None
        self._condition = threading.Condition(threading.RLock())
        self._stop = threading.Event()
        self._worker = None
        self._generation = 0
        self._login_event = threading.Event()
        self._logout_event = threading.Event()
        self._session_id = ""
        self._task = None
        self._issued_ids = set()
        self._recent_ids = deque()
        self.is_connected = False
        self.is_logged_in = False
        self.logging_in = False
        self._closing = False
        self._disconnect_callback = None
        self.last_disconnect_reason = None
        self._last_sent_monotonic = None

    def connect(self, timeout=10):
        deadline = time.monotonic() + timeout
        if self.get_connection():
            return self.is_logged_in
        if self._worker is not None:
            self.disconnect(timeout=timeout)
        self._stop = threading.Event()
        self._closing = False
        self.last_disconnect_reason = None
        self._last_sent_monotonic = None
        self._login_event.clear()
        self._generation += 1
        transport = self._transport_factory(self.settings)
        self._transport = transport
        try:
            transport.open(timeout)
            with self._condition:
                self.is_connected = True
                self.logging_in = True
            self._worker = threading.Thread(
                target=self._receive_loop,
                args=(transport, self._stop, self._generation),
                name="spinq-triangulum-receiver",
                daemon=True,
            )
            self._worker.start()
            self._send(
                {
                    "msg_id": "user_login_request",
                    "account": self.settings.account.get_secret_value(),
                    "password": self.settings.password.get_secret_value(),
                }
            )
            self._login_event.wait(max(0, deadline - time.monotonic()))
            if self.is_logged_in:
                return True
        except Exception as error:
            self._report_disconnect(error, self._generation)
        self.disconnect(timeout=max(0.01, deadline - time.monotonic()))
        return False

    def _send(self, message):
        self._send_text(encode_message(message))

    def _send_text(self, text):
        if not self.is_connected or self._transport is None:
            raise ConnectionError("Triangulum transport is disconnected")
        try:
            self._transport.send(text)
            self._last_sent_monotonic = time.monotonic()
        except Exception as error:
            self._report_disconnect(error, self._generation)
            self._stop.set()
            self._transport.close()
            raise

    def set_disconnect_callback(self, callback):
        self._disconnect_callback = callback

    def _report_disconnect(self, error, generation, **details):
        with self._condition:
            if generation != self._generation or self.last_disconnect_reason is not None:
                return
            # Suppress only expected teardown effects. A simultaneous genuine
            # reset remains visible, even after the caller begins close().
            expected_close = (
                getattr(error, "winerror", None) == 10038
                or getattr(error, "errno", None) in (9, 10038)
                or (type(error) is ConnectionError and "closed" in str(error).lower())
            )
            if self._closing and expected_close:
                return
            reason = safe_reason("{}: {}".format(type(error).__name__, error), (
                self.settings.account.get_secret_value(), self.settings.password.get_secret_value(), self._session_id,
            ))
            self.last_disconnect_reason = reason
            self.is_connected = self.is_logged_in = self.logging_in = False
            details.update(task_ids=[self._task.id] if self._task is not None else [],
                           last_sent_monotonic=self._last_sent_monotonic, server_version=None)
            self._condition.notify_all()
            callback = self._disconnect_callback
        logger.warning("Triangulum disconnected: %s; diagnostics=%s", reason, details)
        if callback is not None:
            callback(reason, details)

    def get_connection(self):
        with self._condition:
            return self.is_connected

    def disconnect(self, timeout=5):
        deadline = time.monotonic() + timeout
        with self._condition:
            self._closing = True
        transport = self._transport
        try:
            if self.is_logged_in and transport is not None:
                self._logout_event.clear()
                try:
                    self._send(
                        {
                            "msg_id": "user_logout_request",
                            "session_id": self._session_id,
                            "account": self.settings.account.get_secret_value(),
                        }
                    )
                    self._logout_event.wait(max(0, (deadline - time.monotonic()) / 2))
                except Exception:
                    pass
        finally:
            self._stop.set()
            if transport is not None:
                try:
                    transport.close()
                except Exception:
                    logger.debug("Triangulum transport cleanup failed")
            with self._condition:
                self.is_connected = self.is_logged_in = self.logging_in = False
                self._condition.notify_all()
            self._login_event.set()
            self._transport = None
            worker = self._worker
            if worker is not None and worker is not threading.current_thread():
                worker.join(max(0, deadline - time.monotonic()))
                if worker.is_alive():
                    raise RuntimeError("Triangulum receive worker exceeded the close deadline")
            self._worker = None
            with self._condition:
                # The retiring worker must still be able to report a genuine
                # reset observed during shutdown, with its original secrets.
                self._session_id = ""
                self._generation += 1

    def _receive_loop(self, transport, stop, generation):
        last_received = opened = time.monotonic()
        last_heartbeat = None
        try:
            while not stop.is_set():
                text = transport.receive()
                now = time.monotonic()
                if text is not None:
                    message = decode_message(text, self.settings.max_message_bytes)
                    with self._condition:
                        if generation != self._generation:
                            return
                        self._dispatch(message)
                    last_received = now
                if self.is_logged_in:
                    if now - last_received >= self.settings.heartbeat_timeout:
                        raise ConnectionError("Triangulum heartbeat deadline expired")
                    if now - (opened if last_heartbeat is None else last_heartbeat) >= self.settings.heartbeat_interval:
                        transport.send(
                            encode_message({"msg_id": "heartbeat", "session_id": self._session_id})
                        )
                        last_heartbeat = now
                        self._last_sent_monotonic = now
        except Exception as error:
            self._report_disconnect(
                error, generation,
                last_received_monotonic=last_received,
                last_heartbeat_sent_monotonic=last_heartbeat,
                idle_seconds=max(0, time.monotonic() - last_received),
                heartbeat_timeout_seconds=self.settings.heartbeat_timeout,
            )
        finally:
            try:
                transport.close()
            except Exception:
                logger.debug("Triangulum transport cleanup failed")
            with self._condition:
                if generation == self._generation:
                    self.is_connected = self.is_logged_in = self.logging_in = False
                    self._condition.notify_all()
                    self._login_event.set()
                    self._logout_event.set()

    def _dispatch(self, message):
        kind = message["msg_id"]
        if kind == "user_login_response":
            if self._login_event.is_set():
                return
            if response_code(message) == 0:
                session = message.get("session_id")
                if not isinstance(session, str) or not session:
                    raise ProtocolError("Login response is missing a session_id")
                self._session_id = session
                self.is_logged_in = True
            self.logging_in = False
            self._login_event.set()
            return
        if kind == "user_logout_response":
            response_code(message)
            self.is_logged_in = False
            self._logout_event.set()
            return
        task = self._task
        if task is None:
            return
        circuit = task.kind == "EXP_CIRCUIT_LAYER"
        ack = "push_task_response" if circuit else "push_custom_task_response"
        # Physical clients use either the legacy custom notification or the
        # common circuit/physical start notification. ACK/finish stay specific.
        started = ("task_started_post",) if circuit else (
            "custom_task_started_post", "task_started_post"
        )
        finished = "task_finished_post" if circuit else "custom_task_finished_post"
        if kind not in (ack, finished) + started or task_id(message) != task.id:
            return
        if task.state in TERMINAL:
            return
        if kind == ack:
            if task.acknowledgement is not None:
                return
            task.acknowledgement = response_code(message)
            task.wire["submission"] = redact(message)
            if task.acknowledgement != 0:
                task.state = "FAILED"
            elif task.pending_finish is not None:
                self._finish(task, task.pending_finish)
            else:
                task.state = "RUNNING" if "started" in task.wire else "PENDING"
        elif kind in started:
            mark_execution_started(task)
            task.wire.setdefault("started", redact(message))
            if task.acknowledgement == 0:
                task.state = "RUNNING"
        elif task.acknowledgement is None:
            if task.pending_finish is None:
                mark_execution_finished(task)
                task.pending_finish = message
        else:
            self._finish(task, message)
        self._condition.notify_all()

    def _finish(self, task, message):
        mark_execution_finished(task)
        task.wire["finished"] = redact(message)
        state = message.get("task_state")
        if state != "S":
            task.state = "TERMINATED" if state in ("T", "TERMINATED") else "FAILED"
            return
        try:
            task.result = decode_result(task, message)
            task.result["protocol_raw"] = dict(task.wire)
            task.state = "COMPLETED"
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
            task.processing_error = str(error)
            task.state = "FAILED"

    def register_experiment(self, kind):
        from .experiment.exp_circuit_layer import ExpCircuitLayerParameters
        from .experiment.exp_physical_layer import ExpPhysicalLayerParameters

        factories = {
            "EXP_CIRCUIT_LAYER": ExpCircuitLayerParameters,
            "EXP_PHYSICAL_LAYER": ExpPhysicalLayerParameters,
        }
        with self._condition:
            if self._task is not None:
                raise RuntimeError("One Triangulum session permits one active experiment")
            if kind not in factories:
                raise ValueError("Unknown Triangulum experiment type")
            identifier = str(secrets.randbits(63) or 1)
            while identifier in self._issued_ids:
                identifier = str(secrets.randbits(63) or 1)
            self._issued_ids.add(identifier)
            self._recent_ids.append(identifier)
            if len(self._recent_ids) > 1024:
                self._issued_ids.remove(self._recent_ids.popleft())
            parameters = factories[kind]()
            self._task = Task(identifier, kind, parameters)
            return self._task, parameters

    def run_experiment(self, *, timeout=None):
        budget = (
            self.settings.request_timeout
            if timeout is None
            else min(timeout, self.settings.request_timeout)
        )
        deadline = time.monotonic() + budget
        with self._condition:
            task = self._task
            if task is None:
                raise RuntimeError("No Triangulum experiment is registered")
            try:
                message = encode_message(task_request(task, self._session_id))
                if len(message.encode("utf-8")) > self.settings.max_message_bytes:
                    raise ValueError("Task request exceeds the configured message limit")
            except (ValueError, TypeError):
                raise SubmissionNotSentError(
                    "Invalid Triangulum task request; no bytes sent"
                ) from None
            try:
                self._send_text(message)
            except Exception:
                raise SubmissionOutcomeUnknownError(
                    "Transport failed during submission; do not replay", task_id=task.id
                ) from None
            while task.acknowledgement is None:
                remaining = deadline - time.monotonic()
                if not self.is_connected or remaining <= 0:
                    raise SubmissionOutcomeUnknownError(
                        "Submission acknowledgement was not received; do not replay",
                        task_id=task.id,
                    )
                self._condition.wait(remaining)
            if task.acknowledgement != 0:
                raise ExperimentRejectedError(
                    "Server rejected task (code {})".format(task.acknowledgement), task_id=task.id
                )
            return task.id

    def get_experiment_status(self):
        with self._condition:
            return self._task.state if self._task else None

    def get_experiment_result(self):
        with self._condition:
            return dict(self._task.result) if self._task else None

    def deregister_experiment(self):
        with self._condition:
            self._task = None
