# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Calibratable T1 inversion-recovery or T2 spin-echo scan, with optional fitting."""

import math
from pathlib import Path

from spinqnmrlink import Pulse, SpinQNMRLink, models
from spinqnmrlink.experiments import serialize_result_document

CONFIG_PATH = Path("connection_config.local.json")
OUTPUT_DIRECTORY = Path("experiment_results/relaxation_scan")
TIMEOUT_SECONDS = 300
KIND = "t1"  # Choose "t1" (inversion recovery) or "t2" (spin echo).
CHANNEL = 0
DELAYS_US = None  # Override with your sample's delay range in microseconds.
PI_US = 80
PI_OVER_2_US = 40
FIT = False  # Fitting requires the scipy dependency in the [plot] extra.


def build_scan(
    kind=KIND, *, channel=CHANNEL, delays_us=DELAYS_US, pi_us=PI_US, pi_over_2_us=PI_OVER_2_US
):
    """Create pulse sequences using calibrated pi and pi/2 widths in microseconds."""
    if kind not in ("t1", "t2"):
        raise ValueError("kind must be t1 or t2")
    if channel not in (0, 1):
        raise ValueError("channel must be 0 (H) or 1 (P)")
    delays = delays_us or (
        [0, 1_000_000, 4_000_000, 8_000_000]
        if kind == "t1"
        else [0, 100_000, 250_000, 500_000, 1_000_000, 2_000_000]
    )
    if len(set(delays)) < 3:
        raise ValueError("provide at least three distinct delays")
    definitions = []
    for delay in delays:
        parameter_type = models.LabT1Parameters if kind == "t1" else models.LabT2Parameters
        parameters = parameter_type(freq_h=27.678523, freq_p=15.204524, make_pps=True)
        parameters.sample_path = channel
        parameters.custom_freq = False

        def pulse(width, amplitude, phase=0):
            return Pulse(
                channel=channel, width_us=width, amplitude_percent=amplitude, phase_deg=phase
            )

        parameters.pulses = (
            [pulse(pi_us, 100, 90), pulse(delay, 0)]
            if kind == "t1"
            else [
                pulse(pi_over_2_us, 100, 90),
                pulse(delay / 2, 0),
                pulse(pi_us, 100, 90),
                pulse(delay / 2, 0),
            ]
        )
        definitions.append(parameters)
    for parameters in definitions:
        parameters.to_wire()
    return delays, definitions


def run_scan(
    kind=KIND,
    config_path=CONFIG_PATH,
    *,
    channel=CHANNEL,
    delays_us=DELAYS_US,
    pi_us=PI_US,
    pi_over_2_us=PI_OVER_2_US,
    timeout=TIMEOUT_SECONDS,
    output_directory=OUTPUT_DIRECTORY,
    offline=False,
    fit=False,
):
    """Measure a full T1/T2 series; fitting and structure checks are separate."""
    delays, definitions = build_scan(
        kind,
        channel=channel,
        delays_us=delays_us,
        pi_us=pi_us,
        pi_over_2_us=pi_over_2_us,
    )
    key = "lab.two." + kind
    if offline:
        print(
            serialize_result_document(
                {"source": "offline reference scan", "points": [p.to_wire() for p in definitions]}
            )
        )
        return {"source": "offline reference scan", "points": [p.to_wire() for p in definitions]}
    rows, raw_results = [], []
    with SpinQNMRLink.from_config(config_path) as sdk:
        device = sdk.device("lab")
        device.open()
        for delay, parameters in zip(delays, definitions):
            result = device.create_experiment(key, parameters=parameters).run(timeout=timeout)
            raw_results.append(result.to_dict())
            value = (result.data or {}).get("real" if kind == "t1" else "mod")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Device did not return a finite relaxation amplitude")
            rows.append(
                {
                    "delay_us": delay,
                    "amplitude": value,
                    "task_completed": result.status == "COMPLETED",
                    "graph_returned": bool(result.data.get("graph")),
                }
            )
    fit_requested = fit
    fit = None
    if fit_requested:
        if kind == "t1":
            from spinqnmrlink.analysis.t1 import fit_relaxation
        else:
            from spinqnmrlink.analysis.t2 import fit_relaxation
        fit = fit_relaxation(rows)
    assessment = {
        "execution_validation": "PASS" if all(r["graph_returned"] for r in rows) else "INCOMPLETE",
        "scientific_assessment": fit["fit_quality"] if fit else "NOT_ASSESSED",
    }
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / (kind + "_scan.json")).write_text(
        serialize_result_document(
            {
                "measurements": rows,
                "fit": fit,
                "assessment": assessment,
                "raw_results": raw_results,
                "analysis_limits": "Fit estimates depend on delay range, sample preparation and pulse calibration.",
            }
        ),
        encoding="utf-8",
    )
    print(assessment)
    return {"measurements": rows, "fit": fit, "assessment": assessment, "raw_results": raw_results}


if __name__ == "__main__":
    run_scan(fit=FIT)
