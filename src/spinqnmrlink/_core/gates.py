# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Shared gate fields and serialization with package-specific policy hooks."""

from typing import ClassVar, List

from pydantic import BaseModel, ConfigDict, Field


class GateModel(BaseModel):
    """Common gate representation; concrete packages retain their policies."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    allowed_types: ClassVar[List[str]] = []
    validate_control_qubits: ClassVar[bool] = False
    normalize_rotation_angles: ClassVar[bool] = False

    angle: float = Field(default=0, description="Rotation angle")
    controlQubit: int = Field(default=-1, description="Control qubit")
    controlQubit2: int = Field(default=-1, description="Second control qubit")
    delay: float = Field(default=0, description="Delay before the gate")
    qubitIndex: int = Field(default=0, description="Target qubit index")
    timeslot: int = Field(default=0, description="Circuit timeslot")
    type: str = Field(default="X", description="Gate type")

    def __init__(self, type: str, **kwargs):
        super().__init__(**kwargs)
        if type not in self.allowed_types:
            raise ValueError(
                f"Gate type '{type}' not supported. Allowed types are {self.allowed_types}."
            )
        self.type = type
        if self.validate_control_qubits:
            if type in {"CNOT", "CZ"} and self.controlQubit == -1:
                raise ValueError(
                    "Invalid gate, controlQubit must be set for CNOT and CZ gates"
                )
            if type in {"CCNOT", "CCZ"} and (
                self.controlQubit == -1 or self.controlQubit2 == -1
            ):
                raise ValueError(
                    "Invalid gate,controlQubit or controlQubit2 must be set "
                    "for CCNOT and CCZ gates"
                )
        if self.normalize_rotation_angles and type in {"Rx", "Ry", "Rz"}:
            while self.angle < 0:
                self.angle += 360
            while self.angle > 720:
                self.angle -= 360

    def to_dict(self) -> dict:
        return {
            "angle": self.angle,
            "controlQubit": self.controlQubit,
            "controlQubit2": self.controlQubit2,
            "delay": self.delay,
            "qubitIndex": self.qubitIndex,
            "timeslot": self.timeslot,
            "type": self.type,
        }
