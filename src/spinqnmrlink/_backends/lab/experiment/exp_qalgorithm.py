# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Quantum Control Experiment Module

Provides Quantum Control experiment functionality
"""

from typing import Dict, Any, List, Optional
import time
import json

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.gate import Gate
from ..utils.circuit import Circuit
from pydantic import ConfigDict, Field

# Create logger
logger = LoggerManager.get_logger(name='exp_qalgorithm')

class ExpQAlgorithmResult(ExperimentResult):
    """Quantum Algorithm Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.matrix = {}
        self.module = []
        self.fidelity = None
        self.gateNums = None
        self.hFre_offset = None
        self.pFre_offset = None
        self.pulseControlTime = None
        self.pureTime = None
        self.purity = None
        self.relaxtion = None
        self.sampleTime = None
        self.smt = None

    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "fidelity": self.fidelity,
            "gateNums": self.gateNums,
            "hFre_offset": self.hFre_offset,
            "pFre_offset": self.pFre_offset,
            "pulseControlTime": self.pulseControlTime,
            "pureTime": self.pureTime,
            "purity": self.purity,
            "relaxtion": self.relaxtion,
            "sampleTime": self.sampleTime,
            "smt": self.smt,
            "matrix": self.matrix,
            "probability": self.module
        }

class ExpQAlgorithmParameters(ExperimentParameter):
    """Quantum Algorithm Experiment Parameters Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    algorithm_type: str = Field(default=ExperimentType.INTRODUCTION_TO_QUANTUM_COMPUTING, description="Algorithm type")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel")
    circuit: Optional[Circuit] = None  # quantum circuit
    grover_bin: int = Field(default=0, ge=0, le=3, description="Grover algorithm binary selection: 0 for 00, 1 for 01, 2 for 10, 3 for 11")
    calcMatrix: bool = Field(default=True, description="Whether to calculate matrix")


    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        if self.circuit is None:
            raise ValueError("circuit must be set before submitting an algorithm experiment")
        if self.algorithm_type not in [ExperimentType.INTRODUCTION_TO_QUANTUM_COMPUTING,
                                    ExperimentType.DEUTSCH_ALGORITHM,
                                    ExperimentType.BERNSTEIN_VARIRANI_ALGORITHM,
                                    ExperimentType.GROVER_ALGORITHM,
                                    ExperimentType.QFT_ALGORITHM,
                                    ExperimentType.HHL_ALGORITHM,
                                    ExperimentType.VQE_ALGORITHM,
                                    ExperimentType.QAOA_ALGORITHM]:
            raise ValueError(f"Invalid algorithm type: {self.algorithm_type}")
        else:
            para = {
                "calcMatrix": self.calcMatrix,
                "circuit": self.circuit.to_dict(),
                "samplePath": self.samplePath
            }
            if self.algorithm_type == ExperimentType.GROVER_ALGORITHM:
                para["grover_bin"] = self.grover_bin
            return para

class ExpQAlgorithm(Experiment):
    """Quantum Algorithm Experiment Class"""

    def __init__(self, parameters: ExpQAlgorithmParameters):
        """
        Initialize Quantum Algorithm experiment

        Args:
            parameters: Quantum Algorithm experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.QUANTUM_ALGORITHM
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpQAlgorithmResult()
        self.step_graph = {}
        self.extra = {}
        self.group_name = "exp_algorithms"
        logger.info(f"Created Quantum Algorithm experiment: {self.name}")

    def get_experiment_parameter(self) -> Dict[str, Any]:
        """Get experiment parameters."""
        para = {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": 0,
            "startTime": 0,
            "state": ExperimentState.PENDING,
            "type": self.parameters.algorithm_type,
            "params": json.dumps(self.parameters.get_parameters()),
            "extra": json.dumps(self.extra)
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
            result = json.loads(parameters["result"])
            evapara = result["evapara"]
            self.result.fidelity = evapara["fidelity"]
            self.result.gateNums = evapara["gateNums"]
            self.result.hFre_offset = evapara["hFre_offset"]
            self.result.pFre_offset = evapara["pFre_offset"]
            self.result.pulseControlTime = evapara["pulseControlTime"]
            self.result.pureTime = evapara["pureTime"]
            self.result.purity = evapara["purity"]
            self.result.relaxtion = evapara["relaxtion"]
            self.result.sampleTime = evapara["sampleTime"]
            self.result.smt = evapara["smt"]
            exeresult = result["exeResult"]
            self.result.matrix = {
                "real": exeresult["real"],
                "imag": exeresult["imag"]
            }
            self.result.module = exeresult["module"]

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
            "type": self.parameters.algorithm_type,
            "extra": json.dumps(self.extra),
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
