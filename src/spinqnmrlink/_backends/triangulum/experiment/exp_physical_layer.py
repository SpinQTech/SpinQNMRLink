# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Quantum Control Experiment Module

Provides Quantum Control experiment functionality
"""

import time
import json

from typing import Dict, Any, Optional, List
from ..experiment.experiment_base import ExperimentParameter, ExperimentResult
from ..utils.types import ExperimentType, ExperimentState
from ..utils import LoggerManager
from ..utils.pulse import Pulse
from ...._core.parameter_choices import SampleFrequencyHz
from pydantic import ConfigDict, Field

# Create logger
logger = LoggerManager.get_logger(name='exp_layer_physical')

class ExpPhysicalLayerResult(ExperimentResult):
    """Physical Layer Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.type_setting = 0
        self.pauli_basis = {}
        self.probability = []
        self.state_vector = []
        self.graph = []

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        if self.type_setting == 0:
            return {
                "graph": self.graph,
            }
        elif self.type_setting == 1:
            return {
                "pauli_basis": self.pauli_basis,
                "graph": self.graph
            }
        elif self.type_setting == 2:
            return {
                "pauli_basis": self.pauli_basis,
                "probability": self.probability,
                "state_vector": self.state_vector,
                "graph": self.graph
            }

class ExpPhysicalLayerParameters(ExperimentParameter):
    """Physical Layer Experiment Parameters Class"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    sampleQubit: List[int] = Field(default=[], description="Sampling qubit indices")
    type_setting: int = Field(default=0, ge=0, le=2, description="Type setting: 0 for Customized Measurement, 1 for Pauli Component Measurement, 2 for Quantum State Tomography")
    relaxation_delay: float = Field(default=0, ge=0, le=25000000, description="Relaxation delay (µs)")
    stepList: List[int] = Field(default=[], description="Step list")
    freShift: int = Field(default=0, ge=-1000, le=1000, description="Frequency shift")
    freDemo: int = Field(default=0, ge=-1000, le=1000, description="Frequency demo")
    state_initialization: bool = Field(default=False, description="State initialization: True for state initialization, False for not state initialization")
    sampleFre: SampleFrequencyHz = Field(default=10000, description="Sampling frequency in Hz: choose 10000, 20000, 50000, or 100000")
    sampleCount: int = Field(default=16000, ge=1, le=16000, description="Sample point")
    sampleDelay: int = Field(default=0, ge=0, le=2000000, description="Sample delay(us)")

    def append_pulse(self, pulse: Pulse):
        self.pulses.append(pulse)

    def _convert_pulse(self) -> Dict[str, Any]:
        """Convert pulse to dictionary"""
        hpulse = []
        for pulse in self.pulses:
            hpulse.append(pulse.to_dict())
        return {"hPulse": hpulse}

    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        para = {
            "pulse": self._convert_pulse(),
            "parameters": {
                "compute_type": self.type_setting,
                "relaxation_time": self.relaxation_delay,
                "sampleQubit": self.sampleQubit,
                "stepList": self.stepList,
                "freShift": self.freShift,
                "freDemo": self.freDemo,
                "makePps": self.state_initialization,
                "sampleFre": self.sampleFre,
                "sampleCount": self.sampleCount,
                "sampleDelay": self.sampleDelay
            }
        }
        return para
