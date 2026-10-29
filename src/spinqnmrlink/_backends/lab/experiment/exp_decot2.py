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

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse
from pydantic import Field

# Create logger
logger = LoggerManager.get_logger(name='exp_decot2')

class ExpT2Result(ExperimentResult):
    """T2 Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.width = None
        self.mod = None
        self.coordinate = {}
        self.matrix = {}
        self.module = []

    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "width": self.width,
            "mod": self.mod,
            "coordinate": self.coordinate,
            "matrix": self.matrix,
            "probability": self.module
        }

class ExpT2Parameters(ExperimentParameter):
    """T2 Experiment Parameters Class"""
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    freq_h: float = Field(default=27.0, gt=0, lt=100, description="Hydrogen resonance frequency (MHz)")
    freq_p: float = Field(default=11.0, gt=0, lt=100, description="Phosphorus resonance frequency (MHz)")
    makePps: bool = Field(default=False, description="Whether to generate PPS signal")
    samplePath: int = Field(default=0, ge=0, le=1, description="Sampling path selection: 0 for hydrogen channel, 1 for phosphorus channel")
    custom_freq: bool = Field(default=False, description="Whether to use custom frequency(h_freq or p_freq)")



    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "custom_freq": self.custom_freq,
            "freq_h": self.freq_h * 1000000,
            "freq_p": self.freq_p * 1000000,
            "repeat": 0,
            "makePps": self.makePps,
            "pulse": self._convert_pulse(),
            "samplePath": self.samplePath,
            "sampleQubit": 0,
            "usingAwgFile": False
        }

class ExpT2(Experiment):
    """T2 Experiment Class"""

    def __init__(self, parameters: ExpT2Parameters):
        """
        Initialize T2 experiment

        Args:
            parameters: T2 experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.QUANTUM_DECOHERENCE_T2
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpT2Result()
        self.step_graph = {}
        self.group_name = "exp_t2"
        logger.info(f"Created T2 experiment: {self.name}")

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
            "extra": "",
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
            self.result.width = data["data"]["exp_t2"]["width"]
            self.result.mod = data["data"]["exp_t2"]["mod"]

    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """Handle start of experiment chart data updates for this concrete experiment type."""
        if data["taskId"] == self.id:
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
        if data["taskId"] == self.id:
            self.completed_at = int(time.time() * 1000)
            if data["data"]["isTerminated"] == False:
                self.state = ExperimentState.COMPLETED
            else:
                self.state = ExperimentState.FAILED
            result = json.loads(data["data"]["parameters"]["result"])
            self.result.coordinate = result["coordinate"]
            self.result.matrix = {
                "real": result["real"],
                "imag": result["imag"]
            }
            self.result.module = result["module"]

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
            "extra": "",
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
