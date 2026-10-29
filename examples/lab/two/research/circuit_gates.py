# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Circuit-layer quantum circuit.

Device: lab; mode: TWO.
Run a Bell-state circuit at the circuit layer.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Circuit, Gate, Gradient, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.circuit.gates"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabLayerCircuitParameters(
        using_pulse=False,  # True submits pulses; False submits the gate circuit.
        circuit=Circuit(
            qubits=2,  # Number of qubits; all gate indices are zero-based.
            gates=[
                Gate(
                    type="H",
                    target=0,
                    timeslot=0,  # Execution slot; identical slots group gates.
                ),
                Gate(
                    type="CNOT",
                    target=1,
                    control=0,
                    timeslot=1,  # Execution slot; identical slots group gates.
                ),
            ],
            measures=None,  # One acquisition-enable flag per qubit.
        ),
        pulses=[],
        gradients=[
            Gradient(
                path=1,  # Gradient channel identifier.
                voltage_v=0.0,  # Gradient voltage in volts.
                duration_us=0.0,  # Gradient duration in microseconds.
            ),
        ],
        sample_path=-1,  # Acquisition: 0=H, 1=P; -1=both where supported.
        relaxation_seconds=15.0,  # Recovery interval in seconds; choose for the actual sample.
        h_frequency_shift=0,  # H frequency offset in Hz.
        p_frequency_shift=0,  # P frequency offset in Hz.
        h_frequency_demo=0,  # H demodulation frequency in Hz.
        p_frequency_demo=0,  # P demodulation frequency in Hz.
        sample_frequency=10000,  # Hz; choose one: 10000, 20000, 50000, 100000.
        sample_count=16384,  # Acquired points; observe the model sampling limits.
        sample_delay_us=0,  # Acquisition delay in microseconds.
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
        print("Server fidelity, if returned:", data.get("fidelity"))
        # Inspect the measured data against the experiment target; completion is a task status.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
