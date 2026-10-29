# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Protocol v2.0 three-qubit experiment parameter models.

The wire envelope and the experiment parameters are separate concerns:
these models build the JSON text stored in ``Task.params`` and ``Task.extra``;
``SpinQLabLink.add_task(..., QubitMode.THREE)`` supplies the authoritative
three-qubit mode in the outer Protobuf envelope.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, ClassVar, Dict, Mapping, Optional, Sequence, Tuple, Union

from ..connection.models import Task
from ...._core.parameter_choices import SampleFrequencyHz, validate_sample_frequency


Number = Union[int, float]

PHYSICAL_TASK_TYPE = "EXP_LAYER_PHYSICAL"
CIRCUIT_PULSE_TASK_TYPE = "EXP_LAYER_CIRCUIT_PULSE"
CIRCUIT_TASK_TYPE = "EXP_LAYER_CIRCUIT_CIRCUIT"
MIXING_CIRCUIT_TASK_TYPE = "EXP_MIXING_CIRCUIT"

THREE_QUBIT_GATE_TYPES = frozenset(
    {
        "H", "I", "X", "Y", "Z", "X90", "Y90", "Z90",
        "Rx", "Ry", "Rz", "T", "Td", "CNOT", "CZ", "CCNOT",
        "CCZ", "SWAP", "CSWAP", "Customized",
    }
)
THREE_QUBIT_PAULI_STEPS = frozenset({1, 2, 4, 7, 8, 9, 10})


def _require_number(name: str, value: Number) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")


def _require_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def _require_boolean(name: str, value: bool) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def _validate_sample_qubits(values: Sequence[int]) -> Tuple[int, ...]:
    result = tuple(values)
    if not result:
        raise ValueError("sampleQubit must contain at least one qubit")
    for value in result:
        _require_integer("sampleQubit item", value)
        if value not in (1, 2, 3):
            raise ValueError("sampleQubit items must use one-based values 1, 2, or 3")
    return result


def _validate_circuit_index(name: str, value: int, *, allow_absent: bool) -> None:
    _require_integer(name, value)
    valid = (-1, 0, 1, 2) if allow_absent else (0, 1, 2)
    if value not in valid:
        wording = "-1, 0, 1, or 2" if allow_absent else "0, 1, or 2"
        raise ValueError(f"{name} must be {wording}")


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class ThreeQubitPulse:
    """One item in the Appendix A ``pulse.hPulse`` array."""

    phase: Number
    am: Number
    width: Number
    freshift: Number

    def __post_init__(self) -> None:
        for name in ("phase", "am", "width", "freshift"):
            _require_number(name, getattr(self, name))

    def to_dict(self) -> Dict[str, Number]:
        return {
            "phase": self.phase,
            "am": self.am,
            "width": self.width,
            "freshift": self.freshift,
        }


@dataclass(frozen=True)
class ThreeQubitGradient:
    """One item in the Appendix A ``pulse.gradient`` array."""

    value: Number
    delay: int
    path: int

    def __post_init__(self) -> None:
        _require_number("value", self.value)
        _require_integer("delay", self.delay)
        _require_integer("path", self.path)

    def to_dict(self) -> Dict[str, Number]:
        return {"value": self.value, "delay": self.delay, "path": self.path}


@dataclass(frozen=True)
class ThreeQubitPulseSequence:
    """Three-qubit pulse container using the exact ``hPulse`` key."""

    h_pulse: Sequence[ThreeQubitPulse]
    gradient: Sequence[ThreeQubitGradient] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "h_pulse", tuple(self.h_pulse))
        object.__setattr__(self, "gradient", tuple(self.gradient))
        if not all(isinstance(item, ThreeQubitPulse) for item in self.h_pulse):
            raise ValueError("h_pulse must contain ThreeQubitPulse objects")
        if not all(isinstance(item, ThreeQubitGradient) for item in self.gradient):
            raise ValueError("gradient must contain ThreeQubitGradient objects")

    def to_dict(self, *, include_gradient: bool = True) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "hPulse": [item.to_dict() for item in self.h_pulse]
        }
        if include_gradient:
            result["gradient"] = [item.to_dict() for item in self.gradient]
        return result


@dataclass(frozen=True)
class ThreeQubitPhysicalCustomParameters:
    """Appendix A.4.1 physical-layer custom measurement parameters."""

    TASK_TYPE: ClassVar[str] = PHYSICAL_TASK_TYPE
    COMPUTE_TYPE: ClassVar[int] = 0

    fre_demo: int
    fre_shift: int
    pulse: ThreeQubitPulseSequence
    calc_matrix: bool
    relaxation_time: Number
    sample_count: int
    sample_delay: int
    sample_fre: SampleFrequencyHz
    sample_qubit: Sequence[int]
    make_pps: bool

    def __post_init__(self) -> None:
        for name in ("fre_demo", "fre_shift", "sample_count", "sample_delay", "sample_fre"):
            _require_integer(name, getattr(self, name))
        validate_sample_frequency(self.sample_fre)
        _require_number("relaxation_time", self.relaxation_time)
        _require_boolean("calc_matrix", self.calc_matrix)
        _require_boolean("make_pps", self.make_pps)
        object.__setattr__(self, "sample_qubit", _validate_sample_qubits(self.sample_qubit))
        if not isinstance(self.pulse, ThreeQubitPulseSequence):
            raise ValueError("pulse must be a ThreeQubitPulseSequence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freDemo": self.fre_demo,
            "freShift": self.fre_shift,
            "pulse": self.pulse.to_dict(),
            "calcMatrix": self.calc_matrix,
            "compute_type": self.COMPUTE_TYPE,
            "relaxation_time": self.relaxation_time,
            "sampleCount": self.sample_count,
            "sampleDelay": self.sample_delay,
            "sampleFre": self.sample_fre,
            "sampleQubit": list(self.sample_qubit),
            "makePps": self.make_pps,
        }


@dataclass(frozen=True)
class ThreeQubitPhysicalPauliParameters:
    """Appendix A.4.2 physical-layer Pauli component parameters."""

    TASK_TYPE: ClassVar[str] = PHYSICAL_TASK_TYPE
    COMPUTE_TYPE: ClassVar[int] = 1

    fre_demo: int
    fre_shift: int
    pulse: ThreeQubitPulseSequence
    calc_matrix: bool
    relaxation_time: Number
    step_list: Sequence[int]
    sample_path: int
    make_pps: bool

    def __post_init__(self) -> None:
        _require_integer("fre_demo", self.fre_demo)
        _require_integer("fre_shift", self.fre_shift)
        _require_integer("sample_path", self.sample_path)
        _require_number("relaxation_time", self.relaxation_time)
        _require_boolean("calc_matrix", self.calc_matrix)
        _require_boolean("make_pps", self.make_pps)
        steps = tuple(self.step_list)
        if not steps:
            raise ValueError("stepList must contain at least one Pauli measurement scheme")
        invalid = [step for step in steps if step not in THREE_QUBIT_PAULI_STEPS]
        if invalid:
            raise ValueError(
                f"stepList contains unsupported values {invalid}; "
                "valid values are 1, 2, 4, 7, 8, 9, and 10"
            )
        object.__setattr__(self, "step_list", steps)
        if not isinstance(self.pulse, ThreeQubitPulseSequence):
            raise ValueError("pulse must be a ThreeQubitPulseSequence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freDemo": self.fre_demo,
            "freShift": self.fre_shift,
            "pulse": self.pulse.to_dict(),
            "calcMatrix": self.calc_matrix,
            "compute_type": self.COMPUTE_TYPE,
            "relaxation_time": self.relaxation_time,
            "stepList": list(self.step_list),
            "samplePath": self.sample_path,
            "makePps": self.make_pps,
        }


@dataclass(frozen=True)
class ThreeQubitPhysicalTomographyParameters:
    """Appendix A.4.3 physical-layer state reconstruction parameters."""

    TASK_TYPE: ClassVar[str] = PHYSICAL_TASK_TYPE
    COMPUTE_TYPE: ClassVar[int] = 2

    fre_demo: int
    fre_shift: int
    pulse: ThreeQubitPulseSequence
    calc_matrix: bool
    relaxation_time: Number
    sample_qubit: Sequence[int]
    make_pps: bool

    def __post_init__(self) -> None:
        _require_integer("fre_demo", self.fre_demo)
        _require_integer("fre_shift", self.fre_shift)
        _require_number("relaxation_time", self.relaxation_time)
        _require_boolean("calc_matrix", self.calc_matrix)
        _require_boolean("make_pps", self.make_pps)
        object.__setattr__(self, "sample_qubit", _validate_sample_qubits(self.sample_qubit))
        if not isinstance(self.pulse, ThreeQubitPulseSequence):
            raise ValueError("pulse must be a ThreeQubitPulseSequence")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freDemo": self.fre_demo,
            "freShift": self.fre_shift,
            "pulse": self.pulse.to_dict(),
            "calcMatrix": self.calc_matrix,
            "compute_type": self.COMPUTE_TYPE,
            "relaxation_time": self.relaxation_time,
            "sampleQubit": list(self.sample_qubit),
            "makePps": self.make_pps,
        }


@dataclass(frozen=True)
class ThreeQubitCircuitItem:
    """One Appendix A.6/A.7 circuit item using zero-based circuit indexes."""

    type: str
    qubit_index: int
    timeslot: int
    angle: Number = 0.0
    delay: Number = 0.0
    control_qubit: int = -1
    control_qubit2: int = -1
    belong_qubit: int = -1
    customtype: str = ""

    def __post_init__(self) -> None:
        if self.type not in THREE_QUBIT_GATE_TYPES:
            raise ValueError(f"Unsupported three-qubit gate type: {self.type}")
        _validate_circuit_index("qubitIndex", self.qubit_index, allow_absent=False)
        _validate_circuit_index("controlQubit", self.control_qubit, allow_absent=True)
        _validate_circuit_index("controlQubit2", self.control_qubit2, allow_absent=True)
        _validate_circuit_index("belongQubit", self.belong_qubit, allow_absent=True)
        _require_integer("timeslot", self.timeslot)
        if self.timeslot < 0:
            raise ValueError("timeslot must be zero or greater")
        _require_number("angle", self.angle)
        _require_number("delay", self.delay)
        if not isinstance(self.customtype, str):
            raise ValueError("customtype must be a string")
        if self.type == "Customized" and not self.customtype:
            raise ValueError("Customized gates require a non-empty customtype")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "angle": self.angle,
            "controlQubit": self.control_qubit,
            "controlQubit2": self.control_qubit2,
            "delay": self.delay,
            "qubitIndex": self.qubit_index,
            "timeslot": self.timeslot,
            "type": self.type,
            "belongQubit": self.belong_qubit,
            "customtype": self.customtype,
        }


def _validate_circuit(items: Sequence[ThreeQubitCircuitItem]) -> Tuple[ThreeQubitCircuitItem, ...]:
    result = tuple(items)
    if not result:
        raise ValueError("circuit must contain at least one item")
    if not all(isinstance(item, ThreeQubitCircuitItem) for item in result):
        raise ValueError("circuit must contain ThreeQubitCircuitItem objects")
    return result


@dataclass(frozen=True)
class ThreeQubitCircuitPulseParameters:
    """Appendix A.5 circuit-layer test-pulse parameters."""

    TASK_TYPE: ClassVar[str] = CIRCUIT_PULSE_TASK_TYPE

    pulse: ThreeQubitPulseSequence
    calc_matrix: bool
    sample_path: int
    sample_qubit: Sequence[int]
    repeat: int

    def __post_init__(self) -> None:
        if not isinstance(self.pulse, ThreeQubitPulseSequence):
            raise ValueError("pulse must be a ThreeQubitPulseSequence")
        _require_integer("sample_path", self.sample_path)
        _require_integer("repeat", self.repeat)
        _require_boolean("calc_matrix", self.calc_matrix)
        object.__setattr__(self, "sample_qubit", _validate_sample_qubits(self.sample_qubit))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pulse": self.pulse.to_dict(include_gradient=False),
            "calcMatrix": self.calc_matrix,
            "samplePath": self.sample_path,
            "sampleQubit": list(self.sample_qubit),
            "repeat": self.repeat,
        }


@dataclass(frozen=True)
class ThreeQubitCircuitParameters:
    """Appendix A.6 circuit-layer quantum circuit parameters."""

    TASK_TYPE: ClassVar[str] = CIRCUIT_TASK_TYPE

    circuit: Sequence[ThreeQubitCircuitItem]
    relaxation_time: Number
    calc_matrix: bool
    sample_path: int
    sample_qubit: Sequence[int]
    repeat: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "circuit", _validate_circuit(self.circuit))
        object.__setattr__(self, "sample_qubit", _validate_sample_qubits(self.sample_qubit))
        _require_number("relaxation_time", self.relaxation_time)
        _require_integer("sample_path", self.sample_path)
        _require_integer("repeat", self.repeat)
        _require_boolean("calc_matrix", self.calc_matrix)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circuit": [item.to_dict() for item in self.circuit],
            "relaxation_time": self.relaxation_time,
            "calcMatrix": self.calc_matrix,
            "samplePath": self.sample_path,
            "sampleQubit": list(self.sample_qubit),
            "repeat": self.repeat,
        }


@dataclass(frozen=True)
class ThreeQubitMixingCircuitParameters:
    """Appendix A.7 classical-quantum mixing circuit parameters."""

    TASK_TYPE: ClassVar[str] = MIXING_CIRCUIT_TASK_TYPE

    circuit: Sequence[ThreeQubitCircuitItem]
    sample_path: int
    sample_qubit: Sequence[int]
    repeat: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "circuit", _validate_circuit(self.circuit))
        object.__setattr__(self, "sample_qubit", _validate_sample_qubits(self.sample_qubit))
        _require_integer("sample_path", self.sample_path)
        _require_integer("repeat", self.repeat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circuit": [item.to_dict() for item in self.circuit],
            "samplePath": self.sample_path,
            "sampleQubit": list(self.sample_qubit),
            "repeat": self.repeat,
        }


THREE_QUBIT_PARAMETER_TYPES = (
    ThreeQubitPhysicalCustomParameters,
    ThreeQubitPhysicalPauliParameters,
    ThreeQubitPhysicalTomographyParameters,
    ThreeQubitCircuitPulseParameters,
    ThreeQubitCircuitParameters,
    ThreeQubitMixingCircuitParameters,
)


def serialize_three_qubit_extra(
    awg_files: Mapping[str, Union[str, Mapping[str, Any]]],
) -> str:
    """Serialize Appendix A.8's map-of-JSON-text ``Task.extra`` structure."""

    if not isinstance(awg_files, Mapping):
        raise ValueError("awg_files must be a mapping of file names to AWG JSON")
    encoded: Dict[str, str] = {}
    for filename, value in awg_files.items():
        if not isinstance(filename, str) or not filename:
            raise ValueError("AWG file names must be non-empty strings")
        if isinstance(value, Mapping):
            text = _json_text(value)
        elif isinstance(value, str):
            text = value
        else:
            raise ValueError("AWG values must be JSON text or mapping objects")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"AWG value for {filename!r} is not valid JSON text") from exc
        if not isinstance(decoded, dict):
            raise ValueError(f"AWG value for {filename!r} must encode a JSON object")
        encoded[filename] = text
    return _json_text(encoded)


def build_three_qubit_task(
    parameters: Any,
    *,
    task_id: str,
    device_id: str,
    name: str = "",
    account: Optional[str] = None,
    create_time: Optional[int] = None,
    custom_awg_files: Optional[Mapping[str, Union[str, Mapping[str, Any]]]] = None,
) -> Task:
    """Build a protocol ``Task`` with correctly nested params and extra JSON."""

    if not isinstance(parameters, THREE_QUBIT_PARAMETER_TYPES):
        raise TypeError("parameters must be one of the public three-qubit parameter models")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("task_id must be a non-empty string")
    if not isinstance(device_id, str) or not device_id:
        raise ValueError("device_id must be a non-empty string")
    if create_time is None:
        create_time = int(time.time() * 1000)
    _require_integer("create_time", create_time)
    extra = (
        serialize_three_qubit_extra(custom_awg_files)
        if custom_awg_files is not None
        else None
    )
    task = Task(
        type=parameters.TASK_TYPE,
        id=task_id,
        device_id=device_id,
        params=_json_text(parameters.to_dict()),
        create_time=create_time,
        account=account,
        name=name,
        extra=extra,
    )
    task.validate_submission()
    return task


__all__ = [
    "PHYSICAL_TASK_TYPE",
    "CIRCUIT_PULSE_TASK_TYPE",
    "CIRCUIT_TASK_TYPE",
    "MIXING_CIRCUIT_TASK_TYPE",
    "THREE_QUBIT_GATE_TYPES",
    "THREE_QUBIT_PAULI_STEPS",
    "ThreeQubitPulse",
    "ThreeQubitGradient",
    "ThreeQubitPulseSequence",
    "ThreeQubitPhysicalCustomParameters",
    "ThreeQubitPhysicalPauliParameters",
    "ThreeQubitPhysicalTomographyParameters",
    "ThreeQubitCircuitItem",
    "ThreeQubitCircuitPulseParameters",
    "ThreeQubitCircuitParameters",
    "ThreeQubitMixingCircuitParameters",
    "serialize_three_qubit_extra",
    "build_three_qubit_task",
]
