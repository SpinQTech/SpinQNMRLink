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
from ..utils.gate import CustomGate
from ..utils.circuit import Circuit
from ...._core.parameter_choices import SampleFrequencyHz
from pydantic import ConfigDict, Field, field_validator

# Create logger
logger = LoggerManager.get_logger(name='exp_layer_circuit')

class ExpLayerCircuitResult(ExperimentResult):
    """Circuit Layer Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.matrix = {}
        self.module = []
        self.coordinate = []
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
            "matrix": self.matrix,
            "probability": self.module,
            "coordinate": self.coordinate,
            "fidelity": self.fidelity,
            "gateNums": self.gateNums,
            "hFre_offset": self.hFre_offset,
            "pFre_offset": self.pFre_offset,
            "pulseControlTime": self.pulseControlTime,
            "pureTime": self.pureTime,
            "purity": self.purity,
            "relaxtion": self.relaxtion,
            "sampleTime": self.sampleTime,
            "smt": self.smt
        }

class ExpLayerCircuitParameters(ExperimentParameter):
    """Circuit Layer Experiment Parameters Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    using_pulse: bool = Field(default=False, description="Whether to use pulse instead of gate")
    circuit: Circuit = None  # quantum circuit
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    gradients: List[Gradient] = Field(default=[], description="Gradient sequence")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel")
    relaxation_delay: float = Field(default=0, ge=0, le=30, description="Relaxation delay (s)")
    h_freShift: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency shift")
    p_freShift: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency shift")
    h_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Hydrogen frequency demo")
    p_freDemo: int = Field(default=0, ge=-1000, le=1000, description="Phosphorus frequency demo")
    sampleFre: SampleFrequencyHz = Field(default=10000, description="Sampling frequency in Hz: choose 10000, 20000, 50000, or 100000")
    sampleCount: int = Field(default=MAX_SAMPLE_COUNT, ge=MIN_SAMPLE_COUNT, le=MAX_SAMPLE_COUNT, description="Sample point")
    sampleDelay: int = Field(default=0, ge=0, le=1000, description="Sample delay(us)")

    @field_validator("sampleCount")
    @classmethod
    def validate_sample_count(cls, value: int) -> int:
        return validate_sample_count(value)






    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        validate_sample_count(self.sampleCount)
        para = {
            "relaxation_time": self.relaxation_delay,
            "samplePath": self.samplePath,
            "h_freShift": self.h_freShift,
            "p_freShift": self.p_freShift,
            "h_freDemo": self.h_freDemo,
            "p_freDemo": self.p_freDemo,
            "sampleFre": self.sampleFre,
            "sampleCount": self.sampleCount,
            "sampleDelay": self.sampleDelay,
            "gradient": self._convert_gradient()
        }
        if self.using_pulse:
            para["pulse"] = self._convert_pulse()
        else:
            para["circuit"] = self.circuit.to_dict()
        return para

class ExpLayerCircuit(Experiment):
    """Circuit Layer Experiment Class"""

    def __init__(self, parameters: ExpLayerCircuitParameters):
        """
        Initialize Circuit Layer experiment

        Args:
            parameters: Circuit Layer experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.CIRCUIT_LAYER_EXPERIMENT
        self._submitted_type = None
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpLayerCircuitResult()
        self.step_graph = {}
        self.extra = {}
        self.group_name = "exp_layer_circuit"
        logger.info(f"Created Circuit Layer experiment: {self.name}")

    def get_experiment_parameter(self) -> Dict[str, Any]:
        """Get experiment parameters."""
        self._submitted_type = self._configured_type()
        para = {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": 0,
            "startTime": 0,
            "state": ExperimentState.PENDING,
            "type": self._submitted_type,
            "params": json.dumps(self.parameters.get_parameters())
        }
        if not self.parameters.using_pulse:
            circuit = self.parameters.circuit.circuit
            for gate in circuit:
                if isinstance(gate, CustomGate):
                    self.extra[gate.customType + ".spinq"] = gate.to_json()

        para["extra"] = json.dumps(self.extra)

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
                exeResult = result["exeResult"]
                if "coordinate" in exeResult:
                    self.result.coordinate = exeResult["coordinate"]
                self.result.matrix = {
                    "real": exeResult["real"],
                    "imag": exeResult["imag"]
                }
                self.result.module = exeResult["module"]
            else:
                self.state = ExperimentState.FAILED

    def get_status(self) -> str:
        """Get experiment status."""
        return self.state

    def _configured_type(self) -> str:
        suffix = "_PULSE" if self.parameters.using_pulse else "_CIRCUIT"
        return ExperimentType.CIRCUIT_LAYER_EXPERIMENT + suffix

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result."""
        return {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": self.completed_at,
            "startTime": self.started_at,
            "state": self.state,
            "type": self._submitted_type or self._configured_type(),
            "extra": json.dumps(self.extra),
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
