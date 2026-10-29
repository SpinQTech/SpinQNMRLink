# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Discrete acquisition settings shared by SDK parameter adapters."""

from typing import Literal, cast, get_args

SampleFrequencyHz = Literal[10000, 20000, 50000, 100000]


def validate_sample_frequency(value: object) -> int:
    """Reject unsupported rates and implicit conversions before Literal validation."""
    if type(value) is not int or value not in get_args(SampleFrequencyHz):
        raise ValueError("sample_frequency must be one integer Hz value: 10000, 20000, 50000, 100000")
    return cast(int, value)
