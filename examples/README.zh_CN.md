# 实验源码示例

[English](README.md) | [中文](README.zh_CN.md)

安装 SDK 后，在 IDE 中打开实验文件。每个基础源码明确展示参数、设备连接、执行及实际测量读取。源码注释、参数和结果解释使用英文。

将配置模板复制为当前工作目录下的 `connection_config.local.json`，编辑字面连接值（Lab 账号密码为预留字段，三角座使用已有用户中心账号），并按实际校准修改参考脉冲。直接运行实验文件或调用 `run_experiment()` 会执行硬件实验，不设置全局离线开关。路径相对于工作目录。

```python
from examples.lab.two.principles.rabi import build_parameters, run_experiment

parameters = build_parameters()
parameters.pulses[0].width_us = 40  # Calibrated pulse duration in microseconds.
result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
print(result.data["real"])  # Actual measured signal amplitude.
```

## Lab TWO — 量子计算原理

| Experiment key | Source |
| --- | --- |
| `lab.two.nmr_signal` | [nmr_signal](lab/two/principles/nmr_signal.py) |
| `lab.two.rabi` | [rabi](lab/two/principles/rabi.py) |
| `lab.two.qubit` | [qubit](lab/two/principles/qubit.py) |
| `lab.two.t1` | [t1](lab/two/principles/t1.py) |
| `lab.two.t2` | [t2](lab/two/principles/t2.py) |
| `lab.two.control` | [control](lab/two/principles/control.py) |
| `lab.two.initialization` | [initialization](lab/two/principles/initialization.py) |
| `lab.two.gates_circuit` | [gates_circuit](lab/two/principles/gates_circuit.py) |
| `lab.two.tomography` | [tomography](lab/two/principles/tomography.py) |
| `lab.two.computing_task` | [computing_task](lab/two/principles/computing_task.py) |

完整实测扫描： [Rabi](lab/two/principles/rabi_scan.py), [T1/T2](lab/two/principles/relaxation_scan.py).

## Lab TWO — 量子算法

| Experiment key | Source |
| --- | --- |
| `lab.two.algorithm.basic` | [algorithm_basic](lab/two/algorithms/algorithm_basic.py) |
| `lab.two.algorithm.deutsch` | [algorithm_deutsch](lab/two/algorithms/algorithm_deutsch.py) |
| `lab.two.algorithm.bernstein_vazirani` | [algorithm_bernstein_vazirani](lab/two/algorithms/algorithm_bernstein_vazirani.py) |
| `lab.two.algorithm.grover` | [algorithm_grover](lab/two/algorithms/algorithm_grover.py) |
| `lab.two.algorithm.qft` | [algorithm_qft](lab/two/algorithms/algorithm_qft.py) |
| `lab.two.algorithm.hhl` | [algorithm_hhl](lab/two/algorithms/algorithm_hhl.py) |
| `lab.two.algorithm.vqe` | [algorithm_vqe](lab/two/algorithms/algorithm_vqe.py) |
| `lab.two.algorithm.qaoa` | [algorithm_qaoa](lab/two/algorithms/algorithm_qaoa.py) |

## Lab TWO — 综合量子技术实验

| Experiment key | Source |
| --- | --- |
| `lab.two.spin_echo` | [spin_echo](lab/two/technology/spin_echo.py) |
| `lab.two.dynamic_decoupling` | [dynamic_decoupling](lab/two/technology/dynamic_decoupling.py) |
| `lab.two.shaped_pulse` | [shaped_pulse](lab/two/technology/shaped_pulse.py) |
| `lab.two.optimized_pulse` | [optimized_pulse](lab/two/technology/optimized_pulse.py) |

## Lab TWO — 研究型实验

| Experiment key | Source |
| --- | --- |
| `lab.two.physical.custom` | [physical_custom](lab/two/research/physical_custom.py) |
| `lab.two.physical.pauli` | [physical_pauli](lab/two/research/physical_pauli.py) |
| `lab.two.physical.tomography` | [physical_tomography](lab/two/research/physical_tomography.py) |
| `lab.two.circuit.pulse` | [circuit_pulse](lab/two/research/circuit_pulse.py) |
| `lab.two.circuit.gates` | [circuit_gates](lab/two/research/circuit_gates.py) |

## Lab THREE

| Experiment key | Source |
| --- | --- |
| `lab.three.physical_custom` | [physical_custom](lab/three/physical_custom.py) |
| `lab.three.physical_pauli` | [physical_pauli](lab/three/physical_pauli.py) |
| `lab.three.tomography` | [tomography](lab/three/tomography.py) |
| `lab.three.circuit_pulse` | [circuit_pulse](lab/three/circuit_pulse.py) |
| `lab.three.circuit` | [circuit](lab/three/circuit.py) |
| `lab.three.hybrid_circuit` | [hybrid_circuit](lab/three/hybrid_circuit.py) |

## Triangulum

| Experiment key | Source |
| --- | --- |
| `triangulum.physical` | [physical](triangulum/physical.py) |
| `triangulum.circuit` | [circuit](triangulum/circuit.py) |

## 进阶流程

[Offline validation](advanced/offline_parameters.py), [saving and assessment](advanced/save_and_assess.py), [direct device configuration](common/configure_devices.py).

```python
from examples.advanced.offline_parameters import check_parameters
from examples.advanced.save_and_assess import save_and_assess
from examples.lab.two.principles.rabi import build_parameters, run_experiment

request = check_parameters("lab.two.rabi", build_parameters())  # Offline: no device connection.
result = run_experiment("connection_config.local.json")  # Hardware: actual measured data.
assessment = save_and_assess(result, "experiment_results/rabi.json")
```

单点演示执行与取数，科学结论需要完整扫描或实验专属分析。本地等待超时不会取消远端任务，实际设备验证单独记录。
