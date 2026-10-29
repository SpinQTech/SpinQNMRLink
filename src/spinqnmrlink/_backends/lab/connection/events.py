# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Public event models and ordered bounded event dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
import queue
import threading
from typing import Any, Callable, Dict, Optional, Tuple

from ..utils.types import QubitMode


@dataclass(frozen=True)
class ChartKey:
    """Protocol-defined identity of one chart stream."""

    task_id: str
    group: str
    chart_name: str
    path: Optional[str] = None
    qubit: Optional[str] = None
    step: Optional[str] = None


@dataclass(frozen=True)
class ProtocolEvent:
    """One decoded server message delivered in receive order."""

    msg_id: str
    qubit_mode: Optional[QubitMode]
    payload_type: str
    payload: Any
    envelope: Dict[str, Any]


@dataclass(frozen=True)
class UnknownMessage(ProtocolEvent):
    """Forward-compatible event for an unrecognised msg_id."""


@dataclass(frozen=True)
class QueueSnapshot:
    """Latest experiment queue state for one runtime mode."""

    qubit_mode: QubitMode
    queue: Tuple[Dict[str, Any], ...]
    current_task_id: Optional[str]


class OrderedEventDispatcher:
    """Single-worker dispatcher preserving per-connection receive order."""

    def __init__(self, callback: Callable[[Dict[str, Any]], None], maxsize: int = 256):
        if not isinstance(maxsize, int) or maxsize <= 0:
            raise ValueError("event_queue_size must be a positive integer")
        self._callback = callback
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._closed = False
        self._state_lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="SpinQLabLinkEventDispatcher",
        )
        self._thread.start()

    def submit(self, message: Dict[str, Any]) -> None:
        # Blocking here is intentional bounded backpressure: decoded messages
        # are never reordered or silently discarded when consumers are slow.
        while not self.closed:
            try:
                self._queue.put(message, timeout=0.05)
                return
            except queue.Full:
                continue

    def wait_until_idle(self) -> None:
        self._queue.join()

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    @property
    def closed(self) -> bool:
        with self._state_lock:
            return self._closed

    def close(self, wait: bool = True, timeout: float = 1.0) -> bool:
        """Close without blocking on a full queue or a user callback."""
        with self._state_lock:
            self._closed = True
        if wait and threading.current_thread() is not self._thread:
            self._thread.join(timeout)
        return not self._thread.is_alive()

    def _run(self) -> None:
        while not self.closed:
            try:
                message = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                if message is None:
                    return
                self._callback(message)
            except Exception:
                import logging
                logging.getLogger("spinqnmrlink.lab.events").exception("Event processing failed")
            finally:
                self._queue.task_done()


class OrderedCallbackDispatcher:
    """Run public state observers away from network and reconnect threads."""

    def __init__(self, maxsize: int = 256):
        if not isinstance(maxsize, int) or maxsize <= 0:
            raise ValueError("observer_queue_size must be a positive integer")
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._closed = False
        self._state_lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="SpinQLabLinkObserverDispatcher",
        )
        self._thread.start()

    def submit(self, callback: Callable[[Any], None], value: Any) -> None:
        while not self.closed:
            try:
                self._queue.put((callback, value), timeout=0.05)
                return
            except queue.Full:
                continue

    def wait_until_idle(self) -> None:
        self._queue.join()

    @property
    def closed(self) -> bool:
        with self._state_lock:
            return self._closed

    def close(self, wait: bool = True, timeout: float = 1.0) -> bool:
        """Close without blocking on a full queue or a user callback."""
        with self._state_lock:
            self._closed = True
        if wait and threading.current_thread() is not self._thread:
            self._thread.join(timeout)
        return not self._thread.is_alive()

    def _run(self) -> None:
        while not self.closed or not self._queue.empty():
            try:
                item = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                if item is None:
                    return
                callback, value = item
                callback(value)
            except Exception:
                # The owning SDK logs callback failures.  This dispatcher is
                # deliberately generic and must remain alive after one bad
                # observer.
                pass
            finally:
                self._queue.task_done()
