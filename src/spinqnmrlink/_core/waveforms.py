# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Protocol-neutral waveform generation shared by both public packages."""

from typing import List

import numpy as np


class WaveformGeneratorBase:
    """Common numerical implementation with a package-owned pulse factory."""

    RECTANGULAR = "Rectangular"
    GAUSSIAN = "Gaussian"
    HERMITE = "Hermite"
    REBURP = "REBURP"
    pulse_type = None

    @classmethod
    def generate(
        cls,
        channel: int,
        wave_type: str,
        samplePoint: int,
        timeLength: int,
        phase: float,
        amplitude: float,
        detuning: int,
    ) -> List[object]:
        if channel < 0 or channel > 1:
            raise ValueError(f"Channel selection error: {channel}")
        # REBURP was historically named but not accepted by either package.
        if wave_type not in [cls.RECTANGULAR, cls.GAUSSIAN, cls.HERMITE]:
            raise ValueError(f"Unsupported waveform type: {wave_type}")
        if samplePoint not in [4, 8, 16, 32, 64]:
            raise ValueError(f"Sample points must be 4,8,16,32,64: {samplePoint}")
        if phase < 0 or phase > 360:
            raise ValueError(f"Phase must be 0-360 degrees: {phase}")
        if amplitude < 0 or amplitude > 100:
            raise ValueError(f"Amplitude must be 0-100: {amplitude}")
        if detuning < -10000 or detuning > 10000:
            raise ValueError(f"Frequency offset must be -1000-1000Hz: {detuning}")
        if cls.pulse_type is None:
            raise TypeError("waveform generator subclass must define pulse_type")

        width = timeLength / samplePoint
        time_points = np.arange(0, timeLength, width)
        if wave_type == cls.RECTANGULAR:
            values = cls._rectangular_wave(timeLength, samplePoint, time_points)
        elif wave_type == cls.GAUSSIAN:
            values = cls._gaussian_wave(timeLength, samplePoint, time_points)
        elif wave_type == cls.HERMITE:
            values = cls._hermite_wave(timeLength, samplePoint, time_points)
        else:
            values = cls._reburp_wave(timeLength, samplePoint, time_points)

        pulses = []
        for index in range(len(time_points)):
            pulse_phase = phase if values[index] >= 0 else phase + 360
            pulse_amplitude = min(abs(values[index] * amplitude), 100)
            pulses.append(
                cls.pulse_type(
                    path=channel,
                    amplitude=pulse_amplitude,
                    phase=pulse_phase,
                    width=width,
                    detuning=detuning,
                )
            )
        return pulses

    @staticmethod
    def _rectangular_wave(timeLength, samplePoint, time_points):
        return np.ones_like(time_points)

    @staticmethod
    def _gaussian_wave(timeLength, samplePoint, time_points):
        sigma = timeLength / 4
        mean = timeLength / 2
        return np.exp(-((time_points - mean) ** 2) / (2 * sigma ** 2))

    @staticmethod
    def _hermite_wave(timeLength, samplePoint, time_points):
        sigma = timeLength / 4
        mean = timeLength / 2
        normalized = (time_points - mean) / sigma
        return (1 - 2 * normalized ** 2) * np.exp(-(normalized ** 2) / 2)

    @staticmethod
    def _reburp_wave(timeLength, samplePoint, time_points):
        mean = timeLength / 2
        normalized = 2 * (time_points - mean) / timeLength
        values = np.zeros_like(time_points)
        for index in range(len(time_points)):
            if abs(normalized[index]) <= 1:
                value = 0
                for harmonic in range(1, 6):
                    value += (1 / harmonic) * np.sin(
                        harmonic * np.pi * normalized[index]
                    )
                values[index] = value
        return values
