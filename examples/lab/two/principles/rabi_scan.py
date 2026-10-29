# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""A measured pulse-width scan, distinct from the single-point Rabi preset."""

import math
from pathlib import Path

from spinqnmrlink import Pulse, SpinQNMRLink, models
from spinqnmrlink.analysis.rabi import fit_rabi, validate_rabi
from spinqnmrlink.experiments import serialize_result_document

CONFIG_PATH = Path("connection_config.local.json")
OUTPUT_DIRECTORY = Path("experiment_results/rabi_scan")
TIMEOUT_SECONDS = 300
CHANNEL = 0
WIDTHS_US = (0, 20, 40, 60, 80, 100, 120, 240, 400)
AMPLITUDE_PERCENT = 100
PHASE_DEG = 90
PLOT = False


def build_scan(
    *,
    channel=CHANNEL,
    widths_us=WIDTHS_US,
    amplitude_percent=AMPLITUDE_PERCENT,
    phase_deg=PHASE_DEG,
):
    """Create explicit pulse-width points in microseconds, without connecting."""
    if channel not in (0, 1):
        raise ValueError("channel must be 0 (H) or 1 (P)")
    if len(set(widths_us)) < 5:
        raise ValueError("provide at least five distinct pulse widths")
    definitions = []
    for width in widths_us:
        parameters = models.LabRabiParameters(freq_h=27.678523, freq_p=15.204524, make_pps=True)
        parameters.sample_path = channel
        parameters.custom_freq = False
        parameters.pulses = [
            Pulse(
                channel=channel,
                width_us=width,
                amplitude_percent=amplitude_percent,
                phase_deg=phase_deg,
            )
        ]
        definitions.append(parameters)
    for parameters in definitions:
        parameters.to_wire()  # Validate every point before opening the device.
    return definitions


def run_scan(
    config_path=CONFIG_PATH,
    *,
    channel=CHANNEL,
    widths_us=WIDTHS_US,
    amplitude_percent=AMPLITUDE_PERCENT,
    phase_deg=PHASE_DEG,
    timeout=TIMEOUT_SECONDS,
    output_directory=OUTPUT_DIRECTORY,
    offline=False,
    plot=False,
):
    """Run a full measurement scan, retain actual data and assess the fit separately."""
    definitions = build_scan(
        channel=channel,
        widths_us=widths_us,
        amplitude_percent=amplitude_percent,
        phase_deg=phase_deg,
    )
    if offline:
        print(
            serialize_result_document(
                {"source": "offline reference scan", "points": [p.to_wire() for p in definitions]}
            )
        )
        return {"source": "offline reference scan", "points": [p.to_wire() for p in definitions]}
    rows = []
    raw_results = []
    with SpinQNMRLink.from_config(config_path) as sdk:
        device = sdk.device("lab")
        device.open()
        for parameters in definitions:
            result = device.create_experiment("lab.two.rabi", parameters=parameters).run(
                timeout=timeout
            )
            raw_results.append(result.to_dict())
            value = (result.data or {}).get("real")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Device did not return a finite Rabi amplitude")
            rows.append(
                {
                    "width_us": parameters.pulses[0].width_us,
                    "amplitude": value,
                    "task_completed": result.status == "COMPLETED",
                    "graph_returned": bool(result.data.get("graph")),
                }
            )
    fit = fit_rabi(rows)
    label = "H" if channel == 0 else "P"
    assessment = validate_rabi({label: {"measurements": rows, "fit": fit}})
    document = {
        "measurements": rows,
        "fit": fit,
        "assessment": assessment,
        "raw_results": raw_results,
        "analysis_limits": "Period grid: 40-800 us. Fit quality describes agreement, not independent calibration accuracy.",
    }
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "rabi_scan.json").write_text(
        serialize_result_document(document), encoding="utf-8"
    )
    print(assessment)
    if plot:
        import matplotlib.pyplot as plt

        plt.scatter([r["width_us"] for r in rows], [r["amplitude"] for r in rows])
        plt.xlabel("Pulse width (us)")
        plt.ylabel("Measured real amplitude")
        plt.show()

    return document


if __name__ == "__main__":
    run_scan(plot=PLOT)
