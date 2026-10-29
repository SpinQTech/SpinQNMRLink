# Copyright 2025 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""SpinQLink-owned quantum gate type backed by shared behavior."""

from typing import ClassVar, List

from spinqnmrlink._core.gates import GateModel


class Gate(GateModel):
    """SpinQLink gate policy with three-qubit controlled gates."""

    allowed_types: ClassVar[List[str]] = [
        "H", "I", "X", "Y", "Z", "X90", "Y90", "Z90",
        "Rx", "Ry", "Rz", "T", "Td", "S", "Sd",
        "CNOT", "CZ", "CCNOT", "CCZ",
    ]
    validate_control_qubits: ClassVar[bool] = True
    normalize_rotation_angles: ClassVar[bool] = True
