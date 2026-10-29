# Copyright 2025 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""SpinQLabLink circuit policy backed by shared scheduling behavior."""

from spinqnmrlink._core.circuits import CircuitBase


class Circuit(CircuitBase):
    def __init__(self, qubits_num: int = 0) -> None:
        if qubits_num <= 0 or qubits_num > 2:
            raise ValueError("Invalid qubits number, must be 1 or 2")
        super().__init__(qubits_num, max_qubits=2)

    def to_dict(self) -> list:
        return [gate.to_dict() for gate in self.circuit]
