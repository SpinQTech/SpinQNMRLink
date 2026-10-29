# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Separate structural result checks from experiment-specific science assessment."""

from __future__ import annotations

import math


def assess_result(result):
    """Report incomplete data instead of inventing measurements or scientific success."""
    data = result.data
    issues = []
    if not isinstance(data, dict) or not data:
        issues.append("Missing result object")
        data = {}

    def finite(value):
        if isinstance(value, (int, float, complex)):
            try:
                return math.isfinite(value.real) and math.isfinite(value.imag)
            except OverflowError:
                return False
        if isinstance(value, dict):
            return all(finite(v) for v in value.values())
        if isinstance(value, (list, tuple)):
            return all(finite(v) for v in value)
        return True

    if not finite(data):
        issues.append("Non-finite result value")
    if data.get("graph"):
        from ._core.graphs import graph_curves

        try:
            curves = graph_curves(data["graph"])
            if not any(points for group in curves for points in group.values()):
                issues.append("Missing acquired chart points")
        except ValueError as exc:
            issues.append(str(exc))
    key = result.experiment_key
    from .catalogue import get_experiment

    descriptor = get_experiment(key)
    # THREE results intentionally preserve arbitrary server data; at least one
    # real update, chart or final payload must be present.
    if descriptor.mode == "THREE":
        if not any(data.get(x) for x in ("data_updates", "graph", "chart_streams", "final_data")):
            issues.append("Missing three-qubit measurement payload")
    else:
        if key == "triangulum.circuit":
            required_fields = ("probabilities",)
        elif key == "lab.two.tomography":
            # EXP_QREFACTOR measures fit coefficients. Reconstructed state
            # metrics are optional placeholders, not acquisition requirements.
            required_fields = ("graph", "q0_lamda", "q1_lamda")
        else:
            required_fields = descriptor.result_fields
        for name in required_fields:
            if data.get(name) is None:
                issues.append("Missing result field: " + name)
    if key == "triangulum.circuit":
        probabilities = data.get("probabilities")
        # The service may omit its optional qubit-count echo. Prefer the actual
        # submitted parameters without adding a synthetic measurement field.
        parameters = result.metadata.get("parameters", {})
        submitted_qubits = parameters.get("qubits_num")
        qubits = data.get("qubits_num", submitted_qubits)
        valid_shape = (
            isinstance(probabilities, list)
            and (
                len(probabilities) in (2, 4, 8)
                if qubits is None
                else type(qubits) is int and 1 <= qubits <= 3 and len(probabilities) == 2**qubits
            )
        )
        if (
            not valid_shape
            or (
                submitted_qubits is not None
                and (type(submitted_qubits) is not int or submitted_qubits != qubits)
            )
        ):
            issues.append("Missing or incorrectly shaped circuit probabilities")
        elif (
            any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not finite(v) or v < 0
                for v in probabilities
            )
            or abs(sum(probabilities) - 1) > 0.05
        ):
            issues.append("Probabilities are not finite, nonnegative and normalized")
    elif key == "lab.two.rabi":
        amplitude = data.get("real")
        if (
            isinstance(amplitude, bool)
            or not isinstance(amplitude, (int, float))
            or not finite(amplitude)
        ):
            issues.append("Missing finite Rabi amplitude")
        if not data.get("graph"):
            issues.append("Missing Rabi chart data")
    elif (
        key.endswith(
            (
                "physical.custom",
                "physical_custom",
                "nmr_signal",
                "spin_echo",
                "dynamic_decoupling",
                "shaped_pulse",
                "optimized_pulse",
            )
        )
        or key == "triangulum.physical"
    ):
        if not data.get("graph") and not data.get("chart_streams"):
            issues.append("Missing acquired signal data")
    elif key == "lab.two.tomography":
        for name in ("q0_lamda", "q1_lamda"):
            value = data.get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not finite(value):
                issues.append("Missing finite tomography fit coefficient: " + name)
    elif "pauli" in key:
        if (
            not data.get("pauli_matrix")
            and not data.get("pauli_basis")
            and not data.get("data_updates")
            and not data.get("final_data")
        ):
            issues.append("Missing Pauli measurement data")
    elif "tomography" in key:
        if not any(
            data.get(x)
            for x in (
                "state_vector",
                "density_matrix",
                "matrix",
                "probability",
                "data_updates",
                "final_data",
            )
        ):
            issues.append("Missing state reconstruction data")
    return {
        "execution_validation": "PASS"
        if result.status == "COMPLETED" and not issues
        else "INCOMPLETE",
        "issues": issues,
        "scientific_assessment": "NOT_ASSESSED",
        "scientific_reason": "A reference point does not establish the scientific target; use the experiment-specific scan or analysis.",
    }
