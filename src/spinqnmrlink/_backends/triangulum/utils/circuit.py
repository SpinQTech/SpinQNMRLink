# Copyright 2025 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""SpinQLink circuit policy backed by shared scheduling behavior."""

from typing import List

from spinqnmrlink._core.circuits import CircuitBase


class Circuit(CircuitBase):
    def __init__(self, qubits_num: int = 0) -> None:
        if qubits_num <= 0 or qubits_num > 3:
            raise ValueError("Invalid qubits number, must be between 1 and 3")
        super().__init__(qubits_num, max_qubits=3)
        self.measures = [1] * qubits_num

    def set_measures(self, measures: List[int]):
        self.measures = measures
        if len(measures) != self.qubits_num:
            raise ValueError("Invalid measures number, must be equal to qubits number")
        if any(measure < 0 or measure > 1 for measure in measures):
            raise ValueError("Invalid measure value, must be 0 or 1")

    def get_measures(self) -> List[int]:
        return self.measures

    def to_dict(self) -> dict:
        active_qubits = sum(1 for measure in self.measures if measure == 1)
        if active_qubits == 0:
            raise ValueError("Invalid measures, must be at least one qubit to be measured")
        if active_qubits > self.qubits_num:
            raise ValueError(
                "Invalid measures, must be at most the number of qubits to be measured"
            )
        max_timeslot = max((gate.timeslot for gate in self.circuit), default=0)
        if max_timeslot > 60:
            raise ValueError("Invalid timeslot, must be less than 60")
        return {
            "gates": [gate.to_dict() for gate in self.circuit],
            "measures": self.measures,
        }
