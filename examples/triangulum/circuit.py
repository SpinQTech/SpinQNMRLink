# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Quantum circuit experiment.

Device: triangulum; transport: JSON WebSocket.
Run a quantum gate circuit with one to three qubits.
Density-matrix support requires Triangulum client 2.0 or newer.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Circuit, Gate, SpinQNMRLink, models

EXPERIMENT_KEY = "triangulum.circuit"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.TriangulumCircuitLayerParameters(
        circuit=Circuit(
            qubits=3,  # Number of qubits; all gate indices are zero-based.
            gates=[
                Gate(
                    type="X",
                    target=0,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
                Gate(
                    type="X",
                    target=1,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
                Gate(
                    type="X",
                    target=2,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
            ],
            measures=[1, 1, 1],  # One acquisition-enable flag per qubit.
        ),
        qubits_num=3,  # Must match the Circuit qubit count.
        # Requires Triangulum client 2.0 or newer.
        calc_matrix=True,  # Request density-matrix components via top-level calcMatrix.
    )


def run_experiment(config_path="connection_config.local.json", *, parameters=None, timeout=300, queue_timeout=None):
    """Run one task; timeout bounds execution, queue_timeout optionally bounds queueing."""
    parameters = build_parameters() if parameters is None else parameters
    with SpinQNMRLink.from_config(config_path) as sdk:
        device = sdk.device("triangulum")
        device.open()  # Connect and authenticate the WebSocket session.
        experiment = device.create_experiment(EXPERIMENT_KEY, parameters=parameters)
        result = experiment.run(timeout=timeout, queue_timeout=queue_timeout)  # A local timeout does not cancel the device task.
        data = result.data
        if not isinstance(data, dict):
            raise ValueError("The device did not return a result object")
        print("Task:", result.status, result.task_id)
        probabilities = data.get("probabilities")
        if not probabilities:
            raise ValueError("The device did not return circuit probabilities")
        print("Basis-state probabilities:", probabilities)
        print("Density matrix, if returned:", data.get("density_matrix"))
        print("State vector, if returned:", data.get("state_vector"))
        # This reference circuit applies X to all three qubits: its ideal output is |111>.
        # Compare measured probabilities with that target; task completion alone is insufficient.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
