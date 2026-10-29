"""Triangulum protocol fixtures and local transport doubles; no device measurements."""

import base64
import hashlib
import json
import queue
import socket
import struct
import threading
import time
import zlib

import pytest

from spinqnmrlink import (
    DeviceNotReadyError,
    ExperimentFailedError,
    ExperimentRejectedError,
    ExperimentTerminatedError,
    ExperimentTimeoutError,
    SubmissionOutcomeUnknownError,
    TriangulumDevice,
    TriangulumSettings,
    parameters_for,
)
from spinqnmrlink._backends.triangulum.protocol import ProtocolError, decode_message
from spinqnmrlink._backends.triangulum.session import TriangulumSession


def settings(**changes):
    return TriangulumSettings(
        host="127.0.0.1",
        port=55444,
        account="account-fixture",
        password="password-fixture",
        **changes,
    )


def finished(request, state="S"):
    circuit = request["msg_id"] == "push_task_request"
    result = {
        "msg_id": "task_finished_post" if circuit else "custom_task_finished_post",
        "task_id": request["task_id"],
        "task_state": state,
        "task_qubits": request["task_qubits"],
    }
    if state == "S":
        if circuit:
            count = 2 ** request["task_qubits"]
            matrix_count = count * count if request.get("calcMatrix", False) else count
            result["task_result"] = {
                "execution": [1.0] + [0.0] * (count - 1),
                "execution_matrix": {
                    "real": [1.0] + [0.0] * (matrix_count - 1), "imag": [0.0] * matrix_count,
                },
            }
        else:
            result["task_result"] = {
                "pauli": {"fixture": 0.5},
                "module": [1.0, 0.0],
                "real": [1.0, 0.0],
                "imag": [0.0, 0.0],
            }
            result["graph_result_compressed"] = [{"fidRe": [[0, 1]]}]
    return result


class ScriptedTransport:
    def __init__(self, settings, action=None, login_code=0):
        self.settings = settings
        self.action = action
        self.login_code = login_code
        self.received = queue.Queue()
        self.sent = []
        self.closed = False

    def open(self, timeout):
        self.closed = False

    def emit(self, message):
        self.received.put(json.dumps(message))

    def send(self, text):
        value = json.loads(text)
        self.sent.append(value)
        if value["msg_id"] == "user_login_request":
            self.emit(
                {
                    "msg_id": "user_login_response",
                    "return_code": self.login_code,
                    "session_id": "session-fixture",
                }
            )
        elif value["msg_id"] == "user_logout_request":
            self.emit({"msg_id": "user_logout_response", "return_code": 0})
        elif value["msg_id"] == "heartbeat":
            self.emit({"msg_id": "heartbeat"})
        elif self.action:
            self.action(self, value)
        else:
            self.ack(value)
            self.emit(finished(value))

    def ack(self, request, code=0, identifier=None):
        self.emit(
            {
                "msg_id": "push_task_response"
                if request["msg_id"] == "push_task_request"
                else "push_custom_task_response",
                "return_code": code,
                "task_id": request["task_id"] if identifier is None else identifier,
            }
        )

    def receive(self):
        try:
            value = self.received.get(timeout=0.01)
        except queue.Empty:
            return None
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        self.closed = True
        self.received.put(ConnectionError("closed fixture"))


def device_and_transport(action=None, login_code=0, **changes):
    config = settings(**changes)
    transport = ScriptedTransport(config, action, login_code)
    client = TriangulumSession(config, transport_factory=lambda _: transport)
    device = TriangulumDevice(config, backend_factory=lambda _: client)
    return device, client, transport


@pytest.mark.parametrize("calc_matrix", (True, False))
def test_circuit_matrix_mode_is_sent_at_envelope_level_and_controls_decoding(calc_matrix):
    parameters = parameters_for("triangulum.circuit")
    parameters.calc_matrix = calc_matrix

    def action(transport, request):
        assert request["calcMatrix"] is calc_matrix
        assert "calcMatrix" not in request["task_gates"]
        transport.ack(request)
        response = finished(request)
        size = 64 if calc_matrix else 8
        response["task_result"]["execution_matrix"] = {
            "real": [1.0] + [0.0] * (size - 1), "imag": [0.0] * size,
        }
        transport.emit(response)

    device, _, _ = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.circuit", parameters=parameters).run(timeout=1)
        assert ("density_matrix" in result.data) is calc_matrix
        assert ("state_vector" in result.data) is not calc_matrix
    finally:
        device.close()


@pytest.mark.parametrize("calc_matrix", (True, False))
def test_circuit_matrix_shape_must_match_the_requested_mode(calc_matrix):
    parameters = parameters_for("triangulum.circuit")
    parameters.calc_matrix = calc_matrix

    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        wrong_size = 8 if calc_matrix else 64
        response["task_result"]["execution_matrix"] = {
            "real": [1.0] + [0.0] * (wrong_size - 1), "imag": [0.0] * wrong_size,
        }
        transport.emit(response)

    device, _, _ = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentFailedError):
            device.create_experiment("triangulum.circuit", parameters=parameters).run(timeout=1)
    finally:
        device.close()


def test_circuit_density_matrix_is_enabled_by_default():
    assert parameters_for("triangulum.circuit").calc_matrix is True


def test_calc_matrix_false_accepts_empty_matrix_arrays_from_client():
    """Client 2.0 reports empty components when density calculation is disabled."""
    parameters = parameters_for("triangulum.circuit")
    parameters.calc_matrix = False

    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response["task_result"]["execution_matrix"] = {"real": [], "imag": []}
        transport.emit(response)

    device, _, _ = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.circuit", parameters=parameters).run(timeout=1)
        assert result.status == "COMPLETED"
        assert len(result.data["probabilities"]) == 8
        assert "state_vector" not in result.data and "density_matrix" not in result.data
    finally:
        device.close()


@pytest.mark.parametrize("value", (1, "true", [True], None))
def test_circuit_matrix_choice_requires_a_boolean(value):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        parameters_for("triangulum.circuit").calc_matrix = value


@pytest.mark.parametrize("key", ("triangulum.physical", "triangulum.circuit"))
def test_complete_sdk_run_matches_cpp_protocol_envelope_and_keeps_wire_result(key):
    device, client, transport = device_and_transport()
    try:
        device.open()
        result = device.create_experiment(key).run(timeout=1)
        request = next(value for value in transport.sent if value["msg_id"].startswith("push_"))
        assert request["session_id"] == "session-fixture"
        assert str(int(request["task_id"])) == result.task_id
        assert 0 < int(result.task_id) < 2**63
        reference = parameters_for(key).to_wire()
        assert request["task_gates"] == (
            reference["circuit"] if key.endswith("circuit") else reference
        )
        assert request["task_qubits"] == 3
        if key.endswith("circuit"):
            assert request["calcMatrix"] is True
        else:
            assert "calcMatrix" not in request
        assert result.raw["protocol_raw"]["finished"]["task_state"] == "S"
        assert "fidelity" not in result.data  # The fixture did not supply it.
        assert "password-fixture" not in result.to_json()
        assert client.get_experiment_status() is None  # Registration cleaned by the SDK.
    finally:
        device.close()
    assert transport.closed and client._worker is None


@pytest.mark.parametrize(
    "state,error", (("F", ExperimentFailedError), ("T", ExperimentTerminatedError))
)
def test_remote_terminal_failure_without_result_is_not_completed(state, error):
    def action(transport, request):
        transport.ack(request)
        transport.emit(finished(request, state))

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(error):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is None
    finally:
        device.close()


def test_submission_rejection_is_distinct_and_does_not_block_the_next_task():
    def reject(transport, request):
        transport.ack(request, -4)

    device, client, transport = device_and_transport(reject)
    try:
        device.open()
        with pytest.raises(ExperimentRejectedError, match="-4"):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is None
        transport.action = None
        assert device.create_experiment("triangulum.circuit").run(timeout=1).status == "COMPLETED"
    finally:
        device.close()


@pytest.mark.parametrize("drop", (False, True))
def test_missing_ack_or_disconnect_is_unknown_and_submission_is_not_replayed(drop):
    def action(transport, request):
        if drop:
            transport.received.put(ConnectionError("fixture disconnect"))

    device, client, transport = device_and_transport(action, request_timeout=0.1)
    try:
        device.open()
        with pytest.raises(SubmissionOutcomeUnknownError):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is not None
        assert len([m for m in transport.sent if m["msg_id"] == "push_task_request"]) == 1
    finally:
        device.close()


def test_acknowledged_task_timeout_retains_identity_and_blocks_resubmission():
    device, client, transport = device_and_transport(
        lambda transport, request: transport.ack(request)
    )
    try:
        device.open()
        with pytest.raises(ExperimentTimeoutError) as caught:
            device.create_experiment("triangulum.circuit").run(timeout=0.1, queue_timeout=0.1)
        assert caught.value.status == "PENDING"
        assert caught.value.task_id == device._last_unresolved_task
        with pytest.raises(SubmissionOutcomeUnknownError):
            device.create_experiment("triangulum.circuit").run(timeout=0.1)
    finally:
        device.close()


def test_submission_acceptance_and_task_start_have_distinct_states():
    device, client, transport = device_and_transport(
        lambda transport, request: transport.ack(request)
    )
    try:
        device.open()
        task, _ = client.register_experiment("EXP_CIRCUIT_LAYER")
        task.parameters = parameters_for("triangulum.circuit").to_native()
        client.run_experiment(timeout=1)
        assert client.get_experiment_status() == "PENDING"
        transport.emit({"msg_id": "task_started_post", "task_id": task.id})
        deadline = time.monotonic() + 0.5
        while client.get_experiment_status() != "RUNNING" and time.monotonic() < deadline:
            time.sleep(0.01)
        assert client.get_experiment_status() == "RUNNING"
    finally:
        client.deregister_experiment()
        device.close()


@pytest.mark.parametrize("order", ("finish_first", "duplicate", "wrong_task"))
def test_out_of_order_duplicates_and_other_task_messages_do_not_corrupt_results(order):
    def action(transport, request):
        if order == "finish_first":
            transport.emit(finished(request))
            transport.ack(request)
        else:
            transport.ack(request, identifier="other-task")
            wrong = finished(request, "F")
            wrong["task_id"] = "other-task"
            transport.emit(wrong)
            transport.ack(request)
            transport.emit(finished(request))
            if order == "duplicate":
                transport.ack(request, -4)
                transport.emit(finished(request, "F"))

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        assert device.create_experiment("triangulum.circuit").run(timeout=1).status == "COMPLETED"
    finally:
        device.close()


def test_malformed_measurement_is_a_processing_failure_not_completion():
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response["task_result"]["execution"] = [float("nan")]
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises((ExperimentFailedError, SubmissionOutcomeUnknownError)):
            device.create_experiment("triangulum.circuit").run(timeout=1)
    finally:
        device.close()


def test_two_sdk_sessions_and_rapid_tasks_have_independent_state_and_ids():
    first, a, ta = device_and_transport()
    second, b, tb = device_and_transport()
    try:
        first.open()
        second.open()
        ids = {
            first.create_experiment("triangulum.circuit").run(timeout=1).task_id for _ in range(8)
        }
        assert len(ids) == 8
        first.close()
        assert second.is_ready
        result = second.create_experiment("triangulum.physical").run(timeout=1)
        assert result.task_id not in ids
    finally:
        first.close()
        second.close()


def test_authentication_failure_has_no_task_submission_and_closes_resources():
    device, client, transport = device_and_transport(login_code=999)
    with pytest.raises(DeviceNotReadyError):
        device.open(timeout=0.5)
    assert transport.closed and client._worker is None
    assert not any(m["msg_id"].startswith("push_") for m in transport.sent)


def test_login_response_without_session_id_is_not_ready():
    device, client, transport = device_and_transport()
    original = transport.send

    def invalid_login(text):
        message = json.loads(text)
        if message["msg_id"] == "user_login_request":
            transport.emit({"msg_id": "user_login_response", "return_code": 0})
        else:
            original(text)

    transport.send = invalid_login
    with pytest.raises(DeviceNotReadyError):
        device.open(timeout=0.5)
    assert transport.closed and client._worker is None


def test_local_validation_failure_sends_nothing_and_does_not_poison_session():
    device, client, transport = device_and_transport(max_message_bytes=180)
    try:
        device.open()
        with pytest.raises(ValueError, match="no bytes sent"):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is None
        assert not any(message["msg_id"].startswith("push_") for message in transport.sent)
        assert device.is_ready
    finally:
        device.close()


@pytest.mark.parametrize("kind", (1, 2))
def test_physical_measurement_variants_decode_the_actual_pauli_and_state_data(kind):
    device, client, transport = device_and_transport()
    parameters = parameters_for("triangulum.physical")
    parameters.type_setting = kind
    parameters.step_list = [1, 2]
    try:
        device.open()
        result = device.create_experiment("triangulum.physical", parameters=parameters).run(
            timeout=1
        )
        assert result.data["pauli_basis"] == {"fixture": 0.5}
        if kind == 2:
            assert result.data["state_vector"] == [1 + 0j, 0 + 0j]
            assert result.data["probability"] == [1, 0]
    finally:
        device.close()


def test_invalid_state_vector_is_reported_as_local_result_processing_failure():
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response["task_result"]["execution_matrix"]["imag"] = []
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentFailedError, match="processing"):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is None
    finally:
        device.close()


@pytest.mark.parametrize(
    "graph", (None, [], [{}], [{"fidRe": []}], "not-base64", [{"fidRe": [[0]]}])
)
def test_invalid_physical_chart_is_a_processing_failure_not_completion(graph):
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response["graph_result_compressed"] = graph
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentFailedError, match="processing"):
            device.create_experiment("triangulum.physical").run(timeout=1)
        assert device._last_unresolved_task is None
    finally:
        device.close()


def test_physical_compressed_chart_is_validated_and_preserved_in_the_result():
    payload = json.dumps([{"fidRe": {"x": [0, 1], "y": [1, 2]}}]).encode()
    graph = base64.b64encode(struct.pack(">I", len(payload)) + zlib.compress(payload)).decode()

    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response["graph_result_compressed"] = graph
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.physical").run(timeout=1)
        assert result.status == "COMPLETED"
        assert result.data["graph"] == graph
    finally:
        device.close()


@pytest.mark.parametrize("fault", ("dimensions", "negative_probability", "qubit_count"))
def test_inconsistent_circuit_measurements_are_not_reported_as_complete(fault):
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        if fault == "dimensions":
            response["task_result"]["execution_matrix"] = {"real": [1], "imag": [0]}
        elif fault == "negative_probability":
            response["task_result"]["execution"][0] = -1
        else:
            response["task_qubits"] = 2
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentFailedError, match="processing"):
            device.create_experiment("triangulum.circuit").run(timeout=1)
    finally:
        device.close()


@pytest.mark.parametrize("fault", ("deep_json", "numeric_overflow", "fidelity_overflow"))
def test_malformed_terminal_data_reports_processing_failure_with_known_task(fault):
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        if fault == "deep_json":
            response["task_result"] = "[" * 2000 + "0" + "]" * 2000
        elif fault == "numeric_overflow":
            response["task_result"]["execution"][0] = 10**400
        else:
            response["fidelity"] = 10**400
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentFailedError, match="processing"):
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert device._last_unresolved_task is None
    finally:
        device.close()


def test_server_authentication_fields_are_redacted_in_saved_task_messages():
    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        response.update(
            session_id="session-fixture", password="password-fixture", account="account-fixture"
        )
        transport.emit(response)

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.circuit").run(timeout=1)
        assert "password-fixture" not in result.to_json()
        assert "account-fixture" not in result.to_json()
        assert "session-fixture" not in result.to_json()
        assert result.raw["protocol_raw"]["finished"]["session_id"] == "<redacted>"
    finally:
        device.close()


def test_lost_application_heartbeat_closes_only_the_affected_session():
    device, client, transport = device_and_transport(
        heartbeat_interval=0.02, heartbeat_timeout=0.07
    )
    other, second, other_transport = device_and_transport()
    original = transport.send

    def silent_heartbeat(text):
        if json.loads(text)["msg_id"] != "heartbeat":
            original(text)

    transport.send = silent_heartbeat
    notification = threading.Event()
    observed = []
    device.subscribe_disconnect(lambda event: (observed.append(event), notification.set()))
    try:
        device.open()
        other.open()
        deadline = time.monotonic() + 0.5
        while device.is_ready and time.monotonic() < deadline:
            time.sleep(0.01)
        assert not device.is_ready
        assert other.is_ready
        assert notification.wait(1)
        assert "heartbeat" in device.last_disconnect_reason
        details = observed[0].diagnostics
        assert details["idle_seconds"] >= details["heartbeat_timeout_seconds"] == 0.07
        assert details["last_heartbeat_sent_monotonic"] is not None
        assert details["server_version"] is None
    finally:
        device.close()
        other.close()


def test_public_disconnect_event_preserves_task_and_redacts_reason_off_receiver_thread():
    def action(transport, request):
        transport.ack(request)
        transport.received.put(ConnectionResetError("reset password-fixture session-fixture account-fixture"))

    device, _, transport = device_and_transport(action)
    observed, names, removed = [], [], []
    notified = threading.Event()

    def consume(event):
        observed.append(event)
        names.append(threading.current_thread().name)
        notified.set()

    unsubscribe = device.subscribe_disconnect(removed.append)
    unsubscribe()
    device.subscribe_disconnect(lambda event: (_ for _ in ()).throw(RuntimeError("observer failed")))
    device.subscribe_disconnect(consume)
    try:
        device.open()
        with pytest.raises(SubmissionOutcomeUnknownError) as caught:
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert notified.wait(1)
        assert observed[0].task_ids == (caught.value.task_id,)
        assert "reset" in device.last_disconnect_reason
        assert all(secret not in repr(observed) for secret in (
            "password-fixture", "account-fixture", "session-fixture"))
        assert names != ["spinq-triangulum-receiver"]
        assert len([m for m in transport.sent if m["msg_id"] == "push_task_request"]) == 1
        assert removed == []
    finally:
        device.close()
    assert len(observed) == 1 and device.last_disconnect_event is observed[0]


def test_explicit_triangulum_close_does_not_publish_disconnect_failure():
    device, _, _ = device_and_transport()
    observed = []
    device.subscribe_disconnect(observed.append)
    device.open()
    device.close()
    assert observed == [] and device.last_disconnect_reason is None


def test_task_send_failure_marks_device_disconnected_and_notifies_without_replay():
    def failed_send(transport, request):
        raise ConnectionResetError(10054, "task write reset")

    device, _, transport = device_and_transport(failed_send)
    observed, notified = [], threading.Event()
    device.subscribe_disconnect(lambda event: (observed.append(event), notified.set()))
    try:
        device.open()
        with pytest.raises(SubmissionOutcomeUnknownError) as caught:
            device.create_experiment("triangulum.circuit").run(timeout=1)
        assert not device.is_ready
        assert notified.wait(1)
        assert observed[0].task_ids == (caught.value.task_id,)
        assert "10054" in device.last_disconnect_reason
        assert len([m for m in transport.sent if m["msg_id"] == "push_task_request"]) == 1
    finally:
        device.close()


def test_real_receive_reset_during_triangulum_close_is_preserved():
    class ResetOnClose(ScriptedTransport):
        def __init__(self, config):
            super().__init__(config)
            self.login_received = False
            self.blocked = threading.Event()
            self.release = threading.Event()

        def receive(self):
            if self.login_received:
                self.blocked.set()
                assert self.release.wait(2)
                raise ConnectionResetError(10054, "peer reset session-fixture")
            value = super().receive()
            if value is not None:
                self.login_received = True
            return value

        def close(self):
            self.release.set()
            super().close()

    config = settings()
    transport = ResetOnClose(config)
    client = TriangulumSession(config, transport_factory=lambda _: transport)
    device = TriangulumDevice(config, backend_factory=lambda _: client)
    observed = []
    device.subscribe_disconnect(observed.append)
    device.open()
    assert transport.blocked.wait(1)
    device.close(timeout=0.5)
    assert len(observed) == 1 and "10054" in observed[0].reason
    assert "session-fixture" not in observed[0].reason
    assert device.last_disconnect_reason == observed[0].reason


def test_known_completion_survives_a_disconnect_after_the_terminal_frame():
    def action(transport, request):
        transport.ack(request)
        transport.emit(finished(request))
        transport.received.put(ConnectionError("closed after completion"))

    device, client, transport = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.circuit").run(timeout=1)
        assert result.status == "COMPLETED"
        assert result.data["probabilities"][0] == 1
    finally:
        device.close()


def test_application_heartbeat_is_session_scoped_and_cleanup_is_bounded():
    device, client, transport = device_and_transport(heartbeat_interval=0.02, heartbeat_timeout=0.2)
    device.open()
    deadline = time.monotonic() + 0.5
    while (
        not any(m["msg_id"] == "heartbeat" for m in transport.sent) and time.monotonic() < deadline
    ):
        time.sleep(0.01)
    assert any(
        m == {"msg_id": "heartbeat", "session_id": "session-fixture"} for m in transport.sent
    )
    # Observe more than two idle-timeout windows with valid heartbeat replies.
    alive_until = time.monotonic() + 0.45
    while time.monotonic() < alive_until:
        assert device.is_ready
        time.sleep(0.01)
    start = time.monotonic()
    device.close(timeout=0.3)
    assert time.monotonic() - start < 0.4
    assert client._worker is None
    device.close(timeout=0.3)


@pytest.mark.parametrize(
    "payload", ("[]", "{}", '{"msg_id":123}', '{"msg_id":"x","data":NaN}', "{broken")
)
def test_protocol_requires_finite_bounded_json_objects(payload):
    with pytest.raises(ProtocolError):
        decode_message(payload, 1024)


def test_protocol_enforces_message_limit_and_rejects_binary_frames():
    with pytest.raises(ProtocolError):
        decode_message('{"msg_id":"heartbeat"}', 4)
    with pytest.raises(ProtocolError):
        decode_message(b'{"msg_id":"heartbeat"}', 1024)


@pytest.mark.parametrize("matrix_kind", ("absent", "null", "vector", "density"))
def test_optional_circuit_matrix_preserves_components_without_assuming_order(matrix_kind):
    real = [float(i) / 64 for i in range(64)]
    imag = [-float(i) / 128 for i in range(64)]

    def action(transport, request):
        transport.ack(request)
        response = finished(request)
        value = response["task_result"]
        if matrix_kind == "absent":
            value.pop("execution_matrix")
        elif matrix_kind == "null":
            value["execution_matrix"] = None
        elif matrix_kind == "density":
            value["execution_matrix"] = {"real": real, "imag": imag}
        transport.emit(response)

    device, _, _ = device_and_transport(action)
    try:
        device.open()
        parameters = parameters_for("triangulum.circuit")
        parameters.calc_matrix = matrix_kind != "vector"
        result = device.create_experiment("triangulum.circuit", parameters=parameters).run(timeout=1)
        assert len(result.data["probabilities"]) == 8
        if matrix_kind == "density":
            expected = {"real": real, "imag": imag, "shape": [8, 8], "order": None}
            assert result.data["density_matrix"] == expected
            assert "state_vector" not in result.data
            assert json.loads(result.to_json())["raw"]["density_matrix"] == expected
        elif matrix_kind == "vector":
            assert len(result.data["state_vector"]) == 8
        else:
            assert "state_vector" not in result.data and "density_matrix" not in result.data
    finally:
        device.close()


def test_redaction_handles_nested_case_variants_without_changing_source():
    from spinqnmrlink._backends.triangulum.protocol import redact

    value = {"Password": "secret", "nested": [{"Account": "name", "SESSION_ID": "id",
                                               "sessionId": "id2", "sample_count": 10}]}
    assert redact(value) == {"Password": "<redacted>", "nested": [{
        "Account": "<redacted>", "SESSION_ID": "<redacted>", "sessionId": "<redacted>",
        "sample_count": 10}]}
    assert value["Password"] == "secret" and value["nested"][0]["Account"] == "name"


def test_unicode_encoding_errors_use_protocol_error_and_limits_count_bytes():
    with pytest.raises(ProtocolError):
        decode_message(chr(0xD800), 1024)
    text = json.dumps({"msg_id": "中文"}, ensure_ascii=False)
    size = len(text.encode("utf-8"))
    assert decode_message(text, size)["msg_id"] == "中文"
    with pytest.raises(ProtocolError):
        decode_message(text, size - 1)


@pytest.mark.parametrize("experiment_kind,started,ack", (
    ("EXP_CIRCUIT_LAYER", "task_started_post", "push_task_response"),
    ("EXP_PHYSICAL_LAYER", "custom_task_started_post", "push_custom_task_response"),
    ("EXP_PHYSICAL_LAYER", "task_started_post", "push_custom_task_response"),
))
def test_start_before_ack_is_recorded_once_and_other_tasks_do_not_start_timer(
    monkeypatch, experiment_kind, started, ack
):
    from types import SimpleNamespace

    from spinqnmrlink._core import task_timing

    clock = SimpleNamespace(seconds=40)
    monkeypatch.setattr(task_timing, "time", SimpleNamespace(monotonic=lambda: clock.seconds))
    client = TriangulumSession(settings())
    task, _ = client.register_experiment(experiment_kind)
    with client._condition:
        client._dispatch({"msg_id": started, "task_id": "someone-else"})
        assert getattr(task, "execution_started_monotonic", None) is None
        client._dispatch({"msg_id": started, "task_id": task.id})
        assert task.state == "PENDING" and task.execution_started_monotonic == 40
        clock.seconds = 60
        client._dispatch({"msg_id": started, "task_id": task.id})
        client._dispatch({"msg_id": ack, "task_id": task.id, "return_code": 0})
        assert task.state == "RUNNING" and task.execution_started_monotonic == 40


@pytest.mark.parametrize("first,second", (
    ("task_started_post", "custom_task_started_post"),
    ("custom_task_started_post", "task_started_post"),
))
def test_mixed_physical_start_aliases_preserve_the_first_timestamp(monkeypatch, first, second):
    from types import SimpleNamespace

    from spinqnmrlink._core import task_timing

    clock = SimpleNamespace(seconds=10)
    monkeypatch.setattr(task_timing, "time", SimpleNamespace(monotonic=lambda: clock.seconds))
    client = TriangulumSession(settings())
    task, _ = client.register_experiment("EXP_PHYSICAL_LAYER")
    with client._condition:
        client._dispatch({"msg_id": "push_custom_task_response", "task_id": task.id, "return_code": 0})
        client._dispatch({"msg_id": first, "task_id": task.id})
        clock.seconds = 30
        client._dispatch({"msg_id": second, "task_id": task.id})
        assert task.execution_started_monotonic == 10
        assert task.wire["started"]["msg_id"] == first
        assert task.state == "RUNNING"


@pytest.mark.parametrize("started", ("task_started_post", "custom_task_started_post"))
def test_physical_start_alias_populates_public_timing(started):
    def action(transport, request):
        transport.ack(request)
        transport.emit({"msg_id": started, "task_id": request["task_id"]})
        transport.emit(finished(request))

    device, _, _ = device_and_transport(action)
    try:
        device.open()
        result = device.create_experiment("triangulum.physical").run(timeout=1, queue_timeout=1)
        assert result.metadata["execution_started_at_utc"] is not None
        assert result.metadata["queue_duration_seconds"] >= 0
        assert result.metadata["execution_duration_seconds"] >= 0
        assert result.raw["protocol_raw"]["started"]["msg_id"] == started
    finally:
        device.close()


@pytest.mark.parametrize("started", ("task_started_post", "custom_task_started_post"))
def test_physical_start_alias_switches_to_execution_timeout_without_replay(started):
    def action(transport, request):
        transport.ack(request)
        transport.emit({"msg_id": started, "task_id": request["task_id"]})

    device, _, transport = device_and_transport(action)
    try:
        device.open()
        with pytest.raises(ExperimentTimeoutError) as caught:
            device.create_experiment("triangulum.physical").run(timeout=0.1, queue_timeout=0.4)
        assert caught.value.phase == "execution"
        assert caught.value.status == "RUNNING"
        assert device._last_unresolved_task == caught.value.task_id
        assert len([m for m in transport.sent if m["msg_id"] == "push_custom_task_request"]) == 1
    finally:
        device.close()


def test_physical_only_start_alias_does_not_start_a_circuit_task():
    client = TriangulumSession(settings())
    task, _ = client.register_experiment("EXP_CIRCUIT_LAYER")
    with client._condition:
        client._dispatch({"msg_id": "custom_task_started_post", "task_id": task.id})
    assert getattr(task, "execution_started_monotonic", None) is None
    assert task.state == "PENDING"


def test_real_websocket_transport_against_a_local_protocol_fixture(monkeypatch):
    """Exercise HTTP upgrade, masked frames and the actual websocket-client dependency."""
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(key, raising=False)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(2)
    failures = []
    frames = []
    pongs = []

    def serve():
        connection = None
        try:
            connection, _ = listener.accept()
            connection.settimeout(2)
            header = b""
            while b"\r\n\r\n" not in header:
                header += connection.recv(4096)
            key = next(
                line.split(b":", 1)[1].strip()
                for line in header.split(b"\r\n")
                if line.lower().startswith(b"sec-websocket-key:")
            )
            accept = base64.b64encode(
                hashlib.sha1(key + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest()
            )
            connection.sendall(
                b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "
                + accept
                + b"\r\n\r\n"
            )

            def read(count):
                value = b""
                while len(value) < count:
                    part = connection.recv(count - len(value))
                    if not part:
                        raise EOFError
                    value += part
                return value

            def send_frame(opcode, data):
                prefix = (
                    bytes((opcode, len(data)))
                    if len(data) < 126
                    else bytes((opcode, 126)) + struct.pack("!H", len(data))
                )
                connection.sendall(prefix + data)

            def emit(value, fragmented=False):
                data = json.dumps(value).encode()
                if fragmented:
                    send_frame(0x01, data[:40])
                    send_frame(0x89, b"fixture-ping")
                    send_frame(0x80, data[40:])
                else:
                    send_frame(0x81, data)

            while True:
                first, second = read(2)
                length = second & 127
                if length == 126:
                    length = struct.unpack("!H", read(2))[0]
                elif length == 127:
                    length = struct.unpack("!Q", read(8))[0]
                mask = read(4) if second & 128 else None
                data = read(length)
                if mask:
                    data = bytes(value ^ mask[index % 4] for index, value in enumerate(data))
                if first & 15 == 8:
                    return
                if first & 15 == 10:
                    pongs.append(data)
                    continue
                request = json.loads(data)
                frames.append(request)
                if request["msg_id"] == "user_login_request":
                    emit(
                        {
                            "msg_id": "user_login_response",
                            "return_code": 0,
                            "session_id": "loopback-session",
                        }
                    )
                elif request["msg_id"] == "push_task_request":
                    emit(
                        {
                            "msg_id": "push_task_response",
                            "return_code": 0,
                            "task_id": request["task_id"],
                        }
                    )
                    emit(finished(request), fragmented=True)
                elif request["msg_id"] == "user_logout_request":
                    emit({"msg_id": "user_logout_response", "return_code": 0})
                    return
        except Exception as error:
            failures.append(error)
        finally:
            if connection:
                connection.close()

    worker = threading.Thread(target=serve, daemon=True)
    worker.start()
    device = TriangulumDevice(
        TriangulumSettings(
            host="127.0.0.1", port=listener.getsockname()[1], account="fixture", password="fixture"
        )
    )
    try:
        device.open(timeout=1)
        result = device.create_experiment("triangulum.circuit").run(timeout=1)
        assert result.status == "COMPLETED"
        assert result.data["probabilities"][0] == 1
    finally:
        device.close(timeout=1)
        worker.join(2)
        listener.close()
    assert not failures
    assert not worker.is_alive()
    assert pongs == [b"fixture-ping"]
    assert [m["msg_id"] for m in frames] == [
        "user_login_request",
        "push_task_request",
        "user_logout_request",
    ]
