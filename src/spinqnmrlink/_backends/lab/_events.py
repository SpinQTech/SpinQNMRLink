# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private Lab events behavior; state is owned by the backend session."""
from ._imports import *  # noqa: F403


class EventsMixin:
    def _handle_transport_data(self, data: bytes):
        """Decode on the network thread, then enqueue messages in wire order."""
        self._decode_received_data(data, asynchronous=True)


    def _handle_received_message(self, data: bytes):
        """Backward-compatible synchronous injection hook used by integrations/tests."""
        self._decode_received_data(data, asynchronous=False)


    def _decode_received_data(self, data: bytes, *, asynchronous: bool):
        try:
            self.heartbeat_manager.on_server_activity()
            messages = (
                [self.protocol.deserialize_payload(data)]
                if self.transport == "websocket"
                else self.protocol.deserialize_messages(data)
            )
            for dict_data in messages:
                if asynchronous:
                    self._event_dispatcher.submit(dict_data)
                else:
                    self._dispatch_received_message(dict_data)
        except ProtocolFrameError as e:
            logger.error(f"Protocol framing error: {e}")
            reason = f"Connection closed after protocol error: {e}"
            self.connection.abort(reason)
        except Exception as e:
            logger.error(f"Failed to parse received message: {e}")


    def _dispatch_received_message(self, dict_data: Dict[str, Any]):
        """Dispatch one already decoded message."""
        try:
            try:
                msg_id = dict_data["msg_id"]
                self._publish_protocol_event(dict_data)

                if msg_id == MachineType.MSG_POST_EXP_STARTED:
                    self.heartbeat_manager.resume_timeout()

                handler = self.handler_map.get(msg_id)
                if handler:
                    if "json_data" in dict_data:
                        payload = normalize_common_json(msg_id, dict_data["json_data"])
                        if msg_id in (
                            MachineType.MSG_RES_USER_LOGIN,
                            MachineType.MSG_POST_QUBIT_MODE_CHANGED,
                            MachineType.MSG_RES_ADD_EXP_TASK_RES,
                            MachineType.MSG_RES_TERMINATE_EXP_TASK_RES,
                            MachineType.MSG_POST_PARAM,
                            MachineType.MSG_POST_LOCK_DATA,
                            MachineType.MSG_POST_INFO,
                            MachineType.MSG_POST_SAMPLE_CALIBRATION,
                            MachineType.MSG_POST_EXP_QUEUE_UPDATE,
                        ):
                            handler(payload, dict_data)
                        else:
                            handler(payload)
                    else:
                        logger.warning(f"Received message {msg_id} without json_data, skipping")
                else:
                    push_mode = self._mode_from_envelope(
                        dict_data,
                        context=f"experiment push {msg_id}",
                    )
                    if push_mode is None:
                        logger.warning(f"Dropping experiment push with invalid mode: {msg_id}")
                        return
                    handler_map = self._exp_handler_maps_by_mode.get(push_mode, {})
                    handler = handler_map.get(msg_id)
                    if handler:
                        if "json_data" in dict_data:
                            raw_payload = dict_data["json_data"]
                            explicit_null_data = (
                                isinstance(raw_payload, dict)
                                and "data" in raw_payload
                                and raw_payload["data"] is None
                            )
                            payload = normalize_common_json(msg_id, raw_payload)
                            # A custom decoder/handler may distinguish an
                            # omitted optional field from an explicit null.
                            # Keep that distinction at the extension boundary.
                            if (
                                isinstance(raw_payload, dict)
                                and "data" not in raw_payload
                                and msg_id in (
                                    MachineType.MSG_POST_EXP_STEP_CHANGED,
                                    MachineType.MSG_POST_EXP_DATA_UPDATED,
                                    MachineType.MSG_POST_EXP_FINISHED,
                                )
                            ):
                                payload.pop("data", None)
                            decoder = self._experiment_decoders.get(msg_id)
                            if decoder is not None:
                                payload = decoder(payload)
                            if msg_id in (
                                MachineType.MSG_POST_EXP_CHART_UPDATED_STARTED,
                                MachineType.MSG_POST_EXP_CHART_UPDATED_FINISHED,
                            ):
                                self._handle_chart_stream(msg_id, dict(payload), push_mode)
                            logger.debug(
                                "Received experiment JSON message %s for %s: %s",
                                msg_id,
                                push_mode.name,
                                summarize_payload(dict_data.get("json_data")),
                            )
                            self._call_experiment_handler(
                                handler,
                                msg_id,
                                payload,
                                push_mode,
                                explicit_null_data=explicit_null_data,
                            )
                        elif "chart_data" in dict_data and dict_data["chart_data"]:
                            chart_data = dict(dict_data["chart_data"])
                            self._handle_chart_stream(msg_id, chart_data, push_mode)
                            # ``retain_chart_points=False`` is an explicit
                            # streaming-only choice.  The experiment
                            # handlers append every chunk to their result
                            # objects, so calling them here would silently
                            # defeat that choice and retain the full stream.
                            if self.retain_chart_points:
                                handler(chart_data)
                    else:
                        self._publish_unknown_message(dict_data, push_mode)
                        logger.warning(
                            f"Message handler not found for mode {push_mode.name}: {msg_id}"
                        )
            except KeyError as e:
                logger.error(f"Key error occurred while processing message: {e}")
            except Exception as e:
                logger.error(f"Exception occurred while processing message: {e}")
                # A malformed or slow user event handler must not tear down an
                # otherwise healthy transport connection.
        except Exception as e:
            logger.error(f"Failed to dispatch received message: {e}")


    def _publish_unknown_message(
        self,
        envelope: Dict[str, Any],
        mode: Optional[QubitMode],
    ) -> None:
        event = self._event_from_envelope(envelope, UnknownMessage)
        for observer in tuple(self._unknown_message_observers):
            try:
                observer(event)
            except Exception as exc:
                logger.error("Unknown-message observer failed: %s", exc)


    def _handle_chart_stream(
        self,
        msg_id: str,
        chart_data: Dict[str, Any],
        mode: QubitMode,
    ) -> None:
        task_id = chart_data.get("taskId")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("Chart data taskId must be a non-empty string")

        is_chunk = msg_id == MachineType.MSG_POST_EXP_CHART_UPDATED
        if is_chunk:
            for field in ("group", "chart_name"):
                value = chart_data.get(field)
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"Chart data {field} must be a non-empty string"
                    )
            points = chart_data.get("points")
            if not isinstance(points, list) or not points:
                raise ValueError("Chart data points must be a non-empty list")
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    raise ValueError("Each chart point must contain exactly x and y")
                if any(
                    isinstance(value, bool) or not isinstance(value, (int, float))
                    for value in point
                ):
                    raise ValueError("Chart point x and y must be numbers")

        key = ChartKey(
            task_id=task_id,
            group=str(chart_data.get("group", "")),
            chart_name=str(chart_data.get("chart_name", "")),
            path=chart_data.get("path") or None,
            qubit=chart_data.get("qubit") or None,
            step=chart_data.get("step") or None,
        )
        boundary = (
            "started" if msg_id == MachineType.MSG_POST_EXP_CHART_UPDATED_STARTED
            else "finished" if msg_id == MachineType.MSG_POST_EXP_CHART_UPDATED_FINISHED
            else "chunk"
        )
        mode_streams = self._chart_streams_by_mode.setdefault(mode, {})
        active_boundaries = self._active_chart_boundaries_by_mode.setdefault(
            mode, set()
        )
        boundary_identity = (
            key.task_id,
            key.group or None,
            key.chart_name or None,
            key.path,
            key.qubit,
            key.step,
        )

        def matches_boundary(candidate: ChartKey, identity) -> bool:
            values = (
                candidate.task_id,
                candidate.group or None,
                candidate.chart_name or None,
                candidate.path,
                candidate.qubit,
                candidate.step,
            )
            return values[0] == identity[0] and all(
                expected is None or actual == expected
                for actual, expected in zip(values[1:], identity[1:])
            )

        if boundary == "started":
            active_boundaries.add(boundary_identity)
            for existing_key, stream in mode_streams.items():
                if matches_boundary(existing_key, boundary_identity):
                    stream["started"] = True
                    stream["finished"] = False
        elif boundary == "finished":
            active_boundaries.discard(boundary_identity)
            for existing_key, stream in mode_streams.items():
                if matches_boundary(existing_key, boundary_identity):
                    stream["finished"] = True
        else:
            stream = mode_streams.setdefault(
                key,
                {"started": False, "finished": False, "points": []},
            )
            if any(matches_boundary(key, identity) for identity in active_boundaries):
                stream["started"] = True
            if self.retain_chart_points:
                stream["points"].extend(chart_data["points"])

        for consumer in tuple(self._chart_consumers):
            try:
                consumer(key, boundary, chart_data)
            except Exception as exc:
                logger.error("Chart consumer failed: %s", exc)
        for consumer in tuple(self._mode_chart_consumers):
            try:
                consumer(mode, key, boundary, chart_data)
            except Exception as exc:
                logger.error("Mode chart consumer failed: %s", exc)


    def add_task(
        self,
        task: Union[Task, Dict[str, Any]],
        qubit_mode: Optional[QubitMode] = None,
    ) -> int:
        """Submit a protocol Task without interpreting its params contents."""
        if not self.is_logged_in:
            raise RuntimeError("Login is required before adding a task")
        target_mode = self._validate_target_qubit_mode(qubit_mode)
        task_model = task if isinstance(task, Task) else Task.from_dict(task)
        para = task_model.to_submission_dict()
        # Task ownership is authoritative from the authenticated session.
        para["account"] = self.account
        task_id = para.get("id")
        with self._request_lock:
            pending_task_ids = {
                request.task_id
                for request in self._pending_requests.values()
                if request.request_msg_id == MachineType.MSG_REQ_ADD_EXP_TASK_REQ
            }
            queued_task_ids = {
                item.get("id")
                for item in self._experiment_queues_by_mode.get(target_mode, [])
            }
            if (
                task_id in self._submitted_task_ids
                or task_id in pending_task_ids
                or task_id in queued_task_ids
            ):
                raise DuplicateTaskIdError(
                    f"Experiment task id has already been submitted: {task_id}"
                )
        logger.debug(
            "Sending experiment task: id=%s, type=%s, parameter_fields=%s",
            para.get("id"),
            para.get("type"),
            sorted(para.keys()),
        )
        # Queue duration and connection liveness are independent. Valid server
        # activity refreshes heartbeat; accepting a task must not suspend it.
        envelope_mode = QubitMode.THREE if target_mode is QubitMode.THREE else None
        sequence_id = self._send_message(
            MachineType.MSG_REQ_ADD_EXP_TASK_REQ,
            para,
            qubit_mode=envelope_mode,
            expected_response_msg_id=MachineType.MSG_RES_ADD_EXP_TASK_RES,
            target_qubit_mode=target_mode,
            task_id=task_id,
        )
        with self._request_lock:
            self._submitted_task_ids.add(task_id)
        return sequence_id


    def register_event_observer(self, callback) -> None:
        if callback not in self._event_observers:
            self._event_observers.append(callback)


    def unregister_event_observer(self, callback) -> None:
        if callback in self._event_observers:
            self._event_observers.remove(callback)


    def register_connection_state_observer(
        self,
        callback,
        *,
        emit_current: bool = True,
    ) -> None:
        if not callable(callback):
            raise ValueError("connection state observer must be callable")
        with self._observer_lock:
            if callback not in self._connection_state_observers:
                self._connection_state_observers.append(callback)
        if emit_current:
            self._observer_dispatcher.submit(callback, self.get_connection_state())


    def unregister_connection_state_observer(self, callback) -> None:
        with self._observer_lock:
            if callback in self._connection_state_observers:
                self._connection_state_observers.remove(callback)


    def register_unknown_message_observer(self, callback) -> None:
        if callback not in self._unknown_message_observers:
            self._unknown_message_observers.append(callback)


    def unregister_unknown_message_observer(self, callback) -> None:
        if callback in self._unknown_message_observers:
            self._unknown_message_observers.remove(callback)


    def register_chart_consumer(self, callback) -> None:
        if callback not in self._chart_consumers:
            self._chart_consumers.append(callback)


    def unregister_chart_consumer(self, callback) -> None:
        if callback in self._chart_consumers:
            self._chart_consumers.remove(callback)


    def unregister_experiment_decoder(self, msg_id: str) -> None:
        self._experiment_decoders.pop(msg_id, None)


    def get_chart_stream(
        self,
        key: ChartKey,
        qubit_mode: Optional[QubitMode] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return one defensive chart snapshot from one isolated mode domain."""
        if not isinstance(key, ChartKey):
            raise ValueError("key must be a ChartKey")
        mode = self._coerce_snapshot_mode(qubit_mode)
        stream = self._chart_streams_by_mode.get(mode, {}).get(key)
        if stream is None:
            return None
        return {
            "mode": mode,
            "started": stream["started"],
            "finished": stream["finished"],
            "points": [list(point) for point in stream["points"]],
        }


    def get_chart_streams(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ) -> Dict[ChartKey, Dict[str, Any]]:
        """Return defensive snapshots for every chart in one mode domain."""
        mode = self._coerce_snapshot_mode(qubit_mode)
        return {
            key: {
                "mode": mode,
                "started": stream["started"],
                "finished": stream["finished"],
                "points": [list(point) for point in stream["points"]],
            }
            for key, stream in self._chart_streams_by_mode.get(mode, {}).items()
        }
