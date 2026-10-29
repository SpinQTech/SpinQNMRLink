# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Quantum control.

Device: lab; mode: TWO.
Apply control pulses to two nuclear-spin channels.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.control"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabQControlParameters(
        pulses=[
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=40.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=1,  # RF channel: 0=H, 1=P.
                width_us=40.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
        ],
        freq_h=27.0,  # H resonance (MHz); used when custom_freq=True.
        freq_p=11.0,  # P resonance (MHz); used when custom_freq=True.
        make_pps=True,  # Request the device PPS preparation step.
        sample_path=-1,  # Acquisition channel: 0=H, 1=P.
        custom_freq=False,  # False uses the device lock-field frequencies.
        using_awg_file=False,  # False submits the explicit pulse sequence instead of an AWG file.
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
