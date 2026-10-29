# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private Lab requests behavior; state is owned by the backend session."""
from ._imports import *  # noqa: F403


class RequestsMixin:
    def _send_message(
        self,
        msg_id: str,
        data: dict,
        qubit_mode: Optional[QubitMode] = None,
        expected_response_msg_id: Optional[str] = None,
        target_qubit_mode: Optional[QubitMode] = None,
        task_id: Optional[str] = None,
        response_timeout: Optional[float] = None,
    ) -> int:
        # Protocol section 2 permits only the login request before the
        # connection is authenticated.  Keep this check in the central send
        # path so internal callers cannot bypass the public business guards.
        if msg_id != MachineType.MSG_REQ_USER_LOGIN and not self.is_logged_in:
            raise PermissionError(
                f"Client authentication is required before sending {msg_id}"
            )

        metadata = self._pack_metadata()
        if self.transport == "websocket":
            serialized_message = self.protocol.serialize_payload(
                msg_id,
                metadata,
                data,
                qubit_mode=qubit_mode,
            )
        else:
            serialized_message = self.protocol.serialize_message(
                msg_id,
                metadata,
                data,
                qubit_mode=qubit_mode,
            )
        if not serialized_message:
            raise ValueError(f"Unable to serialize message: {msg_id}")

        pending = None
        if expected_response_msg_id is not None:
            pending = PendingRequest(
                session_id=metadata["session_id"],
                sequence_id=metadata["sequence_id"],
                request_msg_id=msg_id,
                expected_response_msg_id=expected_response_msg_id,
                target_qubit_mode=target_qubit_mode,
                task_id=task_id,
            )
            with self._request_lock:
                self._pending_requests[(pending.session_id, pending.sequence_id)] = pending

            timeout = self.request_timeout if response_timeout is None else float(response_timeout)
            if timeout <= 0:
                with self._request_lock:
                    self._pending_requests.pop((pending.session_id, pending.sequence_id), None)
                raise ValueError("response_timeout must be positive")
            timer = threading.Timer(
                timeout,
                self._expire_pending_request,
                args=((pending.session_id, pending.sequence_id), pending),
            )
            timer.daemon = True
            pending.timeout_timer = timer
            timer.start()

        if not self.connection.send(serialized_message):
            if pending is not None:
                with self._request_lock:
                    self._pending_requests.pop((pending.session_id, pending.sequence_id), None)
                if pending.timeout_timer is not None:
                    pending.timeout_timer.cancel()
            raise ConnectionError(f"Unable to send message: {msg_id}")

        return metadata["sequence_id"]


    def _remember_request_error(self, sequence_id: int, error: BaseException) -> None:
        self._request_errors[sequence_id] = error
        self._request_errors.move_to_end(sequence_id)
        while len(self._request_errors) > self.response_cache_size:
            self._request_errors.popitem(last=False)


    def _expire_pending_request(
        self,
        key: Tuple[str, int],
        pending: PendingRequest,
    ) -> None:
        with self._request_lock:
            if self._pending_requests.get(key) is not pending:
                return
            self._pending_requests.pop(key, None)
            error = RequestResponseTimeoutError(
                f"Timed out waiting for response to sequence_id {pending.sequence_id}"
            )
            pending.error = error
            self._remember_request_error(pending.sequence_id, error)
            pending.completed.set()


    def _fail_all_pending_requests(self, reason: str) -> None:
        """Wake all request waiters without guessing whether the server acted."""
        with self._request_lock:
            pending_items = list(self._pending_requests.items())
            self._pending_requests.clear()
            for _, pending in pending_items:
                if pending.timeout_timer is not None:
                    pending.timeout_timer.cancel()
                error = RequestOutcomeUnknownError(
                    f"Request {pending.sequence_id} outcome is unknown: {reason}"
                )
                pending.error = error
                self._remember_request_error(pending.sequence_id, error)
                pending.completed.set()


    def _find_pending_request(
        self,
        sequence_id: int,
        response_session_id: str,
    ) -> Optional[PendingRequest]:
        """Find a request by session and sequence, with login-session fallback."""
        candidate_keys = (
            (response_session_id, sequence_id),
            (self.session_id, sequence_id),
            ("", sequence_id),
        )
        with self._request_lock:
            for key in candidate_keys:
                pending = self._pending_requests.get(key)
                if pending is not None:
                    return pending

            # sequence_id is monotonically unique for this SDK instance, so
            # this fallback safely handles servers that omit response session_id.
            for (_, pending_sequence), pending in self._pending_requests.items():
                if pending_sequence == sequence_id:
                    return pending
        return None


    def _complete_request_response(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ) -> Optional[RequestResponse]:
        prepared = self._prepare_request_response(data, envelope)
        if prepared is None:
            return None
        response, pending = prepared
        self._commit_request_response(response, pending)
        return response


    def _prepare_request_response(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ) -> Optional[Tuple[RequestResponse, PendingRequest]]:
        """Build and detach a response before publishing it to waiters."""
        metadata = envelope.get("metadata", {})
        sequence_id = metadata.get("sequence_id")
        if sequence_id is None:
            logger.warning("Response is missing metadata.sequence_id")
            return None

        sequence_id = int(sequence_id)
        with self._request_lock:
            if sequence_id in self._request_responses:
                self._duplicate_response_count += 1
                logger.warning(
                    "Duplicate response ignored: sequence_id=%s, msg_id=%s",
                    sequence_id,
                    envelope.get("msg_id", ""),
                )
                return None

        pending = self._find_pending_request(
            sequence_id,
            str(metadata.get("session_id", "")),
        )
        if pending is None:
            with self._request_lock:
                self._unmatched_response_count += 1
            logger.warning(f"Unmatched response sequence_id: {sequence_id}")
            return None

        response_msg_id = envelope.get("msg_id", "")
        if response_msg_id != pending.expected_response_msg_id:
            logger.warning(
                "Unexpected response message: "
                f"expected {pending.expected_response_msg_id}, got {response_msg_id}"
            )
            return None

        raw_server_mode = envelope.get("qubit_mode")
        try:
            server_mode = QubitMode(raw_server_mode)
        except (TypeError, ValueError):
            server_mode = None

        try:
            raw_code = int(data.get("code", ProtocolErrorCode.UNKNOWN_ERROR))
        except (TypeError, ValueError):
            raw_code = int(ProtocolErrorCode.UNKNOWN_ERROR)

        response = RequestResponse(
            sequence_id=pending.sequence_id,
            request_msg_id=pending.request_msg_id,
            response_msg_id=response_msg_id,
            target_qubit_mode=pending.target_qubit_mode,
            server_qubit_mode=server_mode,
            raw_code=raw_code,
            message=str(data.get("message", "")),
            task_id=(
                data.get("taskId") or pending.task_id
                if raw_code == ProtocolErrorCode.SUCCESS
                else data.get("taskId") or None
            ),
            raw_data=dict(data),
        )

        with self._request_lock:
            self._pending_requests.pop((pending.session_id, pending.sequence_id), None)
            if pending.timeout_timer is not None:
                pending.timeout_timer.cancel()

        return response, pending


    def _commit_request_response(
        self,
        response: RequestResponse,
        pending: PendingRequest,
    ) -> None:
        """Publish a response only after its protocol side effects are applied."""
        with self._request_lock:
            self._request_responses[pending.sequence_id] = response
            self._request_responses.move_to_end(pending.sequence_id)
            while len(self._request_responses) > self.response_cache_size:
                self._request_responses.popitem(last=False)
            if not response.success:
                self._last_request_error = response
            pending.response = response
            pending.completed.set()


    def _handle_business_response(self, data: Dict[str, Any], envelope: Dict[str, Any]):
        """Correlate a business response before applying current server mode."""
        prepared = self._prepare_request_response(data, envelope)
        if prepared is None:
            return
        response, pending = prepared

        try:
            server_mode = self._read_authoritative_qubit_mode(envelope, require_present=False)
            if server_mode is not None:
                self._set_authoritative_qubit_mode(
                    server_mode,
                    require_snapshot_sync=(server_mode != self.get_qubit_mode()),
                )

            if not response.success:
                logger.error(
                    f"Request failed: code={response.raw_code}, message={response.message}, "
                    f"sequence_id={response.sequence_id}"
                )
                if response.raw_code == ProtocolErrorCode.NOT_LOGIN:
                    self.is_logged_in = False
                    self.logging_in = False
                    self.heartbeat_manager.stop()
                    self._set_connection_state(ConnectionState.CONNECTED)
                    self._login()
                    return
                if (
                    response.raw_code == ProtocolErrorCode.QUBIT_MODE_MISMATCH
                    and server_mode is not None
                ):
                    self._fail_pending_requests_outside_mode(server_mode)
                if (
                    response.raw_code == ProtocolErrorCode.QUBIT_MODE_UNSUPPORTED
                    and response.target_qubit_mode is not None
                ):
                    with self._qubit_mode_lock:
                        self._unsupported_qubit_modes.add(response.target_qubit_mode)
                if response.request_msg_id == MachineType.MSG_REQ_ADD_EXP_TASK_REQ:
                    target_mode = response.target_qubit_mode or QubitMode.TWO
                    manager = self._experiment_managers_by_mode.get(target_mode)
                    if manager is not None and manager.current_experiment is not None:
                        manager.current_experiment.state = "FAILED"
                    self.heartbeat_manager.resume_timeout()
                return

            if response.request_msg_id == MachineType.MSG_REQ_ADD_EXP_TASK_REQ:
                target_mode = response.target_qubit_mode or QubitMode.TWO
                handler = self._exp_handler_maps_by_mode.get(target_mode, {}).get(
                    MachineType.MSG_RES_ADD_EXP_TASK_RES
                )
                if handler is not None:
                    handler(data)
        finally:
            # A waiter observing the response must also observe all state
            # changes prescribed by that response code.
            self._commit_request_response(response, pending)


    def _fail_pending_requests_outside_mode(self, authoritative_mode: QubitMode) -> None:
        """Stop in-flight business requests targeting a now-stale mode."""
        with self._request_lock:
            stale = [
                (key, pending)
                for key, pending in self._pending_requests.items()
                if pending.target_qubit_mode is not None
                and pending.target_qubit_mode != authoritative_mode
            ]
            for key, pending in stale:
                self._pending_requests.pop(key, None)
                if pending.timeout_timer is not None:
                    pending.timeout_timer.cancel()
                error = QubitModeMismatchError(
                    f"Request {pending.sequence_id} stopped after authoritative mode "
                    f"changed to {authoritative_mode.name}"
                )
                pending.error = error
                self._remember_request_error(pending.sequence_id, error)
                pending.completed.set()


    def _next_sequence_id(self) -> int:
        """Return a thread-safe, monotonically increasing client message ID."""
        with self._sequence_lock:
            self._sequence_id += 1
            return self._sequence_id


    def _pack_metadata(self) -> Dict[str, Any]:
        metadata = {}
        metadata["sequence_id"] = self._next_sequence_id()
        metadata["timestamp"] = int(time.time() * 1000)
        metadata["account"] = self.account
        metadata["session_id"] = self.session_id
        return metadata


    def wait_for_request_response(
        self,
        sequence_id: int,
        timeout: float = 10.0,
    ) -> RequestResponse:
        with self._request_lock:
            completed = self._request_responses.get(sequence_id)
            if completed is not None:
                return completed
            previous_error = self._request_errors.get(sequence_id)
            if previous_error is not None:
                raise previous_error
            pending = next(
                (
                    request
                    for (_, pending_sequence), request in self._pending_requests.items()
                    if pending_sequence == sequence_id
                ),
                None,
            )

        if pending is None:
            raise KeyError(f"Unknown request sequence_id: {sequence_id}")
        if not pending.completed.wait(timeout):
            raise RequestResponseTimeoutError(
                f"Timed out waiting for response to sequence_id {sequence_id}"
            )
        if pending.error is not None:
            raise pending.error
        if pending.response is None:
            raise RuntimeError(f"Request {sequence_id} completed without a response")
        return pending.response


    def get_request_response(self, sequence_id: int) -> Optional[RequestResponse]:
        with self._request_lock:
            return self._request_responses.get(sequence_id)


    def get_last_request_error(self) -> Optional[RequestResponse]:
        with self._request_lock:
            return self._last_request_error


    def get_request_diagnostics(self) -> Dict[str, int]:
        """Return non-sensitive request-correlation counters."""
        with self._request_lock:
            return {
                "pending": len(self._pending_requests),
                "cached_responses": len(self._request_responses),
                "duplicate_responses": self._duplicate_response_count,
                "unmatched_responses": self._unmatched_response_count,
            }
