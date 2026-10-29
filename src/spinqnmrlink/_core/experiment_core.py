# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Shared state and manager behavior for the two experiment protocols."""

import time
import uuid
from typing import Any, Dict


class ExperimentResultCore:
    """Common result interface retained by both public result base classes."""

    def append_graph(self, lines: Dict[str, Any]):
        raise NotImplementedError("append_graph method must be implemented in subclass")

    def get_result(self) -> Dict[str, Any]:
        raise NotImplementedError("get_result method must be implemented in subclass")


class ExperimentStateCore:
    """Initialize fields with identical meaning in both experiment families."""

    def _initialize_experiment_state(self, parameters, result_factory):
        self.experiment_type = ""
        self.id = str(uuid.uuid4())
        self.name = ""
        self.step = ""
        self.state = "PENDING"
        self.created_at = int(time.time() * 1000)
        self.started_at = None
        self.completed_at = None
        self.parameters = parameters
        self.graph_data = []
        self.result = result_factory()


class ExperimentManagerCore:
    """Protocol-neutral access, waiting and result retrieval behavior."""

    terminal_states = frozenset()
    logger = None

    def get_experiment_parameter(self):
        if self.current_experiment is None:
            self.logger.error("No experiment registered")
            return {}
        return self.current_experiment.get_experiment_parameter()

    def wait_for_experiment_completion(self, timeout=300.0):
        if self.current_experiment is None:
            self.logger.error(
                "No experiment registered or experiment was deregistered due to errors"
            )
            return False
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        deadline = time.monotonic() + timeout
        try:
            while True:
                if self.current_experiment is None:
                    self.logger.error("Experiment was deregistered during execution")
                    return False
                if self.current_experiment.get_status() in self.terminal_states:
                    return True
                if time.monotonic() >= deadline:
                    return False
                time.sleep(min(0.1, max(0, deadline - time.monotonic())))
        except Exception as exc:
            self.logger.error("Error waiting for experiment completion: {}".format(exc))
            self.deregister_experiment()
            return False

    def get_experiment_result(self):
        if self.current_experiment is None:
            self.logger.error(
                "No experiment registered or experiment was deregistered due to errors"
            )
            return {}
        if self.current_experiment.get_status() not in self.terminal_states:
            raise RuntimeError("Read results only after a known terminal experiment state")
        return self.current_experiment.get_result()
