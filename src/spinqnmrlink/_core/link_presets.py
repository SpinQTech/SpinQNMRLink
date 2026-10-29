# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Triangulum reference parameters, serialized by the original protocol models."""
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class LinkPreset:
    key: str
    build_parameters: Callable[[], Any]

def _physical():
    from spinqnmrlink._backends.triangulum.experiment.exp_physical_layer import ExpPhysicalLayerParameters
    from spinqnmrlink._backends.triangulum.utils.pulse import Pulse
    return ExpPhysicalLayerParameters(pulses=[Pulse(path=0, amplitude=100, phase=90, width=40)],
        relaxation_delay=20, sampleFre=20000, sampleCount=16000)

def _circuit():
    from spinqnmrlink._backends.triangulum.experiment.exp_circuit_layer import ExpCircuitLayerParameters
    from spinqnmrlink._backends.triangulum.utils.circuit import Circuit
    from spinqnmrlink._backends.triangulum.utils.gate import Gate
    circuit = Circuit(3)
    for index in range(3):
        circuit << Gate(type="X", qubitIndex=index)
    parameters = ExpCircuitLayerParameters()
    parameters.set_circuit(circuit)
    return parameters

LINK_PRESETS = (LinkPreset("link.physical", _physical), LinkPreset("link.circuit", _circuit))

def get_link_preset(key):
    for preset in LINK_PRESETS:
        if preset.key == key:
            return preset
    raise KeyError(key)
