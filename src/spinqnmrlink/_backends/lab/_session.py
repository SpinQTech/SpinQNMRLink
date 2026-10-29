# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private Lab session behavior; state is owned by the backend session."""
from ._imports import *  # noqa: F403
from ..._core.task_timing import mark_execution_started, mark_execution_finished
from ..._core.diagnostics import safe_reason


class SessionMixin:
    def _ensure_dispatchers_running(self) -> None:
        """Recreate dispatch workers after a prior manual disconnect."""
        if self._event_dispatcher.closed:
            self._event_dispatcher = OrderedEventDispatcher(
                self._dispatch_received_message,
                maxsize=self._event_queue_size,
            )
        if self._observer_dispatcher.closed:
            self._observer_dispatcher = OrderedCallbackDispatcher(
                maxsize=self._event_queue_size,
            )


    def _close_dispatchers(self, timeout=1.0) -> bool:
        deadline = time.monotonic() + timeout
        event_closed = self._event_dispatcher.close(timeout=timeout)
        observer_closed = self._observer_dispatcher.close(timeout=max(0, deadline - time.monotonic()))
        return event_closed and observer_closed


    def _event_from_envelope(
        self,
        envelope: Dict[str, Any],
        event_type=ProtocolEvent,
    ) -> ProtocolEvent:
        mode = self._mode_from_envelope(envelope, context="protocol event")
        if "chart_data" in envelope:
            payload_type = "chart_data"
            payload = envelope.get("chart_data")
        else:
            payload_type = "json_data"
            payload = envelope.get("json_data")
        return event_type(
            msg_id=str(envelope.get("msg_id", "")),
            qubit_mode=mode,
            payload_type=payload_type,
            payload=payload,
            envelope=dict(envelope),
        )


    def _publish_protocol_event(self, envelope: Dict[str, Any]) -> None:
        event = self._event_from_envelope(envelope)
        for observer in tuple(self._event_observers):
            try:
                observer(event)
            except Exception as exc:
                logger.error("Protocol event observer failed: %s", exc)


    def _call_experiment_handler(
        self,
        handler,
        msg_id: str,
        payload: Dict[str, Any],
        mode: QubitMode,
        *,
        explicit_null_data: bool = False,
    ) -> None:
        """Apply common lifecycle state and dispatch to experiment handlers."""
        skip_legacy = (
            msg_id == MachineType.MSG_POST_EXP_STARTED
            and not payload.get("queue")
        ) or (
            msg_id in (
                MachineType.MSG_POST_EXP_STEP_CHANGED,
                MachineType.MSG_POST_EXP_DATA_UPDATED,
                MachineType.MSG_POST_EXP_FINISHED,
            )
            and explicit_null_data
        )
        if msg_id != MachineType.MSG_POST_EXP_FINISHED:
            self._update_task_lifecycle(mode, msg_id, payload)
        try:
            if not skip_legacy:
                handler(payload)
        except Exception as exc:
            manager = self._experiment_managers_by_mode.get(mode)
            experiment = manager.current_experiment if manager is not None else None
            if experiment is not None and experiment.id == payload.get("taskId"):
                experiment.processing_error = str(exc)
                experiment.state = ExperimentState.FAILED
            raise
        else:
            if msg_id == MachineType.MSG_POST_EXP_FINISHED:
                self._update_task_lifecycle(mode, msg_id, payload)


    def _update_task_lifecycle(
        self,
        mode: QubitMode,
        msg_id: str,
        payload: Dict[str, Any],
    ) -> None:
        task_id = payload.get("taskId")
        if not task_id:
            return
        state = None
        if msg_id == MachineType.MSG_POST_EXP_STARTED:
            state = TaskState.RUNNING.value
        elif msg_id == MachineType.MSG_POST_EXP_FINISHED:
            detail = payload.get("data")
            detail = detail if isinstance(detail, dict) else {}
            raw_state = detail.get("state")
            try:
                state = TaskState(raw_state).value if raw_state is not None else None
            except (TypeError, ValueError):
                state = None
            if state is None:
                if detail.get("isTimeout") is True:
                    state = TaskState.TIMEOUT.value
                elif detail.get("isTerminated") is True:
                    state = TaskState.TERMINATED.value
                else:
                    state = TaskState.COMPLETED.value
        if state is None:
            return
        self._task_states_by_mode.setdefault(mode, {})[str(task_id)] = state
        manager = self._experiment_managers_by_mode.get(mode)
        experiment = manager.current_experiment if manager is not None else None
        if experiment is not None and experiment.id == task_id:
            if state == TaskState.RUNNING.value:
                mark_execution_started(experiment)
            elif state in ("COMPLETED", "FAILED", "TERMINATED", "TIMEOUT"):
                mark_execution_finished(experiment)
            experiment.state = state


    def _handle_user_login_res(self, data: Dict[str, Any], envelope: Dict[str, Any]):
        logger.debug(
            "Login response received: code=%s, has_session_id=%s",
            data.get("code"),
            bool(data.get("sessionId")),
        )
        self._complete_request_response(data, envelope)
        if data["code"] == 0:
            if data["sessionId"]:
                self.session_id = data["sessionId"]
                LoggerManager.register_secret(self.session_id)
                # A rejection belongs to the previous authenticated server
                # environment. A new login must discover capabilities again.
                with self._qubit_mode_lock:
                    self._unsupported_qubit_modes.clear()
                mode = self._read_authoritative_qubit_mode(envelope, require_present=False)
                if mode is None:
                    with self._qubit_mode_lock:
                        previous_mode = self._current_qubit_mode
                        self._current_qubit_mode = None
                    if previous_mode is not None:
                        with self._observer_lock:
                            observers = tuple(self._qubit_mode_observers)
                        for observer in observers:
                            self._observer_dispatcher.submit(observer, None)
                else:
                    self._set_authoritative_qubit_mode(
                        mode,
                        reset_runtime_snapshots=True,
                    )
                self.is_logged_in = True
                self.logging_in = False
                self._set_connection_state(ConnectionState.AUTHENTICATED)
                logger.info("Login authenticated successfully")
                self.heartbeat_manager.start()
            else:
                logger.error("Login failed, sessionId is empty")
        else:
            self.is_logged_in = False
            self.logging_in = False
            self.heartbeat_manager.stop()
            if self.is_connected:
                self._set_connection_state(ConnectionState.CONNECTED)
            logger.error(f"Login failed, error code: {data.get('code')}, error message: {data.get('message')}")


    def _handle_user_logout_res(self, data: Dict[str, Any]):
        logger.debug("Logout response received: code=%s", data.get("code"))
        self.is_logged_in = False
        if self.is_connected:
            self._set_connection_state(ConnectionState.CONNECTED)

        # Stop heartbeat on logout
        self.heartbeat_manager.stop()


    def _handle_heartbeat_res(self, data: Dict[str, Any]):
        # Notify heartbeat manager that a response has been received
        self.heartbeat_manager.on_heartbeat_response()


    def _mark_ready_from_initial_push(
        self,
        mode: Optional[QubitMode] = None,
        snapshot_kind: Optional[str] = None,
    ) -> None:
        """Advance READY only from the authoritative mode's snapshot stream."""
        current_mode = self.get_qubit_mode()
        resolved_mode = current_mode if mode is None else QubitMode(mode)
        if resolved_mode != current_mode:
            return
        if snapshot_kind is not None:
            self._received_mode_snapshot_kinds.setdefault(resolved_mode, set()).add(
                snapshot_kind
            )
        if self._mode_snapshot_sync_pending == resolved_mode:
            received = self._received_mode_snapshot_kinds.get(resolved_mode, set())
            if not self._required_mode_snapshot_kinds.issubset(received):
                return
            self._mode_snapshot_sync_pending = None
        if self.connection_state is ConnectionState.AUTHENTICATED:
            self._set_connection_state(ConnectionState.READY)
            logger.info("Device state synchronized; SDK is ready")


    def _handle_lock_data_update_post(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ):
        mode, device = self._device_for_push(envelope, context="lock data")
        if device is None:
            return
        logger.debug(
            "Device lock data updated for %s: %s",
            mode.name,
            summarize_payload(data),
        )
        device.set_lock_data_post(data)
        self._mark_ready_from_initial_push(mode, "lock_data")


    def _handle_exp_queue_update_post(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ):
        mode = self._mode_from_envelope(envelope, context="experiment queue")
        if mode is None:
            return
        self._observe_mode_state_push(mode)
        queue_snapshot = [dict(item) for item in data.get("queue", [])]
        self._experiment_queues_by_mode[mode] = queue_snapshot
        task_states = self._task_states_by_mode.setdefault(mode, {})
        for item in queue_snapshot:
            task_id = item.get("id")
            raw_state = item.get("state")
            if not task_id or raw_state is None:
                continue
            try:
                state = TaskState(raw_state).value
            except (TypeError, ValueError):
                # Keep the queue's raw state in QueueSnapshot/ProtocolEvent,
                # but do not silently map a future enum to an existing state.
                continue
            task_states[str(task_id)] = state
            manager = self._experiment_managers_by_mode.get(mode)
            experiment = manager.current_experiment if manager is not None else None
            if experiment is not None and experiment.id == task_id:
                if state == TaskState.RUNNING.value:
                    mark_execution_started(experiment)
                elif state in ("COMPLETED", "FAILED", "TERMINATED", "TIMEOUT"):
                    mark_execution_finished(experiment)
                experiment.state = state
        self._queue_snapshots_by_mode[mode] = QueueSnapshot(
            qubit_mode=mode,
            queue=tuple(dict(item) for item in queue_snapshot),
            current_task_id=data.get("currentTaskId") or None,
        )
        self._mark_ready_from_initial_push(mode, "queue")
        queue_value = data.get("queue") if isinstance(data, dict) else None
        queue_count = len(queue_value) if isinstance(queue_value, list) else 0
        logger.debug(
            "Experiment queue updated for %s: task_count=%d, has_current_task=%s",
            mode.name,
            queue_count,
            bool(data.get("currentTaskId")) if isinstance(data, dict) else False,
        )
        manager = self._experiment_managers_by_mode.get(mode)
        current_experiment = manager.current_experiment if manager is not None else None
        if current_experiment is None:
            return
        for i, queue in enumerate(queue_snapshot):
            if queue.get("id") == current_experiment.id:
                if i != 0:
                    logger.info(f"Experiment waiting in queue... {i} experiments ahead")


    def _on_heartbeat_timeout(self):
        """Heartbeat timeout callback."""
        self.connection.abort("Connection closed after server activity timeout")


    def _set_connection_state(self, state: ConnectionState) -> None:
        state = ConnectionState(state)
        with self._connection_state_lock:
            if self.connection_state == state:
                return
            self.connection_state = state
        with self._observer_lock:
            observers = tuple(self._connection_state_observers)
        for observer in observers:
            self._observer_dispatcher.submit(observer, state)


    def get_connection_state(self) -> ConnectionState:
        with self._connection_state_lock:
            return self.connection_state


    def _on_transport_disconnected(self, reason: str) -> None:
        """Handle an unexpected transport loss without resubmitting tasks."""
        reason = safe_reason(reason, (self.account, self.password, self.session_id))
        self.last_disconnect_reason = reason
        task_ids = [manager.current_experiment.id for manager in self._experiment_managers_by_mode.values()
                    if manager.current_experiment is not None]
        self.is_connected = False
        self.is_logged_in = False
        self.logging_in = False
        self.heartbeat_manager.stop()
        self._fail_all_pending_requests(reason)
        # A queue snapshot describes server state at one point in time.  Once
        # the transport is lost it is stale, so expose an empty queue until the
        # server sends a fresh snapshot after re-authentication.  Deliberately
        # leave local pending requests untouched: reconnect must neither claim
        # that they completed nor submit them a second time.
        for mode in self._experiment_queues_by_mode:
            self._experiment_queues_by_mode[mode] = []
        self._queue_snapshots_by_mode.clear()
        self._set_connection_state(ConnectionState.DISCONNECTED)
        if self._disconnect_callback is not None:
            self._disconnect_callback(reason, {"task_ids": task_ids})
        logger.warning(f"Transport disconnected: {reason}")
        if self.auto_reconnect and not self._manual_disconnect:
            self._schedule_reconnect()

    def set_disconnect_callback(self, callback):
        """Internal public-device bridge; application observers are queued by Device."""
        self._disconnect_callback = callback


    def _reconnect_delay(self, attempt: int) -> float:
        delay = self.reconnect_initial_delay * (self.reconnect_multiplier ** attempt)
        return min(delay, self.reconnect_max_delay)


    def _schedule_reconnect(self) -> None:
        with self._reconnect_lock:
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return
            self._reconnect_stop.clear()
            self._reconnect_thread = threading.Thread(
                target=self._run_reconnect_loop,
                daemon=True,
                name="SpinQLabLinkReconnect",
            )
            self._reconnect_thread.start()


    def _run_reconnect_loop(self, max_attempts: Optional[int] = None) -> bool:
        """Reconnect and re-login; never resubmit pending experiment requests."""
        attempt = 0
        while not self._reconnect_stop.is_set():
            if max_attempts is not None and attempt >= max_attempts:
                return False
            delay = self._reconnect_delay(attempt)
            if self._reconnect_stop.wait(delay):
                return False
            if self.connection.connect():
                self.is_connected = True
                self._set_connection_state(ConnectionState.CONNECTED)
                try:
                    sequence_id = self._login()
                    response = self.wait_for_request_response(
                        sequence_id,
                        timeout=self.request_timeout,
                    )
                except Exception as exc:
                    logger.warning(
                        "Reconnect login attempt failed before authentication: %s",
                        exc,
                    )
                    self.connection.abort("Reconnect login attempt failed")
                    self.is_connected = False
                    self.is_logged_in = False
                    self.logging_in = False
                    self._set_connection_state(ConnectionState.DISCONNECTED)
                    attempt += 1
                    continue
                if response.success and self.is_logged_in:
                    return True
                # Authentication was explicitly rejected. Retrying unchanged
                # credentials would create a tight login-failure loop; return
                # the failure to the caller and keep business traffic closed.
                return False
            attempt += 1
        return False


    def connect(self, auto_login: bool = True):
        """Connect and optionally preserve the 1.0 automatic-login flow."""
        self._ensure_dispatchers_running()
        self._manual_disconnect = False
        self.last_disconnect_reason = None
        self._reconnect_stop.clear()
        if self.connection.connect():
            self.is_connected = True
            self._set_connection_state(ConnectionState.CONNECTED)
            if auto_login and self.account and self.password:
                self._login()
            elif auto_login:
                logger.info("Connected; call login(account, password) to authenticate")
            return True
        else:
            self._set_connection_state(ConnectionState.DISCONNECTED)
            return False


    def _login(self):
        return self.login()


    def login(
        self,
        account: Optional[str] = None,
        password: Optional[str] = None,
        previous_session_id: Optional[str] = None,
    ) -> int:
        """Authenticate an established connection using explicit credentials."""
        if not self.is_connected:
            raise ConnectionError("Not connected, unable to login")
        if self.is_logged_in:
            raise RuntimeError("Already authenticated; logout before logging in again")
        if account is not None:
            if not isinstance(account, str) or not account:
                raise ValueError("account must be a non-empty string")
            self.account = account
            LoggerManager.register_secret(account)
        if password is not None:
            if not isinstance(password, str) or not password:
                raise ValueError("password must be a non-empty string")
            self.password = password
            LoggerManager.register_secret(password)
        if not self.account or not self.password:
            raise ValueError("account and password are required for login")
        if previous_session_id is not None:
            if not isinstance(previous_session_id, str):
                raise ValueError("previous_session_id must be a string or None")
            self.session_id = previous_session_id
        self.logging_in = True
        return self._send_message(
            MachineType.MSG_REQ_USER_LOGIN,
            {"account": self.account, "password": self.password},
            expected_response_msg_id=MachineType.MSG_RES_USER_LOGIN,
        )


    def logout(self, timeout=1.0):
        if not self.is_connected:
            logger.error("Not connected, unable to logout")
            return False
        if not self.is_logged_in:
            logger.warning("Not authenticated, skipping logout request")
            self.heartbeat_manager.stop()
            self.logging_in = False
            return False

        try:
            self._send_message(MachineType.MSG_REQ_USER_LOGOUT, {})
            sent = True
        except (ConnectionError, PermissionError, ValueError) as exc:
            logger.error(f"Unable to send logout request: {exc}")
            sent = False
        if sent:
            self.connection.wait_for_send_queue(timeout=timeout)

        # Stop heartbeat
        self.heartbeat_manager.stop()
        self.is_logged_in = False
        self.logging_in = False
        return sent


    def disconnect(self, timeout=5.0):
        """Release reconnect, heartbeat, transport and dispatch workers."""
        deadline = time.monotonic() + timeout
        self._manual_disconnect = True
        self._reconnect_stop.set()
        if self.is_connected and self.is_logged_in:
            self.logout(timeout=min(1.0, max(0, deadline - time.monotonic())))
        self.heartbeat_manager.stop()
        # Stop accepting callbacks before closing the transport.
        transport_closed = self.connection.disconnect(timeout=max(0, deadline - time.monotonic()))
        self.is_connected = False
        self.is_logged_in = False
        self.logging_in = False
        self.connection_state = ConnectionState.DISCONNECTED
        self._fail_all_pending_requests("Device closed")
        workers_closed = self._close_dispatchers(timeout=max(0, deadline - time.monotonic()))
        worker = self._reconnect_thread
        if worker is not None and worker is not threading.current_thread():
            worker.join(max(0, deadline - time.monotonic()))
        if not transport_closed or not workers_closed or (worker is not None and worker.is_alive() and worker is not threading.current_thread()):
            raise TimeoutError("Lab worker cleanup timed out")
        return True


    def wait_for_login(self, timeout: int = 10):
        start_time = time.time()
        if(self.logging_in):
            while not self.is_logged_in:
                if time.time() - start_time > timeout:
                    logger.error("Login timeout")
                    self.disconnect()
                    return False
                time.sleep(0.5)
            self.logging_in = False
            return True
        else:
            return False


    def get_connection(self):
        return self.is_connected


    def get_expMgr(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ) -> ExperimentManager:
        mode = self._coerce_snapshot_mode(qubit_mode)
        return self._experiment_managers_by_mode.setdefault(mode, ExperimentManager())


    def get_task_state(
        self,
        task_id: str,
        qubit_mode: Optional[QubitMode] = None,
    ) -> Optional[TaskState]:
        """Return a known authoritative task state, or None if unavailable."""
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")
        mode = self._coerce_snapshot_mode(qubit_mode)
        raw_state = self._task_states_by_mode.get(mode, {}).get(task_id)
        if raw_state is None:
            return None
        return TaskState(raw_state)


    def observe_events(self, callback):
        """Observe all decoded protocol events and return an unsubscribe function."""
        self.register_event_observer(callback)
        return lambda: self.unregister_event_observer(callback)


    def observe_connection_state(self, callback, *, emit_current: bool = True):
        """Observe connection-state changes and return an unsubscribe function."""
        self.register_connection_state_observer(callback, emit_current=emit_current)
        return lambda: self.unregister_connection_state_observer(callback)


    def wait_for_event_dispatch(self) -> None:
        """Wait until all already-decoded server messages have been handled."""
        self._event_dispatcher.wait_until_idle()
        self._observer_dispatcher.wait_until_idle()
