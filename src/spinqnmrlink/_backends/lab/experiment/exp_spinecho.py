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
import math

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState, MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT, validate_sample_count
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse
from ...._core.parameter_choices import SampleFrequencyHz
from pydantic import Field, field_validator
# Create logger
logger = LoggerManager.get_logger(name='exp_spinecho')


def validate_spinecho_sample_count(value: int) -> int:
    """Accept the tablet workflow's 16000 samples plus legacy power-of-two sizes."""
    if value == 16000:
        return value
    return validate_sample_count(value)

class ExpSpinechoResult(ExperimentResult):
    """Spinecho Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.phase = None
        self.coordinate = {}

    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "phase": self.phase,
            "coordinate": self.coordinate
        }

class ExpSpinechoParameters(ExperimentParameter):
    """Spinecho Experiment Parameters Class"""
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    samplePath: int = Field(default=0, ge=0, le=0, description="Sampling path selection: 0 for hydrogen channel")
    sampleFre: SampleFrequencyHz = Field(default=10000, description="Sampling frequency in Hz: choose 10000, 20000, 50000, or 100000")
    sampleCount: int = Field(default=16000, ge=MIN_SAMPLE_COUNT, le=MAX_SAMPLE_COUNT, description="Sample count")
    sampleDelay: int = Field(default=0, ge=0, le=2000000, description="Sample delay(us)")
    h_freShift: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency shift")
    h_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency demo")

    @field_validator("sampleCount")
    @classmethod
    def validate_sample_count(cls, value: int) -> int:
        return validate_spinecho_sample_count(value)



    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        validate_spinecho_sample_count(self.sampleCount)
        return {
            "sampleCount": self.sampleCount,
            "sampleFre": self.sampleFre,
            "sampleDelay": self.sampleDelay,
            "h_freShift": self.h_freShift,
            "h_freDemo": self.h_freDemo,
            "pulse": self._convert_pulse(),
            "samplePath": self.samplePath
        }

class ExpSpinecho(Experiment):
    """Spinecho Experiment Class"""

    def __init__(self, parameters: ExpSpinechoParameters):
        """
        Initialize Spinecho experiment

        Args:
            parameters: Spinecho experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.SPIN_ECHO
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpSpinechoResult()
        self.step_graph = {}
        self.group_name = "exp_spinecho"

        logger.info(f"Created Spinecho experiment:{self.name}")

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
            "extra": "1",
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
                self.result.coordinate = result
                x = result["x"]
                y = result["y"]

                if x == 0 and y == 0:
                    self.result.phase = 0
                else:
                    # Report the geometric phase of the returned coordinate.
                    # Do not apply an undocumented 180-degree offset: the
                    # complete workflow compares this value with the prepared
                    # initial phase and the refocusing-pulse axis.
                    phase = math.degrees(math.atan2(y, x))
                    while(phase < 0):
                        phase += 360
                    while(phase >= 360):
                        phase -= 360
                    self.result.phase = phase
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
            "extra": "1",
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
