# Experiment source examples

[English](README.md) | [中文](README.zh_CN.md)

Install the SDK, then open an experiment file in your IDE. Each basic source contains explicit parameters, device connection, execution and reading of actual measurements. Code comments and result explanations are in English.

Copy the configuration template to `connection_config.local.json` in your working directory, edit its literal connection values (Lab credentials are reserved fields; Triangulum uses its existing User Center account) and replace reference pulse values with actual calibration. Running an experiment file or calling `run_experiment()` performs a hardware run. There is no global offline switch. Paths are relative to the working directory.

```python
from examples.lab.two.principles.rabi import build_parameters, run_experiment

parameters = build_parameters()
parameters.pulses[0].width_us = 40  # Calibrated pulse duration in microseconds.
result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
print(result.data["real"])  # Actual measured signal amplitude.
```

## Lab TWO — Principles of Quantum Computing

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

Full measured scans: [Rabi](lab/two/principles/rabi_scan.py), [T1/T2](lab/two/principles/relaxation_scan.py).

## Lab TWO — Quantum Algorithms

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

## Lab TWO — Integrated Quantum Technology Experiments

| Experiment key | Source |
| --- | --- |
| `lab.two.spin_echo` | [spin_echo](lab/two/technology/spin_echo.py) |
| `lab.two.dynamic_decoupling` | [dynamic_decoupling](lab/two/technology/dynamic_decoupling.py) |
| `lab.two.shaped_pulse` | [shaped_pulse](lab/two/technology/shaped_pulse.py) |
| `lab.two.optimized_pulse` | [optimized_pulse](lab/two/technology/optimized_pulse.py) |

## Lab TWO — Research Experiments

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

## Advanced workflows

[Offline validation](advanced/offline_parameters.py), [saving and assessment](advanced/save_and_assess.py), [direct device configuration](common/configure_devices.py).

```python
from examples.advanced.offline_parameters import check_parameters
from examples.advanced.save_and_assess import save_and_assess
from examples.lab.two.principles.rabi import build_parameters, run_experiment

request = check_parameters("lab.two.rabi", build_parameters())  # Offline: no device connection.
result = run_experiment("connection_config.local.json")  # Hardware: actual measured data.
assessment = save_and_assess(result, "experiment_results/rabi.json")
```

Single points demonstrate execution and data access; full scans or experiment-specific analysis establish scientific conclusions. A local timeout does not cancel a remote task. Actual equipment validation remains recorded separately.
