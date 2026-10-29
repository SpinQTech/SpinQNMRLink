# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Shared implementations for source-identical public value models.

Concrete public classes remain in their original packages so import paths,
type identity and package ownership stay backward compatible.
"""

from pydantic import BaseModel, Field


class PulseModel(BaseModel):
    path: int = Field(default=0, ge=0, le=1, description="NMR channel")
    width: float = Field(default=0, ge=0, le=20000000, description="Width (us)")
    amplitude: float = Field(default=0, ge=0, le=100, description="Amplitude (%)")
    phase: float = Field(default=0, description="Phase (degrees)")
    detuning: float = Field(default=0, ge=-10000, le=10000, description="Frequency shift (Hz)")

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "am": self.amplitude,
            "phase": self.phase,
            "freshift": self.detuning,
        }


class GradientModel(BaseModel):
    path: int = Field(default=1, ge=0, le=13, description="Shimming path")
    voltage: float = Field(default=0, ge=-1, le=1, description="Voltage (V)")
    duration: float = Field(default=0, ge=0, le=20000000, description="Duration (us)")

    def to_dict(self) -> dict:
        return {"path": self.path, "value": self.voltage, "delay": self.duration}
