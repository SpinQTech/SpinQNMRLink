# Lab experiment types and task parameters

This page maps public experiment selection to private protocol types. See [experiments](../experiments.rst) and [parameters](../parameters.rst) for public keys, names and units.

Public callers use `parameters_for(key)` and `lab.create_experiment(key, parameters=...)`. Preparation is offline; `lab.open()` establishes readiness and `experiment.run(timeout=...)` submits and waits for the result. Internally, the adapter uses `ExperimentType` and `register_experiment()` to create the backend task. Public examples should not import these private types or call backend registration methods.

## Experiment types

Common experiment types include:

* Fundamental experiments: NMR phenomenon and signal, Rabi oscillation, qubit, T1, T2, quantum control, quantum-system initialization, quantum circuit, state tomography, and quantum computing task;
* Algorithm experiments: basic, Deutsch, Bernstein, Grover, QFT, HHL, VQE, and QAOA;
* Integrated experiments: spin echo, dynamic decoupling, shaped pulse, and numerical pulse optimization;
* Three-qubit experiments: physical-layer measurement, circuit-layer test pulse, quantum circuit, and hybrid circuit.

See `spinqnmrlink._backends.lab.utils.types.ExperimentType` for the complete enumeration.

## Set parameters

The following example uses the NMR phenomenon and signal experiment:

```{literalinclude} ../../../examples/lab/two/principles/nmr_signal.py
:language: python
```

Each key uses the exact public model returned by `parameters_for(key)`. For the NMR example, `custom_freq=False` uses the device lock frequencies; set `freq_h` and `freq_p` when `custom_freq=True`. See the generated parameter table on the corresponding experiment page for meanings, units and constraints. Set frequency, power, pulse width and delay from the current device and sample calibration.

## Task information

When an experiment runs, the SDK creates a task from the experiment type, device ID, experiment parameters, and creation time, then sends it to the experimental system. The system updates task state and start and end times during execution; users normally do not create or modify task objects directly.

The public `lab.two.*` and `lab.three.*` keys select the required mode. The adapter maps these to `QubitMode.TWO` and `QubitMode.THREE` and checks the authoritative server mode; selecting a key does not switch the equipment's mode. See [three-qubit protocol mapping](lab_three_qubit.md) for details.
