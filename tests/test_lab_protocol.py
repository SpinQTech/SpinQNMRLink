"""In-memory Lab protocol checks using the real backend, without sockets."""

import hashlib
import struct
from pathlib import Path

import pytest

from spinqnmrlink._backends.lab.connection.protocol import Protocol, ProtocolFrameError
from spinqnmrlink._backends.lab.spinqlablink import SpinQLabLink
from spinqnmrlink._backends.lab.utils.types import (
    ConnectionState,
    ExperimentState,
    MachineType,
    QubitMode,
)


@pytest.mark.parametrize("msg_id", (None, "", " \t"))
@pytest.mark.parametrize("transport", ("tcp", "websocket"))
def test_empty_business_frames_and_blank_message_ids_are_rejected(msg_id, transport):
    from spinqnmrlink._backends.lab.connection.message_pb2 import BaseMessage

    payload = b"" if msg_id is None else BaseMessage(msg_id=msg_id, json_data="{}").SerializeToString()
    protocol = Protocol()
    with pytest.raises(ProtocolFrameError):
        if transport == "tcp":
            protocol.deserialize_messages(struct.pack(">II", protocol.HEADER_MAGIC, len(payload)) + payload)
        else:
            protocol.deserialize_payload(payload)
    assert protocol.deserialize_messages(b"") == []


@pytest.mark.parametrize("using_pulse", (True, False))
def test_circuit_result_type_is_the_submitted_type(using_pulse):
    from spinqnmrlink import parameters_for
    from spinqnmrlink._backends.lab.experiment.exp_layer_circuit import ExpLayerCircuit

    parameters = parameters_for("lab.two.circuit.gates").to_native()
    parameters.using_pulse = using_pulse
    experiment = ExpLayerCircuit(parameters)
    expected = "EXP_LAYER_CIRCUIT_PULSE" if using_pulse else "EXP_LAYER_CIRCUIT_CIRCUIT"
    assert experiment.get_result()["type"] == expected
    assert experiment.get_experiment_parameter()["type"] == expected
    assert experiment.get_experiment_parameter()["type"] == expected
    parameters.using_pulse = not using_pulse
    assert experiment.get_result()["type"] == expected
    assert experiment.get_result()["type"] == expected


def test_regenerated_protobuf_preserves_original_message_and_field_schema():
    from google.protobuf.descriptor_pb2 import FileDescriptorProto

    from spinqnmrlink._backends.lab.connection import message_pb2

    descriptor = FileDescriptorProto.FromString(message_pb2.DESCRIPTOR.serialized_pb)
    descriptor.name = ""
    descriptor.ClearField("source_code_info")
    expected = (Path(__file__).parent / "fixtures/proto_schema.sha256").read_text()
    assert hashlib.sha256(descriptor.SerializeToString(deterministic=True)).hexdigest() == expected


@pytest.fixture
def backend():
    client = SpinQLabLink("localhost", account="test-account", password="test-password")
    client.is_connected = client.is_logged_in = True
    client.connection_state = ConnectionState.READY
    client.session_id = "unit-test-session"
    client.connection.send = lambda data: True
    yield client
    client.disconnect(timeout=2)


def test_framing_preserves_mode_and_handles_split_and_coalesced_frames():
    protocol = Protocol()
    metadata = dict(sequence_id=1, timestamp=123, account="test", session_id="test")
    first = protocol.serialize_message("test", metadata, {"value": 1})
    second = protocol.serialize_message("test", metadata, {"value": 2}, qubit_mode=QubitMode.THREE)
    decoder = Protocol()
    assert decoder.deserialize_messages(first[:5]) == []
    messages = decoder.deserialize_messages(first[5:] + second)
    assert len(messages) == 2
    assert messages[0]["json_data"] == {"value": 1}
    assert messages[1]["qubit_mode"] == QubitMode.THREE
    with pytest.raises(ProtocolFrameError):
        Protocol().deserialize_messages(b"invalid-header-bytes")


def test_duplicate_acknowledgement_is_ignored_and_not_reapplied(backend):
    sequence = backend._send_message(
        MachineType.MSG_REQ_ADD_EXP_TASK_REQ,
        {"id": "unit-task"},
        expected_response_msg_id=MachineType.MSG_RES_ADD_EXP_TASK_RES,
        target_qubit_mode=QubitMode.TWO,
        task_id="unit-task",
    )
    envelope = {
        "metadata": {"sequence_id": sequence, "session_id": backend.session_id},
        "msg_id": MachineType.MSG_RES_ADD_EXP_TASK_RES,
        "qubit_mode": 0,
    }
    response = {"code": 0, "taskId": "unit-task", "message": "accepted"}
    backend._handle_business_response(response, envelope)
    backend._handle_business_response(response, envelope)
    assert backend.wait_for_request_response(sequence, timeout=0.2).success
    assert backend._duplicate_response_count == 1
    assert not backend._pending_requests


def test_result_processing_failure_cannot_be_overwritten_as_completed(backend):
    experiment, _ = backend.register_experiment("EXP_RABI", qubit_mode=QubitMode.TWO)
    payload = {"taskId": experiment.id, "data": {"state": "COMPLETED"}}

    def broken_decoder(data):
        raise ValueError("invalid measurement shape")

    with pytest.raises(ValueError):
        backend._call_experiment_handler(
            broken_decoder, MachineType.MSG_POST_EXP_FINISHED, payload, QubitMode.TWO
        )
    assert experiment.state == ExperimentState.FAILED
    assert "invalid measurement shape" in experiment.processing_error


def test_pending_requests_wake_as_unknown_on_disconnect(backend):
    from spinqnmrlink._backends.lab.connection.request import RequestOutcomeUnknownError

    sequence = backend._send_message(
        MachineType.MSG_REQ_ADD_EXP_TASK_REQ,
        {"id": "unit-task"},
        expected_response_msg_id=MachineType.MSG_RES_ADD_EXP_TASK_RES,
        target_qubit_mode=QubitMode.TWO,
        task_id="unit-task",
    )
    backend.disconnect(timeout=2)
    with pytest.raises(RequestOutcomeUnknownError):
        backend.wait_for_request_response(sequence, timeout=0.2)


@pytest.mark.parametrize("source", ("started", "queue"))
def test_start_timestamp_matches_task_and_duplicate_notifications_do_not_reset(backend, monkeypatch, source):
    from types import SimpleNamespace

    from spinqnmrlink._core import task_timing

    clock = SimpleNamespace(seconds=40)
    monkeypatch.setattr(task_timing, "time", SimpleNamespace(monotonic=lambda: clock.seconds))
    experiment, _ = backend.register_experiment("EXP_RABI", qubit_mode=QubitMode.TWO)

    def started(task_id):
        if source == "started":
            backend._call_experiment_handler(lambda _: None, MachineType.MSG_POST_EXP_STARTED,
                                            {"taskId": task_id}, QubitMode.TWO)
        else:
            backend._handle_exp_queue_update_post(
                {"queue": [{"id": task_id, "state": "RUNNING"}]}, {"qubit_mode": 0})

    started("someone-else")
    assert getattr(experiment, "execution_started_monotonic", None) is None
    started(experiment.id)
    assert experiment.execution_started_monotonic == 40
    clock.seconds = 60
    started(experiment.id)
    assert experiment.execution_started_monotonic == 40


def test_public_lab_disconnect_event_retains_task_and_cleans_observers(backend, monkeypatch):
    import threading

    from spinqnmrlink import LabDevice, LabSettings

    monkeypatch.setattr(backend, "connect", lambda **kwargs: True)
    device = LabDevice(LabSettings(host="localhost", port=8181, account="test-account", password="test-password"),
                       backend_factory=lambda _: backend)
    observed = []
    notified = threading.Event()
    device.subscribe_disconnect(lambda event: (observed.append(event), notified.set()))
    device.open()
    experiment, _ = backend.register_experiment("EXP_RABI", qubit_mode=QubitMode.TWO)
    backend.connection._notify_disconnected("receive error: peer reset test-password")
    assert notified.wait(1)
    device.close()
    assert len(observed) == 1 and observed[0].task_ids == (experiment.id,)
    assert "test-password" not in device.last_disconnect_reason
    assert not device.is_ready


def test_accepted_lab_task_still_detects_silent_connection_while_queued(backend, monkeypatch):
    import time

    observed = []
    backend.set_disconnect_callback(lambda reason, details: observed.append(reason))
    experiment, _ = backend.register_experiment("EXP_RABI", qubit_mode=QubitMode.TWO)
    sequence = backend.run_experiment(qubit_mode=QubitMode.TWO)
    backend._handle_business_response(
        {"code": 0, "taskId": experiment.id},
        {"metadata": {"sequence_id": sequence, "session_id": backend.session_id},
         "msg_id": MachineType.MSG_RES_ADD_EXP_TASK_RES, "qubit_mode": 0},
    )
    assert backend.wait_for_request_response(sequence, timeout=0.2).success
    heartbeat = backend.heartbeat_manager
    monkeypatch.setattr(heartbeat, "_schedule_next_check", lambda: None)
    heartbeat._is_running = True
    heartbeat.last_server_activity_time = time.time() - 3600
    heartbeat._check_heartbeat_timeout()
    assert len(observed) == 1 and "timeout" in observed[0]
    assert not backend.is_connected
