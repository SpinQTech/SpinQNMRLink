# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Reviewed LabLink TWO-mode reference configurations.

These presets centralize the values previously repeated across examples and
interoperability tools.  They configure native parameter models and therefore
preserve the LabLink wire format exactly.
"""

from dataclasses import dataclass
from typing import Callable, Tuple


@dataclass(frozen=True)
class LabTwoPreset:
    key: str
    title: str
    purpose: str
    experiment_type: str
    configure: Callable[[object], None]


def _types():
    from spinqnmrlink._backends.lab import Circuit, Gate, Gradient, Pulse, WaveformGenerator
    return Circuit, Gate, Gradient, Pulse, WaveformGenerator


def _pulse(path=0, width=40, phase=90):
    Pulse = _types()[3]
    return Pulse(path=path, width=width, amplitude=100, phase=phase, detuning=0)


def _basic_pulse(parameters):
    parameters.pulses = [_pulse()]
    parameters.freq_h = 27.678523
    parameters.freq_p = 15.204524
    parameters.makePps = True
    parameters.samplePath = 0
    parameters.custom_freq = False


def _qubit(parameters):
    parameters.samplePath = 0
    parameters.pulses = [_pulse()]


def _t1(parameters):
    Pulse = _types()[3]
    parameters.samplePath = 0
    parameters.pulses = [
        _pulse(width=80),
        Pulse(path=0, width=100000, amplitude=0, phase=0, detuning=0),
    ]


def _t2(parameters):
    Pulse = _types()[3]
    parameters.samplePath = 0
    parameters.pulses = [
        _pulse(width=40),
        Pulse(path=0, width=250000, amplitude=0, phase=0, detuning=0),
        _pulse(width=80),
        Pulse(path=0, width=250000, amplitude=0, phase=0, detuning=0),
    ]


def _control(parameters):
    parameters.samplePath = -1
    parameters.pulses = [_pulse(path=0), _pulse(path=1)]


def _initialization(parameters):
    Pulse = _types()[3]
    parameters.repeat = 9
    parameters.pulses = [
        _pulse(0, 40, 90), Pulse(path=0, phase=0, amplitude=0, width=718),
        _pulse(0, 40, 0), Pulse(path=0, phase=0, amplitude=0, width=718),
        Pulse(path=0, phase=0, amplitude=0, width=40),
        Pulse(path=0, phase=0, amplitude=0, width=500000),
        Pulse(path=1, phase=0, amplitude=0, width=40),
        Pulse(path=1, phase=0, amplitude=0, width=718),
        _pulse(1, 40, 90), Pulse(path=1, phase=0, amplitude=0, width=718),
        _pulse(1, 40, 0), Pulse(path=1, phase=0, amplitude=0, width=500000),
    ]


def _circuit(kind="bell"):
    Circuit, Gate = _types()[0:2]
    circuit = Circuit(2)
    circuit << Gate(type="H", qubitIndex=0)
    circuit << Gate(type="CNOT" if kind == "bell" else "H", qubitIndex=1,
                    controlQubit=0 if kind == "bell" else -1)
    return circuit


def _gates(parameters):
    parameters.samplePath = -1
    parameters.using_pulse = False
    parameters.using_custom_gate = False
    parameters.using_custom_pps = False
    parameters.set_circuit(_circuit("parallel_h"))


def _tomography(parameters):
    parameters.samplePath = -1
    parameters.set_circuit(_circuit("parallel_h"))


def _task(parameters):
    parameters.samplePath = 0
    parameters.using_custom_gate = False
    parameters.using_custom_pps = False
    parameters.set_circuit(_circuit("parallel_h"))


def _algorithm(algorithm_type):
    def configure(parameters):
        parameters.algorithm_type = algorithm_type
        parameters.samplePath = -1
        parameters.grover_bin = 2
        parameters.set_circuit(_circuit())
    return configure


def _sample(parameters, sample_delay=0, both=False):
    parameters.pulses = [_pulse()]
    parameters.sampleCount = 16384
    parameters.sampleFre = 10000
    parameters.sampleDelay = sample_delay
    parameters.h_freShift = parameters.h_freDemo = 0
    if hasattr(parameters, "p_freShift"):
        parameters.p_freShift = parameters.p_freDemo = 0
    parameters.samplePath = -1 if both else 0


def _waveform(parameters, both=False):
    WaveformGenerator = _types()[4]
    parameters.pulses = WaveformGenerator.generate(
        channel=0, wave_type=WaveformGenerator.GAUSSIAN, samplePoint=64,
        timeLength=10000, phase=0, amplitude=100, detuning=0,
    )
    parameters.calibrate_sample = 0
    parameters.sampleCount = 16384
    parameters.sampleFre = 10000
    parameters.sampleDelay = 0
    parameters.h_freShift = parameters.p_freShift = 0
    parameters.h_freDemo = parameters.p_freDemo = 0
    parameters.samplePath = -1 if both else 0


def _physical(measurement):
    def configure(parameters):
        parameters.type_setting = measurement
        parameters.pulses = [_pulse()]
        parameters.gradients = []
        parameters.relaxation_delay = 15
        parameters.h_freShift = parameters.p_freShift = 0
        parameters.h_freDemo = parameters.p_freDemo = 0
        if measurement == 0:
            parameters.state_initialization = True
            parameters.sampleFre = 10000
            parameters.sampleCount = 16384
            parameters.sampleDelay = 0
            parameters.samplePath = 0
        elif measurement == 1:
            parameters.stepList = [1, 2, 3, 4, 5, 6]
        else:
            parameters.samplePath = -1
    return configure


def _circuit_layer(using_pulse):
    def configure(parameters):
        Gradient = _types()[2]
        parameters.using_pulse = using_pulse
        if using_pulse:
            parameters.pulses = [_pulse()]
        else:
            parameters.set_circuit(_circuit())
        parameters.gradients = [Gradient(path=1, duration=0, voltage=0)]
        parameters.relaxation_delay = 15
        parameters.h_freShift = parameters.p_freShift = 0
        parameters.h_freDemo = parameters.p_freDemo = 0
        parameters.sampleFre = 10000
        parameters.sampleCount = 16384
        parameters.sampleDelay = 0
        parameters.samplePath = -1
    return configure


_ALGORITHMS = (
    ("basic", "量子计算入门", "EXP_ALGORITHM_BASIC"),
    ("deutsch", "Deutsch 算法", "EXP_DEUTSCH"),
    ("bernstein_vazirani", "Bernstein–Vazirani 算法", "EXP_BERNSTEIN"),
    ("grover", "Grover 搜索", "EXP_GROVER"),
    ("qft", "量子傅里叶变换", "EXP_QFT"),
    ("hhl", "HHL 线性方程算法", "EXP_HHL"),
    ("vqe", "变分量子本征求解器", "EXP_VQE"),
    ("qaoa", "量子近似优化算法", "EXP_QAOA"),
)


LAB_TWO_PRESETS: Tuple[LabTwoPreset, ...] = (
    LabTwoPreset("lab.nmr_signal", "核磁共振现象与信号", "采集脉冲激发后的时域信号。", "EXP_PULSE", _basic_pulse),
    LabTwoPreset("lab.rabi", "Rabi 振荡", "运行一个 Rabi 扫描参考点。", "EXP_RABI", _basic_pulse),
    LabTwoPreset("lab.qubit", "量子比特基础实验", "制备、控制并测量单量子比特。", "EXP_QUBIT", _qubit),
    LabTwoPreset("lab.t1", "T1 纵向弛豫", "运行带等待区间的 T1 参考点。", "EXP_T1", _t1),
    LabTwoPreset("lab.t2", "T2 横向退相干", "运行回波式 T2 参考点。", "EXP_T2", _t2),
    LabTwoPreset("lab.control", "量子控制", "对两个核自旋通道施加控制脉冲。", "EXP_QCONTROL", _control),
    LabTwoPreset("lab.initialization", "量子系统初始化", "运行系统初始化脉冲序列。", "EXP_PSTATE", _initialization),
    LabTwoPreset("lab.gates_circuit", "量子门与线路", "运行两比特并行 H 门线路。", "EXP_QCIRCUIT", _gates),
    LabTwoPreset("lab.tomography", "量子态层析", "采集量子态重建所需数据。", "EXP_QREFACTOR", _tomography),
    LabTwoPreset("lab.computing_task", "量子计算任务", "提交两比特线路计算任务。", "EXP_QALGORITHM", _task),
    *tuple(LabTwoPreset("lab.algorithm." + key, title, "运行内置教学算法线路。", "EXP_QALGORITHMS", _algorithm(value)) for key, title, value in _ALGORITHMS),
    LabTwoPreset("lab.spin_echo", "自旋回波", "运行带采样延迟的自旋回波序列。", "EXP_SPINECHO", lambda p: _sample(p, sample_delay=40)),
    LabTwoPreset("lab.dynamic_decoupling", "动态解耦", "运行动态解耦参考脉冲。", "EXP_DYDECO", _sample),
    LabTwoPreset("lab.shaped_pulse", "整形脉冲", "运行高斯包络参考脉冲。", "EXP_SHAPEPULSE", _waveform),
    LabTwoPreset("lab.optimized_pulse", "数值优化脉冲", "在双通道采样模式运行优化脉冲。", "EXP_NPOPTI", lambda p: _waveform(p, both=True)),
    LabTwoPreset("lab.physical.custom", "物理层自定义测量", "按指定采样通道采集物理层信号。", "EXP_LAYER_PHYSICAL", _physical(0)),
    LabTwoPreset("lab.physical.pauli", "物理层 Pauli 分量测量", "执行协议支持的 Pauli 分量测量步骤。", "EXP_LAYER_PHYSICAL", _physical(1)),
    LabTwoPreset("lab.physical.tomography", "物理层量子态层析", "采集物理层量子态重建数据。", "EXP_LAYER_PHYSICAL", _physical(2)),
    LabTwoPreset("lab.circuit.pulse", "线路层脉冲实验", "在线路层直接运行脉冲序列。", "EXP_LAYER_CIRCUIT", _circuit_layer(True)),
    LabTwoPreset("lab.circuit.gates", "线路层量子线路", "在线路层运行 Bell 态线路。", "EXP_LAYER_CIRCUIT", _circuit_layer(False)),
)


def get_lab_two_preset(key: str) -> LabTwoPreset:
    for preset in LAB_TWO_PRESETS:
        if preset.key == key:
            return preset
    raise KeyError(f"unknown LabLink TWO preset: {key}")
