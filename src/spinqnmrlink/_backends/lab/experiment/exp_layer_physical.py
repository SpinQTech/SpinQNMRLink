# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Quantum Control Experiment Module

Provides Quantum Control experiment functionality
"""

from typing import Dict, Any, List
import time
import json

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState, MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT, validate_sample_count
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse, Gradient
from ...._core.parameter_choices import SampleFrequencyHz
from pydantic import ConfigDict, Field, field_validator

# Create logger
logger = LoggerManager.get_logger(name='exp_layer_physical')

PAULI_COMPONENT_MEASURE = 1
VALID_PAULI_MEASUREMENT_STEPS = set(range(1, 7))

class ExpLayerPhysicalResult(ExperimentResult):
    """Physical Layer Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.type_setting = 0
        self.graph = []
        self.pauli_matrix = {}
        self.matrix = {}
        self.probability = []

    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        para = {
            "graph": self.graph
        }
        if self.type_setting == 0:
            pass
        elif self.type_setting == 1:
            para["pauli_matrix"] = self.pauli_matrix
        elif self.type_setting == 2:
            para["matrix"] = self.matrix
            para["probability"] = self.probability
        return para

class ExpLayerPhysicalParameters(ExperimentParameter):
    """Physical Layer Experiment Parameters Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    gradients: List[Gradient] = Field(default=[], description="Gradient sequence")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel")
    type_setting: int = Field(default=0, ge=0, le=2, description="Type setting: 0 for Customized Measurement, 1 for Pauli Component Measurement, 2 for Quantum State Tomography")
    relaxation_delay: float = Field(default=0, ge=0, le=30, description="Relaxation delay (s)")
    stepList: List[int] = Field(default=[], description="Step list")
    h_freShift: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency shift")
    p_freShift: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency shift")
    h_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency demo")
    p_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency demo")
    state_initialization: bool = Field(default=True, description="State initialization: True for state initialization, False for not state initialization")
    sampleFre: SampleFrequencyHz = Field(default=10000, description="Sampling frequency in Hz: choose 10000, 20000, 50000, or 100000")
    sampleCount: int = Field(default=16384, ge=MIN_SAMPLE_COUNT, le=MAX_SAMPLE_COUNT, description="Sample point")
    sampleDelay: int = Field(default=0, ge=0, le=2000000, description="Sample delay(us)")

    @field_validator("sampleCount")
    @classmethod
    def validate_sample_count(cls, value: int) -> int:
        return validate_sample_count(value)





    def _validate_parameters(self) -> None:
        validate_sample_count(self.sampleCount)

        if self.type_setting != PAULI_COMPONENT_MEASURE:
            return

        if not self.stepList:
            raise ValueError(
                "Invalid stepList for Pauli component measurement: "
                "stepList must be a non-empty list containing measurement steps 1-6."
            )

        invalid_steps = [step for step in self.stepList if step not in VALID_PAULI_MEASUREMENT_STEPS]
        if invalid_steps:
            raise ValueError(
                "Invalid stepList for Pauli component measurement: "
                f"illegal measurement steps {invalid_steps}; valid steps are 1-6."
            )

    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        self._validate_parameters()

        para = {
            "compute_type": self.type_setting,
            "relaxation_time": self.relaxation_delay,
            "stepList": self.stepList,
            "samplePath": self.samplePath,
            "h_freShift": self.h_freShift,
            "p_freShift": self.p_freShift,
            "h_freDemo": self.h_freDemo,
            "p_freDemo": self.p_freDemo,
            "makePps": self.state_initialization,
            "sampleFre": self.sampleFre,
            "sampleCount": self.sampleCount,
            "sampleDelay": self.sampleDelay,
            "pulse": self._convert_pulse(),
            "gradient": self._convert_gradient()
        }
        if self.type_setting == 1:
            para["makePps"] = True
        elif self.type_setting == 2:
            para["makePps"] = True

        return para

class ExpLayerPhysical(Experiment):
    """Physical Layer Experiment Class"""

    def __init__(self, parameters: ExpLayerPhysicalParameters):
        """
        Initialize Physical Layer experiment

        Args:
            parameters: Physical Layer experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.PHYSICAL_LAYER_EXPERIMENT
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpLayerPhysicalResult()
        self.step_graph = {}
        self.extra = {}
        self.group_name = "exp_layer_physical"
        logger.info(f"Created Physical Layer experiment: {self.name}")

    def get_experiment_parameter(self) -> Dict[str, Any]:
        """Get experiment parameters."""
        para = {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": 0,
            "startTime": 0,
            "state": ExperimentState.PENDING,
            "type": self.experiment_type,
            "params": json.dumps(self.parameters.get_parameters())
        }

        return para

    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """Handle experiment addition for this concrete experiment type."""
        if data["code"] == 0:
            self.id = data["taskId"]
            self.created_at = int(time.time() * 1000)
        else:
            raise Exception(f"Experiment addition failed: {data}")

    def handle_exp_started(self, data: Dict[str, Any]) -> None:
        """Handle experiment start for this concrete experiment type."""
        if data["taskId"] == self.id:
            queue = data["queue"][0]
            self.started_at = queue["startTime"]
            self.name = queue["name"]
            self.state = ExperimentState.RUNNING

    def handle_exp_step_changed(self, data: Dict[str, Any]) -> None:
        """Handle experiment step changes for this concrete experiment type."""
        if data["taskId"] == self.id:
            self.step = data["data"]["step"]

    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """Handle experiment data updates for this concrete experiment type."""
        if data["taskId"] == self.id:
            logger.debug("Experiment data updated")
    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """Handle start of experiment chart data updates for this concrete experiment type."""
        if data["taskId"] == self.id:
            if data["group"] != self.group_name:
                return

            self.step_lines = {}

    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """Handle experiment chart data updates for this concrete experiment type."""
        if data["taskId"] == self.id:
            if data["group"] != self.group_name:
                return
            self.step_lines[data["chart_name"]] = data["points"]

    def handle_exp_chart_data_updated_finished(self, data: Dict[str, Any]) -> None:
        """Handle completion of experiment chart data updates for this concrete experiment type."""
        if data["taskId"] == self.id:
            if data["group"] != self.group_name:
                return
            self.result.append_graph(self.step_lines)

    def handle_exp_terminated(self, data: Dict[str, Any]) -> None:
        """Handle experiment termination for this concrete experiment type."""
        if data.get("taskId") == self.id:
            self.completed_at = int(time.time() * 1000)
            self.state = ExperimentState.FAILED

    def handle_exp_removed(self, data: Dict[str, Any]) -> None:
        """Handle experiment removal for this concrete experiment type."""
        if data.get("taskId") == self.id:
            self.completed_at = int(time.time() * 1000)
            self.state = ExperimentState.FAILED

    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """Handle experiment completion for this concrete experiment type."""
        logger.info(f"Experiment finished:{self.name}")
        logger.debug("Experiment finished data received")
        if data["taskId"] == self.id:
            self.completed_at = int(time.time() * 1000)
            if data["data"]["isTerminated"] == False:
                self.state = ExperimentState.COMPLETED
            else:
                self.state = ExperimentState.FAILED
            parameters = data["data"]["parameters"]
            type = self.parameters.type_setting
            self.result.type_setting = type
            if "result" in parameters and parameters["result"] != "":
                if type == 0:
                    #don't need to do anything
                    pass
                elif type == 1:
                    result = json.loads(parameters["result"])
                    self.result.pauli_matrix = result
                elif type == 2:
                    result = json.loads(parameters["result"])
                    self.result.matrix = {
                        "real": result["real"],
                        "imag": result["imag"]
                    }
                    self.result.probability = result["module"]

    def get_status(self) -> str:
        """Get experiment status."""
        return self.state

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result."""
        return {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": self.completed_at,
            "startTime": self.started_at,
            "state": self.state,
            "type": self.experiment_type,
            "extra": json.dumps(self.extra),
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
