# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Quantum gates and circuits.

Device: lab; mode: TWO.
Run a two-qubit circuit with parallel Hadamard gates.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Circuit, Gate, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.gates_circuit"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabQCircuitParameters(
        pulses=[],
        freq_h=27.0,  # H resonance (MHz); used when custom_freq=True.
        freq_p=11.0,  # P resonance (MHz); used when custom_freq=True.
        custom_freq=False,  # False uses the device lock-field frequencies.
        sample_path=-1,  # Acquisition: 0=H, 1=P; -1=both where supported.
        circuit=Circuit(
            qubits=2,  # Number of qubits; all gate indices are zero-based.
            gates=[
                Gate(
                    type="H",
                    target=0,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
                Gate(
                    type="H",
                    target=1,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
            ],
            measures=None,  # One acquisition-enable flag per qubit.
        ),
        using_pulse=False,  # True submits pulses; False submits the gate circuit.
        using_custom_gate=False,  # False uses device-calibrated gate definitions.
        using_custom_pps=False,  # Use device PPS preparation instead of custom JSON.
        pps_json="",  # Ignored when using_custom_pps=False.
        pps_repeat=0,  # Custom PPS repetition setting.
        hlamda=0.0,  # H initialization coefficient; retain the device reference convention.
        plamda=0.0,  # P initialization coefficient; retain the device reference convention.
    )


def run_experiment(config_path="connection_config.local.json", *, parameters=None, timeout=300, queue_timeout=None):
    """Run one task; timeout bounds execution, queue_timeout optionally bounds queueing."""
    parameters = build_parameters() if parameters is None else parameters
    with SpinQNMRLink.from_config(config_path) as sdk:
        device = sdk.device("lab")
        device.open()  # Connect, authenticate and synchronize device state.
        experiment = device.create_experiment(EXPERIMENT_KEY, parameters=parameters)
        result = experiment.run(timeout=timeout, queue_timeout=queue_timeout)  # A local timeout does not cancel the device task.
        data = result.data
        if not isinstance(data, dict):
            raise ValueError("The device did not return a result object")
        print("Task:", result.status, result.task_id)
        if not data.get("graph"):
            raise ValueError("The device did not return acquired chart data")
        print("Acquired chart data:", data["graph"])
        print("Basis probabilities, if returned:", data.get("probability"))
        print("Reconstructed matrix, if returned:", data.get("matrix"))
        # Inspect the measured data against the experiment target; completion is a task status.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
