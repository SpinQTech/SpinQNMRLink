# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Numerical analysis of measured experiment data."""

import math

import numpy as np


def _fit_rabi(rows):
    """Grid-search frequency; solve offset/sine/cosine coefficients linearly."""
    if len(rows) < 5:
        raise ValueError("at least five valid Rabi points are required for sinusoidal fitting")
    x = np.asarray([row["width_us"] for row in rows], dtype=float)
    y = np.asarray([row["amplitude"] for row in rows], dtype=float)
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("Rabi fitting requires finite pulse widths and amplitudes")
    periods = np.linspace(40.0, 800.0, 15201)
    best = None
    for period in periods:
        omega = 2 * np.pi / period
        design = np.column_stack((np.ones_like(x), np.sin(omega * x), np.cos(omega * x)))
        coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
        residual = y - design @ coefficients
        error = float(residual @ residual)
        if best is None or error < best[0]:
            best = (error, period, coefficients)

    error, period, coefficients = best
    offset, sine, cosine = coefficients
    amplitude = float(math.hypot(sine, cosine))
    phase = float(math.atan2(cosine, sine))
    total = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1.0 - error / total if total > 0 else 0.0
    fit_quality = "GOOD" if r_squared >= 0.8 else "ESTIMATE" if r_squared >= 0.6 else "POOR"
    return {
        "period_us": float(period),
        "rabi_frequency_hz": float(1_000_000.0 / period),
        "fitted_amplitude": amplitude,
        "maximum_measured_abs_amplitude": float(np.max(np.abs(y))),
        "offset": float(offset),
        "phase_radians": phase,
        "r_squared": float(r_squared),
        "fit_quality": fit_quality,
        "rotation_widths_us": {
            "pi_over_2": float(period / 4),
            "pi": float(period / 2),
            "three_pi_over_2": float(3 * period / 4),
            "two_pi": float(period),
        },
    }


def _fitted_curve(fit, x):
    omega = 2 * np.pi / fit["period_us"]
    return fit["offset"] + fit["fitted_amplitude"] * np.sin(omega * x + fit["phase_radians"])


def _validate(channel_results):
    if not channel_results:
        return {
            "execution_validation": "INCOMPLETE",
            "fit_assessment": "CHECK",
        }
    execution_passed = all(
        row["task_completed"] and row["graph_returned"]
        for item in channel_results.values()
        for row in item["measurements"]
    )
    fit_qualities = [item["fit"]["fit_quality"] for item in channel_results.values()]
    estimates_available = all(
        quality != "POOR" and 40.0 < item["fit"]["period_us"] < 800.0
        for quality, item in zip(fit_qualities, channel_results.values())
    )

    return {
        "execution_validation": "PASS" if execution_passed else "INCOMPLETE",
        "fit_assessment": (
            "GOOD"
            if estimates_available and all(quality == "GOOD" for quality in fit_qualities)
            else "ESTIMATE"
            if estimates_available
            else "CHECK"
        ),
    }


def _format_r_squared(value):
    return f"≈{value:.3f}" if value >= 0.9995 else f"={value:.3f}"


fit_rabi = _fit_rabi
validate_rabi = _validate
