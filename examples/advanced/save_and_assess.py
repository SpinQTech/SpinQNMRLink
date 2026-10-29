# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Save actual measurements and assess data structure separately from scientific success."""

from pathlib import Path

from spinqnmrlink.experiments import serialize_result_document
from spinqnmrlink.validation import assess_result


def save_and_assess(result, output_path):
    """Save raw data, actual parameters and SDK metadata, then return the assessment."""
    assessment = assess_result(result)
    document = result.to_dict()
    document["assessment"] = assessment
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(serialize_result_document(document), encoding="utf-8")
    print("Data structure:", assessment["execution_validation"])
    print("Scientific assessment:", assessment["scientific_assessment"])
    print("Issues:", assessment["issues"])
    return assessment


if __name__ == "__main__":
    from spinqnmrlink import SpinQNMRLink, parameters_for

    parameters = parameters_for("lab.two.rabi")  # Replace reference values with actual calibration.
    with SpinQNMRLink.from_config("connection_config.local.json") as sdk:
        lab = sdk.device("lab")
        lab.open()
        measured_result = lab.create_experiment("lab.two.rabi", parameters=parameters).run(
            timeout=300
        )
    save_and_assess(measured_result, "experiment_results/rabi.json")
