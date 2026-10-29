# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Protocol-valid LabLink THREE-mode reference configurations."""

from dataclasses import dataclass
from typing import Any, Callable, Tuple


@dataclass(frozen=True)
class LabThreePreset:
    key: str
    title: str
    purpose: str
    experiment_type: str
    build_parameters: Callable[[], Any]


def _pulse_sequence():
    from spinqnmrlink._backends.lab import (
        ThreeQubitGradient,
        ThreeQubitPulse,
        ThreeQubitPulseSequence,
    )
    return ThreeQubitPulseSequence(
        h_pulse=[ThreeQubitPulse(phase=0, am=100, width=200, freshift=0)],
        gradient=[ThreeQubitGradient(value=0, delay=0, path=1)],
    )


def _circuit():
    from spinqnmrlink._backends.lab import ThreeQubitCircuitItem
    return [
        ThreeQubitCircuitItem(type="H", qubit_index=0, timeslot=0),
        ThreeQubitCircuitItem(
            type="CCNOT", qubit_index=2, control_qubit=0,
            control_qubit2=1, timeslot=1,
        ),
    ]


def _physical_custom():
    from spinqnmrlink._backends.lab import ThreeQubitPhysicalCustomParameters
    return ThreeQubitPhysicalCustomParameters(
        fre_demo=0, fre_shift=0, pulse=_pulse_sequence(), calc_matrix=True,
        relaxation_time=15, sample_count=16000, sample_delay=0,
        sample_fre=50000, sample_qubit=[1, 2, 3], make_pps=True,
    )


def _physical_pauli():
    from spinqnmrlink._backends.lab import ThreeQubitPhysicalPauliParameters
    return ThreeQubitPhysicalPauliParameters(
        fre_demo=0, fre_shift=0, pulse=_pulse_sequence(), calc_matrix=True,
        relaxation_time=15, step_list=[1, 2, 4, 7, 8, 9, 10],
        sample_path=-1, make_pps=True,
    )


def _physical_tomography():
    from spinqnmrlink._backends.lab import ThreeQubitPhysicalTomographyParameters
    return ThreeQubitPhysicalTomographyParameters(
        fre_demo=0, fre_shift=0, pulse=_pulse_sequence(), calc_matrix=True,
        relaxation_time=15, sample_qubit=[1, 2, 3], make_pps=True,
    )


def _circuit_pulse():
    from spinqnmrlink._backends.lab import ThreeQubitCircuitPulseParameters
    return ThreeQubitCircuitPulseParameters(
        pulse=_pulse_sequence(), calc_matrix=True, sample_path=0,
        sample_qubit=[1, 2, 3], repeat=0,
    )


def _circuit_parameters():
    from spinqnmrlink._backends.lab import ThreeQubitCircuitParameters
    return ThreeQubitCircuitParameters(
        circuit=_circuit(), relaxation_time=15, calc_matrix=True,
        sample_path=0, sample_qubit=[1, 2, 3], repeat=0,
    )


def _mixing_parameters():
    from spinqnmrlink._backends.lab import ThreeQubitMixingCircuitParameters
    return ThreeQubitMixingCircuitParameters(
        circuit=_circuit(), sample_path=0, sample_qubit=[1, 2, 3], repeat=0,
    )


LAB_THREE_PRESETS: Tuple[LabThreePreset, ...] = (
    LabThreePreset("lab3.physical_custom", "三比特物理层自定义测量", "按指定通道采集三比特脉冲响应。", "EXP_LAYER_PHYSICAL", _physical_custom),
    LabThreePreset("lab3.physical_pauli", "三比特 Pauli 分量测量", "执行协议定义的 Pauli 测量步骤。", "EXP_LAYER_PHYSICAL", _physical_pauli),
    LabThreePreset("lab3.tomography", "三比特量子态层析", "采集三比特量子态重建数据。", "EXP_LAYER_PHYSICAL", _physical_tomography),
    LabThreePreset("lab3.circuit_pulse", "三比特线路层测试脉冲", "在线路层运行三比特测试脉冲。", "EXP_LAYER_CIRCUIT_PULSE", _circuit_pulse),
    LabThreePreset("lab3.circuit", "三比特量子线路", "运行 H 与 CCNOT 组成的参考线路。", "EXP_LAYER_CIRCUIT_CIRCUIT", _circuit_parameters),
    LabThreePreset("lab3.hybrid_circuit", "三比特混合线路", "运行协议定义的经典—量子混合线路。", "EXP_MIXING_CIRCUIT", _mixing_parameters),
)


def get_lab_three_preset(key: str) -> LabThreePreset:
    for preset in LAB_THREE_PRESETS:
        if preset.key == key:
            return preset
    raise KeyError(f"unknown LabLink THREE preset: {key}")
