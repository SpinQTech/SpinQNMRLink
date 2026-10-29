# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private backend types. No connections are created by importing this module."""
from .utils.types import ExperimentType
from .utils.pulse import Pulse, Gradient
from .utils.gate import Gate
from .utils.circuit import Circuit
from .utils.types import QubitMode, ConnectionState
from .experiment.three_qubit_models import *
from spinqnmrlink._core.waveforms import WaveformGeneratorBase

class WaveformGenerator(WaveformGeneratorBase):
    pulse_type = Pulse
