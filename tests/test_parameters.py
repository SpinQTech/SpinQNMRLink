import json
import threading
from pathlib import Path

import pytest

from spinqnmrlink import (
    Circuit,
    Gate,
    LabSettings,
    Pulse,
    SDKSettings,
    SpinQNMRLink,
    list_experiments,
    parameters_for,
)

BASELINE = json.loads(
    (Path(__file__).parent / "fixtures/protocol_parameters.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("key", BASELINE)
def test_all_35_wire_payloads_match_protocol_reference(key):
    parameters = parameters_for(key)
    assert parameters.to_wire() == BASELINE[key]
    assert all(name == name.lower() for name in type(parameters).model_fields)
    restored = type(parameters).model_validate_json(parameters.model_dump_json())
    assert restored.to_wire() == BASELINE[key]


def test_construct_prepare_and_browse_do_not_start_threads_or_load_native_library():
    before = {t.ident for t in threading.enumerate()}
    with SpinQNMRLink(
        SDKSettings(lab=LabSettings(host="localhost", port=8181, account="test", password="test"))
    ) as sdk:
        device = sdk.device("lab")
        for entry in list_experiments("lab"):
            device.create_experiment(entry.key)
        assert device._client is None
        assert not device.is_ready
    assert before == {t.ident for t in threading.enumerate()}


def test_device_specific_acquisition_and_time_units():
    lab = parameters_for("lab.two.physical.custom")
    lab.sample_count = 16000
    with pytest.raises(ValueError):
        lab.to_wire()
    triangulum = parameters_for("triangulum.physical")
    triangulum.relaxation_seconds = 0.02
    assert triangulum.to_wire()["parameters"]["relaxation_time"] == 20000
    triangulum.sample_qubits = [1, 2]
    assert triangulum.to_wire()["parameters"]["sampleQubit"] == [1, 2]
    triangulum.pulses[0].channel = 1
    with pytest.raises(ValueError, match="channel 0"):
        triangulum.to_wire()
    lab = parameters_for("lab.two.physical.custom")
    lab.relaxation_seconds = 0.02
    assert lab.to_wire()["relaxation_time"] == 0.02


def test_nested_mutation_is_validated_before_submission():
    parameters = parameters_for("lab.two.rabi")
    parameters.pulses.append(Pulse(channel=2))
    with pytest.raises(ValueError):
        parameters.to_wire()
    with pytest.raises(ValueError):
        Circuit(qubits=2, gates=[Gate(type="CNOT", target=1, control=1)])
    with pytest.raises(ValueError):
        Pulse(width_us=float("nan"))


def test_spinecho_16000_sample_exception_does_not_apply_to_other_lab_tasks():
    spin_echo = parameters_for("lab.two.spin_echo")
    spin_echo.sample_count = 16000
    assert spin_echo.to_wire()["sampleCount"] == 16000
    dynamic = parameters_for("lab.two.dynamic_decoupling")
    dynamic.sample_count = 16000
    with pytest.raises(ValueError):
        dynamic.to_wire()


def test_presets_are_independent_and_unknown_keys_rejected():
    left = parameters_for("lab.two.rabi")
    right = parameters_for("lab.two.rabi")
    left.pulses[0].width_us = 70
    assert right.pulses[0].width_us == 40
    with pytest.raises(KeyError):
        parameters_for("lab.rabi")


def test_named_public_models_are_available_without_prior_factory_calls():
    from spinqnmrlink.models import LabRabiParameters

    parameters = parameters_for("lab.two.rabi")
    assert type(parameters) is LabRabiParameters
    assert (
        LabRabiParameters.model_validate_json(parameters.model_dump_json()).to_wire()
        == parameters.to_wire()
    )


def test_three_qubit_public_indices_convert_to_one_based_protocol_indices():
    parameters = parameters_for("lab.three.physical_custom")
    assert parameters.sample_qubits == [0, 1, 2]
    assert parameters.to_wire()["sampleQubit"] == [1, 2, 3]
    parameters.sample_qubits = [3]
    with pytest.raises(ValueError):
        parameters.to_wire()


def test_three_qubit_integer_fields_do_not_accept_booleans():
    parameters = parameters_for("lab.three.physical_custom")
    with pytest.raises(ValueError):
        parameters.sample_count = True


def test_common_circuit_definition_supports_lab_three_and_triangulum():
    circuit = Circuit(
        qubits=3,
        gates=[
            Gate(type="H", target=0),
            Gate(type="CCNOT", target=2, control=0, control2=1, timeslot=1),
        ],
    )
    lab = parameters_for("lab.three.circuit")
    lab.circuit = circuit
    assert lab.to_wire()["circuit"][1]["controlQubit2"] == 1
    triangulum = parameters_for("triangulum.circuit")
    triangulum.circuit = circuit
    assert triangulum.to_wire()["circuit"]["gates"][1]["type"] == "CCNOT"


def test_common_pulse_supports_lab_three_without_losing_channel_boundaries():
    parameters = parameters_for("lab.three.physical_custom")
    parameters.pulse.h_pulse = [Pulse(channel=0, width_us=150, amplitude_percent=80)]
    assert parameters.to_wire()["pulse"]["hPulse"][0]["width"] == 150
    parameters.pulse.h_pulse[0].channel = 1
    with pytest.raises(ValueError, match="channel 0"):
        parameters.to_wire()


def test_mutated_controlled_gate_is_revalidated_before_wire_conversion():
    parameters = parameters_for("lab.two.circuit.gates")
    parameters.circuit.gates[1].control = -1
    with pytest.raises(ValueError, match="gate indices"):
        parameters.to_wire()
