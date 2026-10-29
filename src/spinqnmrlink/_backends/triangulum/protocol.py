# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Triangulum JSON wire protocol, independent of sockets and experiment execution."""

import json
import math

from ..._core.graphs import graph_curves


class ProtocolError(ValueError):
    """A received message violates the supported device protocol."""


class SubmissionNotSentError(ValueError):
    """Local task validation failed before any bytes were sent."""


def decode_message(text, max_bytes):
    if not isinstance(text, str):
        raise ProtocolError("Expected a bounded JSON text message")
    try:
        if len(text.encode("utf-8")) > max_bytes:
            raise ProtocolError("Expected a bounded JSON text message")
        value = json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except UnicodeError:
        raise ProtocolError("Invalid Unicode in JSON message") from None
    except (ValueError, RecursionError):
        raise ProtocolError("Invalid JSON message") from None
    if not isinstance(value, dict) or not isinstance(value.get("msg_id"), str):
        raise ProtocolError("Message must contain a string msg_id")
    return value


def encode_message(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def task_request(task, session_id):
    parameters = task.parameters.get_parameters()
    circuit = task.kind == "EXP_CIRCUIT_LAYER"
    request = {
        "msg_id": "push_task_request" if circuit else "push_custom_task_request",
        "session_id": session_id,
        "task_id": task.id,
        "task_name": "SDK-" + task.id,
        "task_description": "Circuit Layer Experiment" if circuit else "Physical Layer Experiment",
        "task_qubits": parameters["qubits_num"] if circuit else 3,
        "task_gates": parameters["circuit"] if circuit else parameters,
    }
    if circuit:
        request["calcMatrix"] = parameters["calcMatrix"]
    return request


def response_code(message):
    code = message.get("return_code")
    if type(code) is not int:
        raise ProtocolError("Response must contain an integer return_code")
    return code


def task_id(message):
    value = message.get("task_id")
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value):
        raise ProtocolError("Task response must contain a task_id")
    return str(value)


def _numbers(value, name):
    if not isinstance(value, list) or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
        for x in value
    ):
        raise ProtocolError("Invalid numeric array: " + name)
    return value


def _vector(matrix):
    if not isinstance(matrix, dict):
        raise ProtocolError("Invalid state-vector components")
    real = _numbers(matrix.get("real"), "real")
    imag = _numbers(matrix.get("imag"), "imag")
    if len(real) != len(imag):
        raise ProtocolError("State-vector component lengths differ")
    return [complex(r, i) for r, i in zip(real, imag)]


def decode_result(task, message):
    """Decode a successful result without inventing absent optional measurements."""
    value = message.get("task_result", {})
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, RecursionError):
            raise ProtocolError("Invalid task_result JSON") from None
    if not isinstance(value, dict):
        raise ProtocolError("task_result must be an object")
    data = {}
    if task.kind == "EXP_CIRCUIT_LAYER":
        probabilities = _numbers(value.get("execution"), "execution")
        if len(probabilities) != 2**task.parameters.qubits_num:
            raise ProtocolError("Circuit probability count does not match the submitted circuit")
        if any(value < 0 for value in probabilities):
            raise ProtocolError("Circuit probabilities must be nonnegative")
        data["probabilities"] = probabilities
        matrix = value.get("execution_matrix")
        if matrix is not None:
            components = _vector(matrix)
            dimension = len(probabilities)
            density = task.parameters.calc_matrix
            # With calcMatrix disabled, client 2.0 returns empty component arrays
            # alongside valid probabilities. These mean absent matrix data.
            if components or density:
                expected = dimension * dimension if density else dimension
                if len(components) != expected:
                    raise ProtocolError("Matrix dimension does not match the requested calcMatrix mode")
                if density:
                    # The protocol does not specify row/column storage order.
                    data["density_matrix"] = {
                        "real": list(matrix["real"]), "imag": list(matrix["imag"]),
                        "shape": [dimension, dimension], "order": None,
                    }
                else:
                    data["state_vector"] = components
        if "task_qubits" in message and (
            type(message["task_qubits"]) is not int
            or message["task_qubits"] != task.parameters.qubits_num
        ):
            raise ProtocolError("Result qubit count differs from the submitted circuit")
        fidelity = message.get("fidelity")
        if fidelity is not None and (
            isinstance(fidelity, bool)
            or not isinstance(fidelity, (int, float))
            or not math.isfinite(fidelity)
        ):
            raise ProtocolError("Invalid circuit fidelity")
        for field in ("fidelity", "task_qubits"):
            if field in message:
                data["qubits_num" if field == "task_qubits" else field] = message[field]
        if "coordinate" in value:
            data["coordinate"] = value["coordinate"]
    else:
        if "graph_result_compressed" not in message:
            raise ProtocolError("Physical result is missing acquired chart data")
        data["graph"] = message["graph_result_compressed"]
        curves = graph_curves(data["graph"])
        if not any(points for group in curves for points in group.values()):
            raise ProtocolError("Physical result is missing acquired chart points")
        kind = task.parameters.type_setting
        if kind in (1, 2):
            if "pauli" not in value:
                raise ProtocolError("Physical result is missing Pauli components")
            data["pauli_basis"] = value["pauli"]
        if kind == 2:
            data["probability"] = _numbers(value.get("module"), "module")
            data["state_vector"] = _vector(value)
    return data


def redact(value):
    """Keep task wire data while removing authentication fields from saved metadata."""
    if isinstance(value, dict):
        return {
            key: "<redacted>"
            if isinstance(key, str) and key.casefold() in ("account", "password", "session_id", "sessionid")
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
