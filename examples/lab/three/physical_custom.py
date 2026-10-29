# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""3-qubit physical-layer custom measurement.

Device: lab; mode: THREE.
Acquire the three-qubit pulse response on the selected channels.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Gradient, Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.three.physical_custom"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabThreeQubitPhysicalCustomParameters(
        fre_demo=0,  # Device demodulation setting in Hz.
        fre_shift=0,  # Device frequency-offset setting in Hz.
        pulse=models.LabThreeQubitPulseSequence(
            h_pulse=[
                Pulse(
                    channel=0,  # Hydrogen RF channel 0.
                    width_us=200.0,  # Duration (us); set active widths from calibration.
                    amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                    phase_deg=0.0,  # Phase (degrees).
                    detuning_hz=0.0,  # Pulse offset (Hz).
                ),
            ],
            gradient=[
                Gradient(
                    path=1,  # Gradient channel identifier.
                    voltage_v=0.0,  # Gradient voltage in volts.
                    duration_us=0.0,  # Gradient duration in microseconds.
                ),
            ],
        ),
        calc_matrix=True,  # Request state reconstruction when supported by this experiment.
        relaxation_seconds=15,  # Recovery interval in seconds; choose for the actual sample.
        sample_count=16000,  # Acquired points; observe the model sampling limits.
        sample_delay_us=0,  # Acquisition delay in microseconds.
        sample_frequency=50000,  # Hz; choose one: 10000, 20000, 50000, 100000.
        sample_qubits=[0, 1, 2],  # Zero-based qubit indices; adapter converts THREE wire numbering.
        make_pps=True,  # Request the device PPS preparation step.
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
