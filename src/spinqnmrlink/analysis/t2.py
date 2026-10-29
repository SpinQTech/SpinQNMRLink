# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Numerical analysis of measured experiment data."""

import numpy as np
from scipy.optimize import curve_fit


def _model(t, amplitude, t2, offset):
    return amplitude * np.exp(-t / t2) + offset


def _fit(rows):
    if len(rows) < 3:
        raise ValueError("at least three valid T2 points are required for exponential fitting")
    x = np.asarray([row["delay_us"] for row in rows], dtype=float)
    y = np.asarray([row["amplitude"] for row in rows], dtype=float)
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("T2 fitting requires finite delays and magnitudes")
    scale = max(float(np.max(np.abs(y))), 1.0)
    parameters, _ = curve_fit(
        _model,
        x,
        y,
        p0=(float(y[0] - y[-1]), 500_000.0, float(y[-1])),
        bounds=([-10 * scale, 1_000.0, -10 * scale], [10 * scale, 20_000_000.0, 10 * scale]),
        maxfev=20_000,
    )
    fitted = _model(x, *parameters)
    residual = float(np.sum((y - fitted) ** 2))
    total = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1 - residual / total if total > 0 else 0.0
    return {
        "amplitude": float(parameters[0]),
        "t2_us": float(parameters[1]),
        "offset": float(parameters[2]),
        "r_squared": r_squared,
        "fit_quality": ("GOOD" if r_squared >= 0.8 else "ESTIMATE" if r_squared >= 0.6 else "POOR"),
    }


fit_relaxation = _fit
