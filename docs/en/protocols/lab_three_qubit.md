# Lab three-qubit protocol mapping

This page describes private parameter classes and wire fields. Public callers use the [three-qubit experiment catalogue](../lab/three/index.rst), typed snake_case models and zero-based indices from [parameters](../parameters.rst).

Lab supports six three-qubit experiments. Select a `lab.three.*` key with `lab.create_experiment()`; the adapter selects `QubitMode.THREE` internally. The service must already be synchronized in THREE mode. Public callers do not pass a private `QubitMode` to experiment preparation or execution.

## Experiment types

| Experiment | Parameter class | Experiment types |
|---|---|---|
| Three-qubit physical-layer custom measurement | `ThreeQubitPhysicalCustomParameters` | `EXP_LAYER_PHYSICAL` |
| Three-qubit Pauli-component measurement | `ThreeQubitPhysicalPauliParameters` | `EXP_LAYER_PHYSICAL` |
| Three-qubit state tomography | `ThreeQubitPhysicalTomographyParameters` | `EXP_LAYER_PHYSICAL` |
| Three-qubit circuit-layer test pulse | `ThreeQubitCircuitPulseParameters` | `EXP_LAYER_CIRCUIT_PULSE` |
| Three-qubit quantum circuit | `ThreeQubitCircuitParameters` | `EXP_LAYER_CIRCUIT_CIRCUIT` |
| Three-qubit hybrid circuit | `ThreeQubitMixingCircuitParameters` | `EXP_MIXING_CIRCUIT` |

These are private serializer classes, not public import names. The three physical-layer experiments share one wire experiment type: the adapter derives `compute_type` from the selected public key (`lab.three.physical_custom`, `lab.three.physical_pauli` or `lab.three.tomography`) as `0`, `1` or `2` respectively.

## Qubit numbering

Public `sample_qubits` uses distinct indices 0, 1 or 2. The adapter converts these to private `sample_qubit` / wire `sampleQubit` values 1, 2 or 3. Public circuits use `Circuit(qubits=3, ...)` and zero-based `Gate` indices. Private `qubit_index`, `control_qubit` and `control_qubit2` remain zero-based; an unused private control field is -1. Do not supply one-based acquisition indices to public models.

## Run an experiment

The basic call sequence for a three-qubit experiment is:

```{literalinclude} ../../../examples/lab/three/circuit.py
:language: python
```

Six examples are provided in `examples/lab/three`. Before running an experiment, set the pulse widths, frequencies, power levels, and acquisition parameters from the device and sample calibration results.

## Experiment results

The private `ThreeQubitExperimentResult.get_result()` decoder returns:

* `data_updates`: data received while the experiment is running;
* `graph`: results grouped by chart name;
* `chart_streams`: chart data grouped by task, channel, qubit, and step;
* `final_data`: data returned when the experiment finishes.

The public execution call returns `ExperimentResult`; access the decoded Lab result through `result.data` and the backend envelope through `result.raw`. Result fields are shown in the corresponding experiment examples.
