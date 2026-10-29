# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""3-qubit hybrid circuit.

Device: lab; mode: THREE.
Run a classical-quantum hybrid circuit defined by the protocol.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Circuit, Gate, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.three.hybrid_circuit"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabThreeQubitMixingCircuitParameters(
        circuit=Circuit(
            qubits=3,  # Number of qubits; all gate indices are zero-based.
            gates=[
                Gate(
                    type="H",
                    target=0,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
                Gate(
                    type="CCNOT",
                    target=2,
                    control=0,
                    control2=1,
                    timeslot=1,  # Execution slot; identical slots group gates.
                ),
            ],
        ),
        sample_path=0,  # Acquisition: 0=H, 1=P; -1=both where supported.
        sample_qubits=[0, 1, 2],  # Zero-based qubit indices; adapter converts THREE wire numbering.
        repeat=0,  # Device repetition setting; 0 retains its reference convention.
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
        if not any(
            data.get(field) for field in ("graph", "data_updates", "chart_streams", "final_data")
        ):
            raise ValueError("The device did not return a three-qubit measurement payload")
        print("Final server payload:", data.get("final_data"))
        print("Chart groups:", data.get("graph"))
        # Server-defined THREE data remains available unchanged in result.raw.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
