# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private Lab tasks behavior; state is owned by the backend session."""
from ._imports import *  # noqa: F403


class TasksMixin:
    def register_experiment(
        self,
        experiment_type: ExperimentType,
        *,
        qubit_mode: Optional[QubitMode] = None,
        parameters=None,
        task_id: Optional[str] = None,
        name: str = "",
        custom_awg_files=None,
    ):
        """Register a TWO experiment or an Appendix-A THREE experiment.

        TWO parameters can be initialized by the experiment factory.
        THREE registration requires an explicit three-qubit parameter model.
        """
        mode = self._coerce_snapshot_mode(qubit_mode)
        manager = self._experiment_managers_by_mode.setdefault(mode, ExperimentManager())
        handler_map = self._exp_handler_maps_by_mode.setdefault(mode, {})
        if mode is QubitMode.THREE:
            if not isinstance(parameters, THREE_QUBIT_PARAMETER_TYPES):
                raise TypeError(
                    "THREE registration requires a public three-qubit parameter model"
                )
            if experiment_type != parameters.TASK_TYPE:
                raise ValueError(
                    "experiment_type does not match the three-qubit parameter model: "
                    f"expected {parameters.TASK_TYPE}, got {experiment_type}"
                )
            experiment = ThreeQubitExperiment(
                parameters,
                task_id=task_id,
                name=name,
                custom_awg_files=custom_awg_files,
            )
            return manager.register_experiment_instance(
                experiment,
                parameters,
                handler_map,
            )
        if parameters is not None or task_id is not None or name or custom_awg_files is not None:
            raise ValueError(
                "parameters, task_id, name, and custom_awg_files are THREE-only "
                "registration options"
            )
        return manager.register_experiment(experiment_type, handler_map)


    def deregister_experiment(self, qubit_mode: Optional[QubitMode] = None):
        # Resume timeout now that the experiment is done
        self.heartbeat_manager.resume_timeout()
        return self.get_expMgr(qubit_mode).deregister_experiment()


    def get_experiment_status(self, qubit_mode: Optional[QubitMode] = None):
        return self.get_expMgr(qubit_mode).get_experiment_status()


    def get_experiment_result(self, qubit_mode: Optional[QubitMode] = None):
        return self.get_expMgr(qubit_mode).get_experiment_result()


    def run_experiment(self, qubit_mode: Optional[QubitMode] = None) -> int:
        target_mode = self._validate_target_qubit_mode(qubit_mode)
        manager = self._experiment_managers_by_mode.setdefault(
            target_mode, ExperimentManager()
        )
        para = manager.get_experiment_parameter()
        if not para:
            raise RuntimeError("No experiment registered")
        para["deviceId"] = self.device_id
        para["account"] = self.account
        return self.add_task(para, target_mode)


    def terminate_experiment(
        self,
        qubit_mode: Optional[QubitMode] = None,
        timeout: float = 10.0,
    ) -> RequestResponse:
        """Request termination and wait for the protocol acknowledgement response."""
        if not self.is_logged_in:
            raise RuntimeError("Login is required before terminating an experiment")
        manager = self.get_expMgr(qubit_mode)
        if manager.current_experiment is None:
            raise RuntimeError("No experiment registered")
        task_id = manager.current_experiment.id
        return self.terminate_task(
            task_id,
            qubit_mode=qubit_mode,
            timeout=timeout,
            _locally_owned=True,
        )


    def terminate_task(
        self,
        task_id: str,
        qubit_mode: Optional[QubitMode] = None,
        timeout: float = 10.0,
        _locally_owned: bool = False,
    ) -> RequestResponse:
        """Request termination of a task and wait for its acknowledgement."""
        if not self.is_logged_in:
            raise RuntimeError("Login is required before terminating a task")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")
        target_mode = self._validate_target_qubit_mode(qubit_mode)
        # Queue snapshots may omit account.  If the server did include one,
        # reject an explicitly foreign task before sending.
        queued_task = next(
            (
                item
                for item in self._experiment_queues_by_mode.get(target_mode, [])
                if item.get("id") == task_id
            ),
            None,
        )
        if queued_task is not None and queued_task.get("account") not in (None, "", self.account):
            raise PermissionError("Cannot terminate a task owned by another account")
        ownership_confirmed = (
            _locally_owned
            or task_id in self._submitted_task_ids
            or (
                queued_task is not None
                and queued_task.get("account") == self.account
            )
        )
        if not ownership_confirmed:
            raise PermissionError(
                "Cannot verify that the current account created this task"
            )
        envelope_mode = QubitMode.THREE if target_mode is QubitMode.THREE else None
        sequence_id = self._send_message(
            MachineType.MSG_REQ_TERMINATE_EXP_TASK_REQ,
            {"taskId": task_id},
            qubit_mode=envelope_mode,
            expected_response_msg_id=MachineType.MSG_RES_TERMINATE_EXP_TASK_RES,
            target_qubit_mode=target_mode,
            task_id=task_id,
            response_timeout=timeout,
        )
        return self.wait_for_request_response(sequence_id, timeout)


    def wait_for_experiment_completion(
        self,
        qubit_mode: Optional[QubitMode] = None,
    ):
        return self.get_expMgr(qubit_mode).wait_for_experiment_completion()


    def register_experiment_decoder(self, msg_id: str, decoder) -> None:
        """Register an optional decoder applied before experiment handlers."""
        if not msg_id or not callable(decoder):
            raise ValueError("msg_id must be non-empty and decoder must be callable")
        self._experiment_decoders[msg_id] = decoder
