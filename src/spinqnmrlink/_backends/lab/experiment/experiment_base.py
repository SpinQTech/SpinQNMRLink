# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Base experiment-related class definitions.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, ConfigDict
from spinqnmrlink._core.experiment_core import ExperimentResultCore, ExperimentStateCore

from ..utils import LoggerManager
from ..utils.types import MachineType, ExperimentState
logger = LoggerManager.get_logger(name='experiment')

MIN_SAMPLE_COUNT = 1024
MAX_SAMPLE_COUNT = 16384

def validate_sample_count(value: int) -> int:
    """Validate sampling point count shared by NMR sampling experiments."""
    if not MIN_SAMPLE_COUNT <= value <= MAX_SAMPLE_COUNT:
        raise ValueError(
            "Invalid sampleCount: "
            f"sampleCount must be in range {MIN_SAMPLE_COUNT}-{MAX_SAMPLE_COUNT}."
        )
    if value & (value - 1) != 0:
        raise ValueError(
            "Invalid sampleCount: "
            f"sampleCount must be a power of 2 in range {MIN_SAMPLE_COUNT}-{MAX_SAMPLE_COUNT}."
        )
    return value

class ExperimentResult(ExperimentResultCore):
    """Base class for experiment results."""
    pass

class ExperimentParameter(BaseModel):
    """Base class for experiment parameters."""
    model_config = ConfigDict(validate_assignment=True)

    def append_pulse(self, pulse) -> None:
        """Append one pulse for parameter models that expose ``pulses``."""
        self.pulses.append(pulse)

    def _convert_pulse(self) -> Dict[str, Any]:
        """Serialize pulse channels in the common LabLink wire shape."""
        hydrogen, phosphorus = [], []
        for pulse in self.pulses:
            target = hydrogen if pulse.path == 0 else phosphorus
            target.append(pulse.to_dict())
        return {"hPulse": hydrogen, "pPulse": phosphorus}

    def append_gradient(self, gradient) -> None:
        """Append one gradient for models that expose ``gradients``."""
        self.gradients.append(gradient)

    def _convert_gradient(self) -> list:
        return [gradient.to_dict() for gradient in self.gradients]

    def set_circuit(self, circuit) -> None:
        """Assign the native LabLink circuit to a circuit parameter model."""
        self.circuit = circuit

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get experiment parameters.

        This abstract method must be implemented by all experiment subclasses.
        It should return a dictionary containing all experiment parameters
        required for execution.

        Returns:
            Dict[str, Any]: Dictionary containing experiment parameters.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("get_parameters method must be implemented in subclass")

class Experiment(ExperimentStateCore, ABC):
    """Base class for experiments."""
    def __init__(self, parameters: Optional[ExperimentParameter] = None):
        self._initialize_experiment_state(parameters, ExperimentResult)

    def register_handler(self, handler_map: dict) -> None:
        """Register message handlers for this experiment."""
        handler_map[MachineType.MSG_RES_ADD_EXP_TASK_RES] = self.handle_exp_added
        handler_map[MachineType.MSG_POST_EXP_STARTED] = self.handle_exp_started
        handler_map[MachineType.MSG_POST_EXP_TERMINATED] = self.handle_exp_terminated
        handler_map[MachineType.MSG_POST_EXP_REMOVED] = self.handle_exp_removed
        handler_map[MachineType.MSG_POST_EXP_STEP_CHANGED] = self.handle_exp_step_changed
        handler_map[MachineType.MSG_POST_EXP_DATA_UPDATED] = self.handle_exp_data_updated
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED_STARTED] = self.handle_exp_chart_data_updated_started
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED] = self.handle_exp_chart_data_updated
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED_FINISHED] = self.handle_exp_chart_data_updated_finished
        handler_map[MachineType.MSG_POST_EXP_FINISHED] = self.handle_exp_finished

    @abstractmethod
    def get_experiment_parameter(self) -> Dict[str, Any]:
        """
        Get experiment parameters.

        Returns:
            Dict[str, Any]: Experiment parameters.
        """
        raise NotImplementedError("get_experiment_parameter method must be implemented in subclass")

    @abstractmethod
    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """Handle experiment addition."""
        raise NotImplementedError("handle_exp_added method must be implemented in subclass")

    @abstractmethod
    def handle_exp_started(self, data: Dict[str, Any]) -> None:
        """Handle experiment start."""
        raise NotImplementedError("handle_exp_started method must be implemented in subclass")

    @abstractmethod
    def handle_exp_terminated(self, data: Dict[str, Any]) -> None:
        """Handle experiment termination."""
        raise NotImplementedError("handle_exp_terminated method must be implemented in subclass")

    @abstractmethod
    def handle_exp_removed(self, data: Dict[str, Any]) -> None:
        """Handle experiment removal."""
        raise NotImplementedError("handle_exp_removed method must be implemented in subclass")

    @abstractmethod
    def handle_exp_step_changed(self, data: Dict[str, Any]) -> None:
        """Handle experiment step changes."""
        raise NotImplementedError("handle_exp_step_changed method must be implemented in subclass")

    @abstractmethod
    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """Handle experiment data updates."""
        raise NotImplementedError("handle_exp_data_updated method must be implemented in subclass")

    @abstractmethod
    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """Handle start of experiment chart data updates."""
        raise NotImplementedError("handle_exp_chart_data_updated_started method must be implemented in subclass")

    @abstractmethod
    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """Handle experiment chart data updates."""
        raise NotImplementedError("handle_exp_chart_data_updated method must be implemented in subclass")

    @abstractmethod
    def handle_exp_chart_data_updated_finished(self) -> None:
        """Handle completion of experiment chart data updates."""
        raise NotImplementedError("handle_exp_chart_data_updated_finished method must be implemented in subclass")

    @abstractmethod
    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """Handle experiment completion."""
        raise NotImplementedError("handle_exp_finished method must be implemented in subclass")

    def get_status(self) -> str:
        """Get experiment status."""
        raise NotImplementedError("get_status method must be implemented in subclass")

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result."""
        raise NotImplementedError("get_result method must be implemented in subclass")
