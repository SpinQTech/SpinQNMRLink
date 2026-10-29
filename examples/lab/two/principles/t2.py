# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""T2 transverse relaxation.

Device: lab; mode: TWO.
Run an echo-based T2 reference point.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

import math

from spinqnmrlink import Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.t2"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabT2Parameters(
        pulses=[
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=40.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=250000.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=0.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=80.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=90.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=250000.0,  # Duration (us); set active widths from calibration.
                amplitude_percent=0.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
        ],
        freq_h=27.0,  # H resonance (MHz); used when custom_freq=True.
        freq_p=11.0,  # P resonance (MHz); used when custom_freq=True.
        make_pps=False,  # Request the device PPS preparation step.
        sample_path=0,  # Acquisition channel: 0=H, 1=P.
        custom_freq=False,  # False uses the device lock-field frequencies.
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
        amplitude = data.get("mod")
        if (
            isinstance(amplitude, bool)
            or not isinstance(amplitude, (int, float))
            or not math.isfinite(amplitude)
        ):
            raise ValueError("The device did not return a finite measurement amplitude")
        print("Measured amplitude:", amplitude)  # Device signal units, not a probability.
        print("Pulse-width result:", data.get("width"))
        # One point does not establish a period or relaxation time. Use the scan example.
        return result
    # Leaving the context closes device resources, including when an exception occurs.


if __name__ == "__main__":
    run_experiment()  # This performs a hardware run using the configuration above.
