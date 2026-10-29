# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Numerically optimized pulse.

Device: lab; mode: TWO.
Run an optimized pulse with both acquisition channels enabled.
Copy the configuration template to connection_config.local.json in your
working directory and edit its literal connection and credential values.
Use calibrated sample settings before calling run_experiment().
"""

from spinqnmrlink import Pulse, SpinQNMRLink, models

EXPERIMENT_KEY = "lab.two.optimized_pulse"


def build_parameters():
    """Configure the actual sample using calibrated pulse and acquisition values."""
    return models.LabNpoptiParameters(
        calibrate_sample=0,  # Sample selection: 0=phosphorus-containing sample, 1=water.
        pulses=[
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=13.53352832366127,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=15.305573773635818,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=17.24216238937528,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=19.348058160704674,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=21.62651668298873,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=24.079047427224857,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=26.705183522634336,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=29.502265617444284,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=32.465246735834974,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=35.58652521421384,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=38.855812751236414,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=42.260044322318876,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=45.783336177161424,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=49.40699735316383,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=53.10959910353452,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=56.8671053718672,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=60.653065971263345,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=64.43887248251953,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=68.1940751190348,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=71.88675697091757,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=75.48396019890073,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=78.95215696607879,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=82.25775623986647,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=85.36763613451477,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=88.24969025845955,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=90.87337563610701,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=93.21024923595276,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=95.23447998951764,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=96.92332344763442,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=98.25754689579004,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=99.22179382602435,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=99.80487811074755,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=100.0,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=99.80487811074755,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=99.22179382602435,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=98.25754689579004,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=96.92332344763442,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=95.23447998951764,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=93.21024923595276,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=90.87337563610701,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=88.24969025845955,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=85.36763613451477,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=82.25775623986647,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=78.95215696607879,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=75.48396019890073,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=71.88675697091757,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=68.1940751190348,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=64.43887248251953,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=60.653065971263345,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=56.8671053718672,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=53.10959910353452,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=49.40699735316383,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=45.783336177161424,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=42.260044322318876,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=38.855812751236414,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=35.58652521421384,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=32.465246735834974,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=29.502265617444284,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=26.705183522634336,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=24.079047427224857,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=21.62651668298873,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=19.348058160704674,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=17.24216238937528,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
            Pulse(
                channel=0,  # RF channel: 0=H, 1=P.
                width_us=156.25,  # Duration (us); set active widths from calibration.
                amplitude_percent=15.305573773635818,  # RF amplitude (%); 0 gives free evolution.
                phase_deg=0.0,  # Phase (degrees).
                detuning_hz=0.0,  # Pulse offset (Hz).
            ),
        ],
        sample_path=-1,  # Acquisition: 0=H, 1=P; -1=both where supported.
        sample_frequency=10000,  # Hz; choose one: 10000, 20000, 50000, 100000.
        sample_count=16384,  # Acquired points; observe the model sampling limits.
        sample_delay_us=0,  # Acquisition delay in microseconds.
        h_frequency_shift=0,  # H frequency offset in Hz.
        p_frequency_shift=0,  # P frequency offset in Hz.
        h_frequency_demo=0,  # H demodulation frequency in Hz.
        p_frequency_demo=0,  # P demodulation frequency in Hz.
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
