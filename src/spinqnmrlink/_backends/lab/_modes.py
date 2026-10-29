# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private Lab modes behavior; state is owned by the backend session."""
from ._imports import *  # noqa: F403


class ModesMixin:
    def _new_device(self) -> Device:
        return Device(
            device_id=self.device_id,
            device_type="SpinQLabLink",
            device_params={},
        )


    def _activate_mode(
        self,
        mode: QubitMode,
        reset_runtime_snapshots: bool = False,
    ) -> None:
        """Point compatibility attributes at one mode's isolated state."""
        mode = QubitMode(mode)
        if reset_runtime_snapshots or mode not in self._devices_by_mode:
            self._devices_by_mode[mode] = self._new_device()
            self._experiment_queues_by_mode[mode] = []
            self._task_states_by_mode[mode] = {}
            self._received_mode_snapshot_kinds[mode] = set()
            self._active_chart_boundaries_by_mode[mode] = set()
        else:
            self._experiment_queues_by_mode.setdefault(mode, [])
            self._task_states_by_mode.setdefault(mode, {})

        self._experiment_managers_by_mode.setdefault(mode, ExperimentManager())
        self._exp_handler_maps_by_mode.setdefault(mode, {})

        self.device = self._devices_by_mode[mode]
        self.expMgr = self._experiment_managers_by_mode[mode]
        self.exp_handler_map = self._exp_handler_maps_by_mode[mode]
        self.hardware_connected = self.device.status.connected


    def _mode_from_envelope(
        self,
        envelope: Dict[str, Any],
        *,
        context: str,
    ) -> Optional[QubitMode]:
        """Resolve a pushed message's mode, defaulting omitted modes to TWO."""
        if not envelope.get("qubit_mode_present", False):
            return QubitMode.TWO
        raw_mode = envelope.get("qubit_mode")
        try:
            return QubitMode(raw_mode)
        except (TypeError, ValueError):
            self._record_qubit_mode_protocol_error(
                f"Unsupported protocol qubit mode in {context}: {raw_mode}"
            )
            return None


    def _read_authoritative_qubit_mode(
        self,
        envelope: Dict[str, Any],
        require_present: bool,
    ) -> Optional[QubitMode]:
        """Read a server-authoritative mode without inferring protocol version."""
        present = bool(envelope.get("qubit_mode_present", False))
        if not present:
            if require_present:
                self._record_qubit_mode_protocol_error(
                    "Qubit mode change notification is missing qubit_mode"
                )
                return None
            return QubitMode.TWO

        raw_mode = envelope.get("qubit_mode")
        try:
            return QubitMode(raw_mode)
        except (TypeError, ValueError):
            self._record_qubit_mode_protocol_error(
                f"Unsupported protocol qubit mode: {raw_mode}"
            )
            return None


    def _record_qubit_mode_protocol_error(self, message: str) -> None:
        """Save a mode protocol error so callers can inspect it."""
        with self._qubit_mode_lock:
            self.qubit_mode_protocol_error = message
        logger.error(message)


    def _set_authoritative_qubit_mode(
        self,
        mode: QubitMode,
        *,
        reset_runtime_snapshots: bool = False,
        require_snapshot_sync: bool = False,
    ) -> None:
        with self._qubit_mode_lock:
            mode_changed = self._current_qubit_mode != mode
            self._current_qubit_mode = mode
            self.qubit_mode_protocol_error = None
            self._activate_mode(
                mode,
                reset_runtime_snapshots=reset_runtime_snapshots or mode_changed,
            )
            if require_snapshot_sync:
                self._received_mode_snapshot_kinds[mode] = set()
                self._mode_snapshot_sync_pending = mode
            elif mode_changed:
                self._mode_snapshot_sync_pending = None
        if require_snapshot_sync and self.is_logged_in:
            self._set_connection_state(ConnectionState.AUTHENTICATED)
        if mode_changed:
            with self._observer_lock:
                observers = tuple(self._qubit_mode_observers)
            for observer in observers:
                self._observer_dispatcher.submit(observer, mode)


    def _handle_qubit_mode_changed(self, data: Dict[str, Any], envelope: Dict[str, Any]):
        """Apply a valid server-pushed mode change atomically."""
        mode = self._read_authoritative_qubit_mode(envelope, require_present=True)
        if mode is None:
            return
        # An explicit authoritative switch proves that the announced business
        # domain is exposed now. Do not let an older 1002 result poison it.
        with self._qubit_mode_lock:
            self._unsupported_qubit_modes.discard(mode)
        self._set_authoritative_qubit_mode(
            mode,
            reset_runtime_snapshots=True,
            require_snapshot_sync=True,
        )
        logger.info(f"Qubit mode changed to: {mode.name}")


    def _device_for_push(
        self,
        envelope: Dict[str, Any],
        *,
        context: str,
    ) -> Tuple[Optional[QubitMode], Optional[Device]]:
        mode = self._mode_from_envelope(envelope, context=context)
        if mode is None:
            return None, None
        self._observe_mode_state_push(mode)
        if mode not in self._devices_by_mode:
            self._devices_by_mode[mode] = self._new_device()
            self._experiment_queues_by_mode.setdefault(mode, [])
        return mode, self._devices_by_mode[mode]


    def _observe_mode_state_push(self, mode: QubitMode) -> None:
        """Refresh the authoritative mirror from a mode-state server push."""
        if mode != self.get_qubit_mode():
            self._set_authoritative_qubit_mode(
                mode,
                reset_runtime_snapshots=True,
                require_snapshot_sync=True,
            )


    def _handle_device_param_post(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ):
        mode, device = self._device_for_push(envelope, context="device parameters")
        if device is None:
            return
        logger.debug(
            "Device parameters updated for %s: %s",
            mode.name,
            summarize_payload(data),
        )
        device.set_device_params(data)
        self._mark_ready_from_initial_push(mode, "device_param")


    def _handle_device_info_post(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ):
        mode, device = self._device_for_push(envelope, context="device info")
        if device is None:
            return
        logger.debug(
            "Device info updated for %s: %s",
            mode.name,
            summarize_payload(data),
        )
        device.set_temp_data_post(data)
        if mode == self.get_qubit_mode():
            self.hardware_connected = device.status.connected
        self._mark_ready_from_initial_push(mode, "device_info")


    def _handle_sample_calibration_post(
        self,
        data: Dict[str, Any],
        envelope: Dict[str, Any],
    ):
        mode = self._mode_from_envelope(envelope, context="sample calibration")
        if mode is None:
            return
        self._observe_mode_state_push(mode)
        logger.debug(
            "Sample calibration updated for %s: %s",
            mode.name,
            summarize_payload(data),
        )
        self._mark_ready_from_initial_push(mode, "calibration")
        self._sample_calibration_by_mode[mode] = {
            "sampleLock": data.get("sampleLock"),
            "calibrateResult": data.get("calibrateResult"),
            "raw": dict(data),
        }


    def get_qubit_mode(self) -> Optional[QubitMode]:
        """Return the server-authoritative qubit mode for the current session."""
        with self._qubit_mode_lock:
            return self._current_qubit_mode


    @property
    def current_qubit_mode(self) -> Optional[QubitMode]:
        """Read-only compatibility view of the server-authoritative mode."""
        return self.get_qubit_mode()


    def get_qubit_mode_error(self) -> Optional[str]:
        """Return the latest mode protocol error, if any."""
        with self._qubit_mode_lock:
            return self.qubit_mode_protocol_error


    def _coerce_snapshot_mode(
        self,
        qubit_mode: Optional[QubitMode],
    ) -> QubitMode:
        if qubit_mode is None:
            current = self.get_qubit_mode()
            if current is None:
                raise RuntimeError("Authoritative qubit mode is unavailable")
            return current
        try:
            return QubitMode(qubit_mode)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "qubit_mode must be QubitMode.TWO or QubitMode.THREE"
            ) from exc


    def _validate_target_qubit_mode(
        self,
        qubit_mode: Optional[QubitMode],
    ) -> QubitMode:
        if qubit_mode is None:
            target_mode = QubitMode.TWO
        else:
            try:
                target_mode = QubitMode(qubit_mode)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "qubit_mode must be QubitMode.TWO or QubitMode.THREE"
                ) from exc

        capability = self.get_qubit_mode_capability(target_mode)
        if not capability.sdk_supported or capability.server_rejected:
            raise QubitModeUnsupportedError(capability.reason)

        current_mode = capability.authoritative_mode
        if current_mode is None:
            detail = self.get_qubit_mode_error() or "authoritative qubit mode is unavailable"
            raise RuntimeError(f"Cannot send business request: {detail}")
        if target_mode != current_mode:
            raise QubitModeMismatchError(
                f"Target mode {target_mode.name} does not match server mode {current_mode.name}"
            )
        return target_mode


    def is_qubit_mode_supported(self, mode: QubitMode) -> bool:
        capability = self.get_qubit_mode_capability(mode)
        return capability.sdk_supported and not capability.server_rejected


    def get_qubit_mode_capability(self, mode: QubitMode) -> QubitModeCapability:
        """Return an explainable SDK/server/current-mode capability report."""
        try:
            requested_mode = QubitMode(mode)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "mode must be QubitMode.TWO or QubitMode.THREE"
            ) from exc

        with self._qubit_mode_lock:
            authoritative_mode = self._current_qubit_mode
            sdk_supported = requested_mode in self._sdk_supported_qubit_modes
            server_rejected = requested_mode in self._unsupported_qubit_modes

        if not sdk_supported:
            reason = f"SDK does not implement {requested_mode.name} business tasks"
        elif server_rejected:
            reason = (
                f"Authenticated server explicitly rejected {requested_mode.name} "
                "with QUBIT_MODE_UNSUPPORTED"
            )
        elif authoritative_mode is None:
            reason = "Authoritative server qubit mode is unavailable"
        elif authoritative_mode is not requested_mode:
            reason = (
                f"Server is currently in {authoritative_mode.name}, not "
                f"{requested_mode.name}"
            )
        else:
            reason = f"SDK and current server mode allow {requested_mode.name} submission"

        return QubitModeCapability(
            mode=requested_mode,
            sdk_supported=sdk_supported,
            authoritative_mode=authoritative_mode,
            server_rejected=server_rejected,
            can_submit_now=(
                sdk_supported
                and not server_rejected
                and authoritative_mode is requested_mode
            ),
            reason=reason,
        )


    def get_device(self, qubit_mode: Optional[QubitMode] = None) -> Device:
        mode = self._coerce_snapshot_mode(qubit_mode)
        if mode not in self._devices_by_mode:
            self._devices_by_mode[mode] = self._new_device()
        return self._devices_by_mode[mode]


    def get_experiment_queue(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ) -> List[Dict[str, Any]]:
        """Return a defensive copy of one mode's latest queue snapshot."""
        mode = self._coerce_snapshot_mode(qubit_mode)
        return [dict(item) for item in self._experiment_queues_by_mode.get(mode, [])]


    def get_queue_snapshot(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ) -> QueueSnapshot:
        mode = self._coerce_snapshot_mode(qubit_mode)
        return self._queue_snapshots_by_mode.get(
            mode,
            QueueSnapshot(mode, tuple(), None),
        )


    def get_sample_calibration(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ) -> Dict[str, Any]:
        mode = self._coerce_snapshot_mode(qubit_mode)
        value = self._sample_calibration_by_mode.get(
            mode,
            {"sampleLock": None, "calibrateResult": None, "raw": {}},
        )
        return {
            "sampleLock": value["sampleLock"],
            "calibrateResult": value["calibrateResult"],
            "raw": dict(value["raw"]),
        }


    def register_qubit_mode_observer(
        self,
        callback,
        *,
        emit_current: bool = True,
    ) -> None:
        if not callable(callback):
            raise ValueError("qubit mode observer must be callable")
        with self._observer_lock:
            if callback not in self._qubit_mode_observers:
                self._qubit_mode_observers.append(callback)
        if emit_current:
            self._observer_dispatcher.submit(callback, self.get_qubit_mode())


    def unregister_qubit_mode_observer(self, callback) -> None:
        with self._observer_lock:
            if callback in self._qubit_mode_observers:
                self._qubit_mode_observers.remove(callback)


    def observe_qubit_mode(self, callback, *, emit_current: bool = True):
        """Observe authoritative mode changes and return an unsubscribe function."""
        self.register_qubit_mode_observer(callback, emit_current=emit_current)
        return lambda: self.unregister_qubit_mode_observer(callback)


    def register_mode_chart_consumer(self, callback) -> None:
        """Register a chart consumer receiving mode, key, boundary, data."""
        if not callable(callback):
            raise ValueError("mode chart consumer must be callable")
        if callback not in self._mode_chart_consumers:
            self._mode_chart_consumers.append(callback)


    def unregister_mode_chart_consumer(self, callback) -> None:
        if callback in self._mode_chart_consumers:
            self._mode_chart_consumers.remove(callback)


    def get_device_status(self) -> Dict[str, Any]:
        return {
            "connected": self.device.status.connected,
            "lock_state": self.device.status.lock_state,
            "temperature": self.device.status.temperature
        }


    def get_device_frequencies(self) -> Dict[str, float]:
        return self.device.get_frequencies()
