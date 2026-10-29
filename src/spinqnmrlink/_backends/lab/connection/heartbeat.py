# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Heartbeat manager.

Used to manage the heartbeat connection with the server.

Liveness strategy
-----------------
* A heartbeat request is sent at the configured interval (15 seconds by
  default).
* Every valid server message, not only a heartbeat response, refreshes the
  last-activity timestamp.
* Two missed intervals by default are treated as a lost connection, including
  while a task is queued or running.
"""

import time
import threading
from typing import Callable, Optional
from ..utils import LoggerManager

# Message type definitions
MSG_HEARTBEAT_REQ = "heartbeat_req"  # Heartbeat request
MSG_HEARTBEAT_RES = "heartbeat_res"  # Heartbeat response

HEARTBEAT_INTERVAL = 15.0
HEARTBEAT_MISSED_PERIODS = 2

# Create logger
logger = LoggerManager.get_logger(name='heartbeat')


class HeartbeatManager:
    """Heartbeat manager independent of task queue/execution deadlines."""

    def __init__(
        self,
        send_message_callback: Callable[[str, dict], None],
        interval: float = HEARTBEAT_INTERVAL,
        missed_periods: int = HEARTBEAT_MISSED_PERIODS,
    ):
        """
        Initialize the heartbeat manager.

        Args:
            send_message_callback: Callback used to send heartbeat messages.
        """
        self.send_message_callback = send_message_callback

        # Heartbeat-related attributes
        self.heartbeat_timer: Optional[threading.Timer] = None
        if interval <= 0:
            raise ValueError("heartbeat interval must be positive")
        if not isinstance(missed_periods, int) or missed_periods <= 0:
            raise ValueError("heartbeat missed_periods must be a positive integer")
        self.interval = float(interval)
        self.missed_periods = missed_periods
        self.timeout = self.interval * self.missed_periods
        self.last_server_activity_time = 0.0
        self.heartbeat_checking_timer: Optional[threading.Timer] = None

        # State
        self._is_running = False

        # Explicit legacy suspension is available to internal callers only;
        # normal SDK task submission never enables it.
        self._timeout_suspended = False

        # Callback for timeout handling
        self.on_timeout_callback: Optional[Callable[[], None]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_timeout_callback(self, callback: Callable[[], None]):
        """
        Set the heartbeat timeout callback function.

        Args:
            callback: Callback invoked when a timeout occurs.
        """
        self.on_timeout_callback = callback

    def suspend_timeout(self):
        """Suspend the timeout clock.

        Legacy low-level override. Normal task submission does not use it:
        queueing and running tasks still require server activity.
        """
        if not self._timeout_suspended:
            logger.debug("Heartbeat timeout suspended (experiment queued/running)")
            self._timeout_suspended = True
            # Reset the response timestamp so the clock starts fresh when resumed
            self.last_server_activity_time = time.time()

    def resume_timeout(self):
        """Resume the timeout clock.

        Call this when the experiment finishes or is deregistered.
        """
        if self._timeout_suspended:
            logger.debug("Heartbeat timeout resumed")
            self._timeout_suspended = False
            # Restart the timestamp so we get a full window before triggering
            self.last_server_activity_time = time.time()

    def start(self):
        """Start the heartbeat mechanism."""
        if self._is_running:
            logger.warning("Heartbeat is already running")
            return

        logger.debug("Starting heartbeat")
        self._is_running = True
        self._timeout_suspended = False
        self.last_server_activity_time = time.time()

        # Start heartbeat send timer
        self._send_heartbeat()

        # Start heartbeat timeout checking timer
        self._check_heartbeat_timeout()

    def stop(self):
        """Stop the heartbeat mechanism."""
        if not self._is_running:
            return

        logger.debug("Stopping heartbeat")
        self._is_running = False
        self._timeout_suspended = False

        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None

        if self.heartbeat_checking_timer:
            self.heartbeat_checking_timer.cancel()
            self.heartbeat_checking_timer = None

    def on_heartbeat_response(self):
        """Backward-compatible heartbeat response activity hook."""
        self.on_server_activity()

    def on_server_activity(self):
        """Refresh liveness after any decoded server message."""
        self.last_server_activity_time = time.time()

    def get_status(self) -> dict:
        """
        Get heartbeat status.

        Returns:
            dict: Heartbeat status information.
        """
        current_time = time.time()
        elapsed_time = (
            current_time - self.last_server_activity_time
            if self.last_server_activity_time > 0
            else 0
        )
        return {
            "is_running": self._is_running,
            "timeout_suspended": self._timeout_suspended,
            "last_response_time": self.last_server_activity_time,
            "elapsed_time": elapsed_time,
            "timeout_threshold": self.timeout,
            "send_interval": self.interval,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_heartbeat(self):
        """Send a heartbeat message."""
        if not self._is_running:
            logger.warning("Heartbeat stopped, not sending")
            return

        try:
            self.send_message_callback(MSG_HEARTBEAT_REQ, {})
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

        if self._is_running:
            self.heartbeat_timer = threading.Timer(self.interval, self._send_heartbeat)
            self.heartbeat_timer.daemon = True
            self.heartbeat_timer.start()

    def _check_heartbeat_timeout(self):
        """Check whether the heartbeat has timed out.

        Task queue/execution state does not suspend this check.
        """
        if not self._is_running:
            logger.debug("Heartbeat is not running; not checking timeout")
            return

        if self._timeout_suspended:
            # Keep rescheduling the check but do not count elapsed time
            logger.debug("Heartbeat timeout check skipped (suspended)")
            self._schedule_next_check()
            return

        current_time = time.time()
        elapsed_time = current_time - self.last_server_activity_time

        if elapsed_time > self.timeout:
            logger.error(
                f"Server activity timeout ({elapsed_time:.1f} s > {self.timeout} s); "
                "considered disconnected"
            )
            self._is_running = False
            if self.on_timeout_callback:
                try:
                    self.on_timeout_callback()
                except Exception as e:
                    logger.error(f"Heartbeat timeout callback execution failed: {e}")
        else:
            self._schedule_next_check()

    def _schedule_next_check(self):
        """Schedule the next heartbeat timeout check."""
        if self._is_running:
            check_interval = min(5.0, self.interval)
            self.heartbeat_checking_timer = threading.Timer(check_interval, self._check_heartbeat_timeout)
            self.heartbeat_checking_timer.daemon = True
            self.heartbeat_checking_timer.start()
