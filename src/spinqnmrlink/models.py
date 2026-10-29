# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Public scientific models and validated protocol parameter adapters.

Parameter classes are derived from the device serializers so their bounds and
defaults have one source of truth. Only snake_case names are accepted publicly.
"""

from __future__ import annotations

import dataclasses
import importlib
import re
from copy import deepcopy
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator, model_validator

from ._core.parameter_choices import validate_sample_frequency
from .catalogue import _preset_key, get_experiment


class ValueModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, allow_inf_nan=False, strict=True
    )


class Pulse(ValueModel):
    """RF pulse: microseconds, percent, degrees and hertz."""

    channel: int = Field(default=0, ge=0, le=2, strict=True)
    width_us: float = Field(default=0, ge=0, le=20_000_000)
    amplitude_percent: float = Field(default=0, ge=0, le=100)
    phase_deg: float = 0
    detuning_hz: float = Field(default=0, ge=-10000, le=10000)


class Gradient(ValueModel):
    """Gradient pulse: voltage in volts and duration in microseconds."""

    path: int = Field(default=1, ge=0, le=13, strict=True)
    voltage_v: float = Field(default=0, ge=-1, le=1)
    duration_us: float = Field(default=0, ge=0, le=20_000_000)


class Gate(ValueModel):
    """Quantum gate with zero-based qubit indices and rotation in degrees."""

    type: str = "X"
    target: int = Field(default=0, ge=0, le=2, strict=True)
    control: int = Field(default=-1, ge=-1, le=2, strict=True)
    control2: int = Field(default=-1, ge=-1, le=2, strict=True)
    angle_deg: float = 0
    delay_us: float = Field(default=0, ge=0)
    timeslot: int = Field(default=0, ge=0, strict=True)
    belong_qubit: int = Field(default=-1, ge=-1, le=2, strict=True)
    custom_type: str = ""


class Circuit(ValueModel):
    """Circuit definition shared by both devices; capabilities remain device-specific."""

    qubits: int = Field(ge=1, le=3, strict=True)
    gates: List[Gate] = Field(default_factory=list)
    measures: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_circuit(self):
        supported = {
            "H",
            "I",
            "X",
            "Y",
            "Z",
            "X90",
            "Y90",
            "Z90",
            "Rx",
            "Ry",
            "Rz",
            "T",
            "Td",
            "S",
            "Sd",
            "CNOT",
            "CZ",
            "CCNOT",
            "CCZ",
            "Customized",
        }
        for gate in self.gates:
            if gate.type not in supported:
                raise ValueError("unsupported gate type")
            if gate.type == "Customized" and not gate.custom_type:
                raise ValueError("Customized gates require custom_type")
            indices = [gate.target]
            if gate.type in ("CNOT", "CZ", "CCNOT", "CCZ"):
                indices.append(gate.control)
            if gate.type in ("CCNOT", "CCZ"):
                indices.append(gate.control2)
            if any(x < 0 or x >= self.qubits for x in indices) or len(set(indices)) != len(indices):
                raise ValueError("gate indices must be distinct and inside the circuit")
        if self.measures is not None and (
            len(self.measures) != self.qubits
            or any(type(x) is not int or x not in (0, 1) for x in self.measures)
            or not any(self.measures)
        ):
            raise ValueError("measures must enable at least one qubit with one 0/1 value per qubit")
        return self


_NAMES = {
    "makePps": "make_pps",
    "usingAwgFile": "using_awg_file",
    "sampleFre": "sample_frequency",
    "sampleCount": "sample_count",
    "sampleDelay": "sample_delay_us",
    "samplePath": "sample_path",
    "sampleQubit": "sample_qubits",
    "stepList": "step_list",
    "calcMatrix": "calc_matrix",
    "freShift": "frequency_shift",
    "freDemo": "frequency_demo",
    "h_freShift": "h_frequency_shift",
    "p_freShift": "p_frequency_shift",
    "h_freDemo": "h_frequency_demo",
    "p_freDemo": "p_frequency_demo",
    "relaxation_delay": "relaxation_seconds",
    "relaxation_time": "relaxation_seconds",
    "sample_fre": "sample_frequency",
    "sample_delay": "sample_delay_us",
    "sample_qubit": "sample_qubits",
    "qubitIndex": "target",
    "qubit_index": "target",
    "controlQubit": "control",
    "control_qubit": "control",
    "controlQubit2": "control2",
    "control_qubit2": "control2",
    "angle": "angle_deg",
    "delay": "delay_us",
    "width": "width_us",
    "am": "amplitude_percent",
    "freshift": "detuning_hz",
    "phase": "phase_deg",
}
_CACHE: Dict[type, type] = {}


def _name(field):
    return _NAMES.get(field, re.sub(r"(?<!^)(?=[A-Z])", "_", field).lower())


class ExperimentParameters(ValueModel):
    """Typed parameter object. to_wire() validates nested values without connecting."""

    _native_type: ClassVar[Any] = None
    _field_map: ClassVar[Dict[str, str]] = {}
    _field_types: ClassVar[Dict[str, Any]] = {}

    @field_validator("sample_frequency", mode="before", check_fields=False)
    @classmethod
    def validate_frequency_choice(cls, value):
        return validate_sample_frequency(value)

    def to_native(self):
        # Lists and nested models can be mutated after preparation. Revalidate
        # their current public shape before applying protocol conversions.
        validated = type(self).model_validate(self.model_dump(mode="python"))
        values = {}
        for public, native in self._field_map.items():
            if getattr(validated, public) is None and not dataclasses.is_dataclass(
                self._native_type
            ):
                info = self._native_type.model_fields[native]
                if info.default is None:
                    continue
            value = _to_native(
                getattr(validated, public), self._field_types[native], self._native_type.__module__
            )
            if native == "relaxation_delay" and ".triangulum." in self._native_type.__module__:
                value *= 1_000_000
            if native == "sample_qubit" and "three_qubit_models" in self._native_type.__module__:
                if (
                    not value
                    or len(set(value)) != len(value)
                    or any(type(x) is not int or x not in (0, 1, 2) for x in value)
                ):
                    raise ValueError(
                        "sample_qubits must contain distinct zero-based indices from 0 to 2"
                    )
                value = [x + 1 for x in value]
            values[native] = value
        result = self._native_type(**values)
        if self._native_type.__module__.endswith("triangulum.experiment.exp_physical_layer"):
            if any(pulse.path != 0 for pulse in result.pulses):
                raise ValueError("Triangulum physical experiments only accept channel 0 pulses")
        if (
            hasattr(result, "circuit")
            and result.circuit is not None
            and hasattr(result, "set_circuit")
        ):
            result.set_circuit(result.circuit)
        return result

    def to_wire(self):
        native = self.to_native()
        return (
            cast(Any, native).to_dict()
            if dataclasses.is_dataclass(native)
            else native.get_parameters()
        )


def _public_type(annotation):
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union:
        return Union[tuple(_public_type(x) for x in args)]
    if origin is not None and args:
        if origin in (list, tuple) or str(origin).endswith("Sequence'>"):
            if isinstance(args[0], type) and args[0].__name__ == "ThreeQubitCircuitItem":
                return Circuit
            return cast(Any, List)[_public_type(args[0])]
        return annotation
    if isinstance(annotation, type) and ".spinqnmrlink" not in annotation.__module__:
        if (
            annotation.__name__ in ("Pulse", "ThreeQubitPulse")
            and "_backends" in annotation.__module__
        ):
            return Pulse
        if (
            annotation.__name__ in ("Gradient", "ThreeQubitGradient")
            and "_backends" in annotation.__module__
        ):
            return Gradient
        if annotation.__name__ == "Circuit" and "_backends" in annotation.__module__:
            return Circuit
        if "_backends" in annotation.__module__ and dataclasses.is_dataclass(annotation):
            return _parameter_class(annotation)
    return annotation


def _parameter_class(native):
    if native in _CACHE:
        return _CACHE[native]
    definitions = {}
    types = get_type_hints(native)
    field_map = {}
    if dataclasses.is_dataclass(native):
        fields = dataclasses.fields(native)
        for f in fields:
            public = _name(f.name)
            field_map[public] = f.name
            default = ... if f.default is dataclasses.MISSING else deepcopy(f.default)
            if isinstance(default, tuple):
                default = list(default)
            if f.default_factory is not dataclasses.MISSING:
                default = Field(default_factory=f.default_factory)
            definitions[public] = (_public_type(types[f.name]), default)
    else:
        for field, info in native.model_fields.items():
            public = _name(field)
            field_map[public] = field
            types[field] = info.annotation
            copied = deepcopy(info)
            copied.alias = copied.validation_alias = copied.serialization_alias = None
            if field == "relaxation_delay" and ".triangulum." in native.__module__:
                copied = Field(
                    default=info.default / 1_000_000,
                    ge=0,
                    le=25,
                    description="Relaxation delay in seconds (wire uses microseconds).",
                )
            annotation = _public_type(info.annotation)
            if copied.default is None:
                annotation = Optional[annotation]
            definitions[public] = (annotation, copied)
    prefix = "Triangulum" if ".triangulum." in native.__module__ else "Lab"
    classname = prefix + (
        native.__name__[3:] if native.__name__.startswith("Exp") else native.__name__
    )
    model = create_model(
        classname, __base__=ExperimentParameters, __module__=__name__, **definitions
    )
    model._native_type = native
    model._field_map = field_map
    model._field_types = types
    _CACHE[native] = model
    globals()[classname] = model
    return model


def _from_native(value):
    if type(value).__name__ == "ThreeQubitPulse":
        return Pulse(
            channel=0,
            width_us=value.width,
            amplitude_percent=value.am,
            phase_deg=value.phase,
            detuning_hz=value.freshift,
        )
    if type(value).__name__ == "ThreeQubitGradient":
        return Gradient(path=value.path, voltage_v=value.value, duration_us=value.delay)
    if isinstance(value, BaseModel) and value.__class__.__name__ == "Pulse":
        return Pulse(
            channel=value.path,
            width_us=value.width,
            amplitude_percent=value.amplitude,
            phase_deg=value.phase,
            detuning_hz=value.detuning,
        )
    if isinstance(value, BaseModel) and value.__class__.__name__ == "Gradient":
        return Gradient(path=value.path, voltage_v=value.voltage, duration_us=value.duration)
    if value.__class__.__name__ == "Circuit" and "_backends" in value.__class__.__module__:
        gates = value.gates if hasattr(value, "gates") else value.circuit
        return Circuit(
            qubits=value.qubits_num,
            gates=[
                Gate(
                    type=x.type,
                    target=x.qubitIndex,
                    control=x.controlQubit,
                    control2=x.controlQubit2,
                    angle_deg=x.angle,
                    delay_us=x.delay,
                    timeslot=x.timeslot,
                )
                for x in gates
            ],
            measures=getattr(value, "measures", None),
        )
    if (
        isinstance(value, BaseModel) or dataclasses.is_dataclass(value)
    ) and "_backends" in value.__class__.__module__:
        cls = _parameter_class(type(value))
        values = {
            public: _from_native(getattr(value, native))
            for public, native in cls._field_map.items()
        }
        if (
            "relaxation_delay" in cls._field_map.values()
            and ".triangulum." in type(value).__module__
        ):
            values["relaxation_seconds"] /= 1_000_000
        if (
            "sample_qubit" in cls._field_map.values()
            and "three_qubit_models" in type(value).__module__
        ):
            values["sample_qubits"] = [x - 1 for x in values["sample_qubits"]]
        return cls(**values)
    if isinstance(value, (tuple, list)):
        if value and type(value[0]).__name__ == "ThreeQubitCircuitItem":
            return Circuit(
                qubits=3,
                gates=[
                    Gate(
                        type=x.type,
                        target=x.qubit_index,
                        control=x.control_qubit,
                        control2=x.control_qubit2,
                        angle_deg=x.angle,
                        delay_us=x.delay,
                        timeslot=x.timeslot,
                        belong_qubit=x.belong_qubit,
                        custom_type=x.customtype,
                    )
                    for x in value
                ],
            )
        return [_from_native(x) for x in value]
    if isinstance(value, dict):
        return {k: _from_native(v) for k, v in value.items()}
    return value


def _to_native(value, annotation, module):
    if isinstance(value, Pulse):
        if "three_qubit_models" in module:
            from ._backends.lab.experiment.three_qubit_models import ThreeQubitPulse

            if value.channel != 0:
                raise ValueError("Lab THREE pulse.hPulse accepts channel 0 only")
            return ThreeQubitPulse(
                phase=value.phase_deg,
                am=value.amplitude_percent,
                width=value.width_us,
                freshift=value.detuning_hz,
            )
        backend = "triangulum" if ".triangulum." in module else "lab"
        cls = importlib.import_module("spinqnmrlink._backends." + backend + ".utils.pulse").Pulse
        return cls(
            path=value.channel,
            width=value.width_us,
            amplitude=value.amplitude_percent,
            phase=value.phase_deg,
            detuning=value.detuning_hz,
        )
    if isinstance(value, Gradient):
        if "three_qubit_models" in module:
            from ._backends.lab.experiment.three_qubit_models import ThreeQubitGradient

            if not float(value.duration_us).is_integer():
                raise ValueError("Lab THREE gradient durations require integer microseconds")
            return ThreeQubitGradient(
                value=value.voltage_v, delay=int(value.duration_us), path=value.path
            )
        backend = "triangulum" if ".triangulum." in module else "lab"
        cls = importlib.import_module("spinqnmrlink._backends." + backend + ".utils.pulse").Gradient
        return cls(path=value.path, voltage=value.voltage_v, duration=value.duration_us)
    if isinstance(value, Circuit):
        if "three_qubit_models" in module:
            from ._backends.lab.experiment.three_qubit_models import ThreeQubitCircuitItem

            if value.qubits != 3:
                raise ValueError("Lab THREE circuits require exactly three qubits")
            if value.measures is not None and value.measures != [1, 1, 1]:
                raise ValueError("Select Lab THREE acquisitions with sample_qubits")
            return [
                ThreeQubitCircuitItem(
                    type=x.type,
                    qubit_index=x.target,
                    control_qubit=x.control,
                    control_qubit2=x.control2,
                    angle=x.angle_deg,
                    delay=x.delay_us,
                    timeslot=x.timeslot,
                    belong_qubit=x.belong_qubit,
                    customtype=x.custom_type,
                )
                for x in value.gates
            ]
        backend = "triangulum" if ".triangulum." in module else "lab"
        pkg = importlib.import_module("spinqnmrlink._backends." + backend)
        if backend == "lab" and value.qubits > 2:
            raise ValueError("Lab TWO circuits support at most two qubits")
        circuit = pkg.Circuit(value.qubits)
        if hasattr(circuit, "set_measures"):
            circuit.set_measures(value.measures or [1] * value.qubits)
        elif value.measures is not None and value.measures != [1] * value.qubits:
            raise ValueError("Lab TWO does not support selective circuit measurement")
        for item in value.gates:
            circuit << pkg.Gate(
                type=item.type,
                qubitIndex=item.target,
                controlQubit=item.control,
                controlQubit2=item.control2,
                angle=item.angle_deg,
                delay=item.delay_us,
                timeslot=item.timeslot,
            )
        return circuit
    if isinstance(value, ExperimentParameters):
        return value.to_native()
    if isinstance(value, (list, tuple)):
        args = get_args(annotation)
        return [_to_native(x, args[0] if args else Any, module) for x in value]
    return value


def parameters_for(key: str) -> ExperimentParameters:
    """Return an independent typed reference preset; values require device calibration."""
    descriptor = get_experiment(key)
    preset_key = _preset_key(key)
    if descriptor.mode == "THREE":
        from ._core.lab_three_presets import get_lab_three_preset

        return _from_native(get_lab_three_preset(preset_key).build_parameters())
    if descriptor.device_type == "lab":
        from ._backends.lab.experiment.ExperimentManager import ExperimentManager as LabManager
        from ._core.lab_two_presets import get_lab_two_preset

        _, factory = LabManager()._get_experiment_class(cast(Any, descriptor.experiment_type))
        native = factory()
        get_lab_two_preset(preset_key).configure(native)
    else:
        from ._core.link_presets import get_link_preset

        native = get_link_preset(preset_key).build_parameters()
    return _from_native(native)


def __getattr__(name):
    """Resolve named public parameter types lazily, without device construction."""
    from .catalogue import list_experiments

    for descriptor in list_experiments():
        prefix = "Triangulum" if descriptor.device_type == "triangulum" else "Lab"
        native_name = descriptor.model
        public_name = prefix + (native_name[3:] if native_name.startswith("Exp") else native_name)
        if name == public_name:
            return type(parameters_for(descriptor.key))
    raise AttributeError("No public parameter model named {}".format(name))
