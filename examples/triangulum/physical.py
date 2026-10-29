# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Physical-layer pulse experiment.

Device: triangulum; transport: JSON WebSocket.
Send pulses directly and acquire the device response.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "triangulum.physical"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.TriangulumPhysicalLayerParameters(
        pulses=[
            Pulse(
                channel=0,  # Triangulum RF channel 0.
                width_us=40.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
        ],
        sample_qubits=[],  # Protocol acquisition indices; Triangulum passes them through unchanged.
        type_setting=0,  # Measurement selection: 0=custom, 1=Pauli, 2=tomography.
        relaxation_seconds=2e-05,  # Recovery interval in seconds; choose for the actual sample.
        step_list=[],  # Protocol measurement-step identifiers, not qubit indices.
        frequency_shift=0,  # Frequency offset in Hz.
        frequency_demo=0,  # Demodulation frequency in Hz.
        state_initialization=False,  # Request device state initialization before acquisition.
        sample_frequency=20000,  # Hz; choose one: 10000, 20000, 50000, 100000.
        sample_count=16000,  # Acquired points; observe the model sampling limits.
        sample_delay_us=0,  # Acquisition delay in microseconds.
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
        if not data.get("graph"):
            raise ValueError("The device did not return acquired chart data")
        print("Acquired chart data:", data["graph"])
        # Inspect the measured data against the experiment target; completion is a task status.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
