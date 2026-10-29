# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Spin echo.

Device: lab; mode: TWO.
Run a spin-echo sequence with a sampling delay.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.spin_echo"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabSpinechoParameters(
        pulses=[
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=40.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
        ],
        sample_path=0,  # Acquisition: 0=H, 1=P; -1=both where supported.
        sample_frequency=10000,  # Hz; choose one: 10000, 20000, 50000, 100000.
        sample_count=16384,  # Acquired points; observe the model sampling limits.
        sample_delay_us=40,  # Acquisition delay in microseconds.
        h_frequency_shift=0,  # H frequency offset in Hz.
        h_frequency_demo=0,  # H demodulation frequency in Hz.
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
        print("Spin phase in degrees, if returned:", data.get("phase"))
        # Inspect the measured data against the experiment target; completion is a task status.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
