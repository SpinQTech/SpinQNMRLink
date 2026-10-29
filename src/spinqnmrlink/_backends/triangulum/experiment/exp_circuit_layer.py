# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Quantum Control Circuit Experiment Module

Class definitions for Quantum Control Circuit experiments.
"""

from typing import Dict, Any, Optional
from ..experiment.experiment_base import ExperimentParameter, ExperimentResult
from ..utils.types import ExperimentState
from ..utils import LoggerManager
from ..utils.circuit import Circuit
from pydantic import ConfigDict, Field

# Create logger
logger = LoggerManager.get_logger(name='exp_circuit_layer')

class ExpCircuitLayerResult(ExperimentResult):
    """Circuit Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.fidelity = None
        self.probabilities = []
        self.state_vector = []
        self.qubits_num = 0
        self.coordinate = {}

    def get_result(self) -> Dict[str, Any]:
        """获取实验结果"""
        # 合成最终的实验结果输出
        return {
            "fidelity": self.fidelity,
            "probabilities": self.probabilities,
            "state_vector": self.state_vector,
            "qubits_num": self.qubits_num,
            "coordinate": self.coordinate
        }

class ExpCircuitLayerParameters(ExperimentParameter):
    """Circuit Experiment Parameter Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    circuit: Optional[Circuit] = Field(default=None, description="Circuit")
    qubits_num: int = Field(default=0, ge=0, le=3, description="Qubits number")
    calc_matrix: bool = Field(default=True, strict=True, description="Request density-matrix components")
    def set_circuit(self, circuit: Circuit):
        if not isinstance(circuit, Circuit):
            raise TypeError("circuit must be a spinqnmrlink._backends.triangulum.Circuit instance")
        self.circuit = circuit
        self.qubits_num = circuit.qubits_num

    def get_parameters(self) -> Dict[str, Any]:
        """获取实验参数"""
        if self.circuit is None:
            raise ValueError("circuit is not configured; call set_circuit() before submitting the experiment")
        parameters = {
            "circuit": self.circuit.to_dict(),
            "qubits_num": self.qubits_num,
            "calcMatrix": self.calc_matrix,
        }
        return parameters
