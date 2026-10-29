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

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState
from ..utils import LoggerManager
from ..utils.types import ExperimentType

from ..utils.gate import CustomGate
from ..utils.circuit import Circuit
from pydantic import ConfigDict, Field

# Create logger
logger = LoggerManager.get_logger(name='exp_qtask')

class ExpQTaskResult(ExperimentResult):
    """Quantum Task Experiment Result Class"""
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

class ExpQTaskParameters(ExperimentParameter):
    """Quantum Task Experiment Parameters Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    freq_h: float = Field(default=27.0, gt=0, lt=100, description="Hydrogen resonance frequency (MHz)")
    freq_p: float = Field(default=11.0, gt=0, lt=100, description="Phosphorus resonance frequency (MHz)")
    custom_freq: bool = Field(default=False, description="Whether to use custom frequency(h_freq or p_freq)")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel")
    circuit: Circuit = None  # quantum circuit
    using_custom_gate: bool = Field(default=False, description="Whether to use custom gate")
    using_custom_pps: bool = Field(default=False, description="Whether to use custom pps file")
    pps_json: str = Field(default="", description="Custom pps file json")
    pps_repeat: int = Field(default=0, ge=0, description="Custom pps repeat times")
    Hlamda: float = Field(default=0.0, description="Hlamda,which is from exp_system_initialization")
    Plamda: float = Field(default=0.0, description="Plamda,which is from exp_system_initialization")
    def _validate_pps_json(self) -> bool:
        if self.pps_json == "":
            logger.warning("using custom pps but pps_json is empty!")
            return False
        try:
            pulse_dict = json.loads(self.pps_json)
            if "pulse" in pulse_dict:
                if "channel1_pulse" in pulse_dict["pulse"] and "channel2_pulse" in pulse_dict["pulse"]:
                    ch1_pulse = pulse_dict["pulse"]["channel1_pulse"]
                    ch2_pulse = pulse_dict["pulse"]["channel2_pulse"]
                    for i,p in enumerate(ch1_pulse):
                        for key in p:
                            if key not in ["width", "amplitude", "phase", "detuning"]:
                                logger.warning(f"Invalid pps_json at channel1_pulse[{i}], \"{key}\" is not in the channel1_pulse")
                                return False

                            if p["width"] < 0 or p["width"] > 20000000:
                                logger.warning(f"Invalid pps_json at channel1_pulse[{i}], width must be between 0 and 20000000, but got {p['width']}")
                                return False
                            if p["amplitude"] < 0 or p["amplitude"] > 100:
                                logger.warning(f"Invalid pps_json at channel1_pulse[{i}], amplitude must be between 0 and 100, but got {p['amplitude']}")
                                return False
                            if p["detuning"] < -10000 or p["detuning"] > 10000:
                                logger.warning(f"Invalid pps_json at channel1_pulse[{i}], detuning must be between -10000 and 10000, but got {p['detuning']}")
                                return False
                    for i,p in enumerate(ch2_pulse):
                        for key in p:
                            if key not in ["width", "amplitude", "phase", "detuning"]:
                                logger.warning(f"Invalid pps_json at channel2_pulse[{i}], {key} is not in the channel2_pulse")
                                return False

                            if p["width"] < 0 or p["width"] > 20000000:
                                logger.warning(f"Invalid pps_json at channel2_pulse[{i}], width must be between 0 and 20000000, but got {p['width']}")
                                return False
                            if p["amplitude"] < 0 or p["amplitude"] > 100:
                                logger.warning(f"Invalid pps_json at channel2_pulse[{i}], amplitude must be between 0 and 100, but got {p['amplitude']}")
                                return False
                            if p["detuning"] < -10000 or p["detuning"] > 10000:
                                logger.warning(f"Invalid pps_json at channel2_pulse[{i}], detuning must be between -10000 and 10000, but got {p['detuning']}")
                                return False

                    if len(ch1_pulse) != len(ch2_pulse):
                        logger.warning("Invalid pps_json, channel1_pulse and channel2_pulse must have the same length")
                        return False
                    return True
                else:
                    logger.warning("Invalid pps_json, pulse dictionary must be in the pps_json")
                    return False
            else:
                logger.warning("Invalid pps_json, pulse dictionary must be in the pps_json")
                return False
        except json.JSONDecodeError:
            logger.warning("pps_json is not a valid json!")
            return False


    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        para = {
            "custom_freq": self.custom_freq,
            "freq_h": self.freq_h * 1000000,
            "freq_p": self.freq_p * 1000000,
            "repeat": self.pps_repeat,
            "samplePath": self.samplePath
        }
        if self.using_custom_pps:
            if not self._validate_pps_json():
                raise ValueError("Invalid pps_json, please check the pps_json and try again")
            para["ppsFile"] = "customized_pps.spinq"

        para["circuit"] = self.circuit.to_dict()
        return para

class ExpQTask(Experiment):
    """Quantum Task Experiment Class"""

    def __init__(self, parameters: ExpQTaskParameters):
        """
        Initialize Quantum Task experiment

        Args:
            parameters: Quantum Task experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.QUANTUM_COMPUTING_TASK
        self.name = "ComputingTask" + "-" + self.id[:8]
        self.result = ExpQTaskResult()
        self.step_graph = {}
        self.extra = {}
        self.group_name = "exp_qalgorithm"
        logger.info(f"Created Quantum Computing Task experiment: {self.name}")

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
        if self.parameters.using_custom_gate:
            circuit = self.parameters.circuit.circuit
            for gate in circuit:
                if isinstance(gate, CustomGate):
                    self.extra[gate.customType + ".spinq"] = gate.to_json()
        if self.parameters.using_custom_pps:
            self.extra["customized_pps.spinq"] = self.parameters.pps_json

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
            "type": self.experiment_type,
            "extra": json.dumps(self.extra),
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
