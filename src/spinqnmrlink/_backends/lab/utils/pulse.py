# Copyright 2025 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""Backward-compatible SpinQLabLink pulse and gradient types."""

from spinqnmrlink._core.models import GradientModel, PulseModel


class Pulse(PulseModel):
    """SpinQLabLink-owned pulse type backed by the shared implementation."""


class Gradient(GradientModel):
    """SpinQLabLink-owned gradient type backed by the shared implementation."""
