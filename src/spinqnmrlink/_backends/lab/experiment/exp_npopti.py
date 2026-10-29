# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
NMR Experiment Module

Provides Nuclear Magnetic Resonance experiment functionality
"""

from typing import Dict, Any, List
import time
import json

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState, MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT, validate_sample_count
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse
from ...._core.parameter_choices import SampleFrequencyHz
from pydantic import Field, field_validator
# Create logger
logger = LoggerManager.get_logger(name='exp_npopti')

class ExpNpoptiResult(ExperimentResult):
    """Npopti Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.matrix = {}
        self.module = []
        self.coordinate = {}

    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "matrix": self.matrix,
            "probability": self.module,
            "coordinate": self.coordinate
        }

class ExpNpoptiParameters(ExperimentParameter):
    """Npopti Experiment Parameters Class"""
    calibrate_sample: int = Field(default=0, ge=0, le=1, description="Calibrate sample type: 0 for CH₃PO(CH₂CH₃)₂, 1 for H₂O")
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: 0 for hydrogen channel, 1 for phosphorus channel, -1 for both channels")
    sampleFre: SampleFrequencyHz = Field(default=10000, description="Sampling frequency in Hz: choose 10000, 20000, 50000, or 100000")
    sampleCount: int = Field(default=MAX_SAMPLE_COUNT, ge=MIN_SAMPLE_COUNT, le=MAX_SAMPLE_COUNT, description="Sample count")
    sampleDelay: int = Field(default=0, ge=0, le=2000000, description="Sample delay(us)")
    h_freShift: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency shift")
    p_freShift: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency shift")
    h_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency demo")
    p_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency demo")

    @field_validator("sampleCount")
    @classmethod
    def validate_sample_count(cls, value: int) -> int:
        return validate_sample_count(value)



    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        validate_sample_count(self.sampleCount)
        return {
            "sampleCount": self.sampleCount,
            "sampleFre": self.sampleFre,
            "sampleDelay": self.sampleDelay,
            "h_freShift": self.h_freShift,
            "p_freShift": self.p_freShift,
            "h_freDemo": self.h_freDemo,
            "p_freDemo": self.p_freDemo,
            "pulse": self._convert_pulse(),
            "samplePath": self.samplePath
        }

class ExpNpopti(Experiment):
    """Npopti Experiment Class"""

    def __init__(self, parameters: ExpNpoptiParameters):
        """
        Initialize Npopti experiment

        Args:
            parameters: Npopti experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.NUMERICAL_OPTIMIZATION_PULSE
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpNpoptiResult()
        self.step_graph = {}
        self.group_name = "exp_npopti"
        logger.info(f"Created Npopti experiment:{self.name}")

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
            "extra": "0" if self.parameters.calibrate_sample == 0 else "1",
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
                parameters = data["data"]["parameters"]
                result = json.loads(parameters["result"])
                real = result.get("real")
                imag = result.get("imag")
                if real is not None and imag is not None:
                    self.result.matrix = {"real": real, "imag": imag}
                self.result.module = result.get("module", [])
                self.result.coordinate = result.get("coordinate", {})
                required = (
                    ("coordinate",)
                    if self.parameters.calibrate_sample == 1
                    else ("real", "imag", "module")
                )
                missing = [key for key in required if key not in result]
                if missing:
                    logger.warning(
                        "Numerical-pulse result is incomplete; missing=%s, returned_keys=%s",
                        missing,
                        sorted(result.keys()),
                    )
            else:
                self.state = ExperimentState.FAILED

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
            "extra": "0" if self.parameters.calibrate_sample == 0 else "1",
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
