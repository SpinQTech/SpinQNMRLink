# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private backend types. No connections are created by importing this module."""

from spinqnmrlink._core.waveforms import WaveformGeneratorBase

from .utils.circuit import Circuit
from .utils.gate import Gate
from .utils.pulse import Gradient, Pulse
from .utils.types import ExperimentType


class WaveformGenerator(WaveformGeneratorBase):
    pulse_type = Pulse


__all__ = ["ExperimentType", "Pulse", "Gradient", "Gate", "Circuit", "WaveformGenerator"]
