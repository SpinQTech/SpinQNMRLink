"""Controlled socket shutdowns and callbacks; no external device or network."""

import threading

import pytest

from spinqnmrlink._backends.lab.connection.connection import TCPConnection, WebSocketConnection


class ClosingSocket:
    def __init__(self, phase="recv"):
        self.phase = phase
        self.entered = threading.Event()
        self.released = threading.Event()
        self.failure = OSError(10038, "socket closed")

    def _wait(self):
        self.entered.set()
        assert self.released.wait(2)
        if self.failure is not None:
            raise self.failure
        return b""

    def settimeout(self, value):
        if self.phase == "settimeout":
            self._wait()

    def recv(self, size):
        return self._wait()

    def shutdown(self, how):
        self.released.set()

    def close(self):
        self.released.set()


def receive_connection(phase="recv"):
    connection = TCPConnection("localhost", 1)
    sock = ClosingSocket(phase)
    connection.socket = sock
    connection.connected = connection._running = True
    observed = []
    connection.set_disconnect_callback(observed.append)
    worker = threading.Thread(target=connection._recv_worker)
    connection._recv_thread = worker
    worker.start()
    assert sock.entered.wait(1)
    return connection, sock, worker, observed


@pytest.mark.parametrize("iteration", range(30))
def test_expected_active_close_does_not_report_receive_failure(iteration):
    connection, _, worker, observed = receive_connection()
    assert connection.disconnect(timeout=1)
    assert not worker.is_alive()
    assert observed == []


@pytest.mark.parametrize("iteration", range(20))
def test_active_close_during_settimeout_keeps_stable_socket_reference(iteration):
    connection, _, worker, observed = receive_connection("settimeout")
    assert connection.disconnect(timeout=1)
    assert not worker.is_alive()
    assert observed == []


@pytest.mark.parametrize("iteration", range(10))
def test_remote_eof_is_reported_once_and_cleanup_preserves_reason(iteration):
    connection, sock, worker, observed = receive_connection()
    sock.failure = None
    sock.released.set()
    worker.join(1)
    connection.disconnect(timeout=1)
    assert observed == ["server closed the connection"]
    assert connection.last_disconnect_reason == observed[0]


def test_unexpected_10038_is_reported_and_duplicate_failures_are_not_repeated():
    connection, sock, worker, observed = receive_connection()
    sock.released.set()
    worker.join(1)
    connection._notify_disconnected("send error: secondary failure")
    connection.disconnect(timeout=1)
    assert len(observed) == 1 and "10038" in observed[0]
    assert connection.last_disconnect_reason == observed[0]


def test_genuine_reset_is_not_hidden_by_simultaneous_manual_close():
    connection, sock, _, observed = receive_connection()
    sock.failure = ConnectionResetError(10054, "peer reset")
    connection.disconnect(timeout=1)
    assert len(observed) == 1 and "10054" in observed[0]
    assert connection.last_disconnect_reason == observed[0]


@pytest.mark.parametrize("kind", ("empty", "text", "eof", "control"))
def test_websocket_control_frames_are_distinct_from_empty_business_payloads(kind):
    from types import SimpleNamespace

    from websocket import ABNF

    frames = {
        "empty": [(ABNF.OPCODE_BINARY, b"")],
        "text": [(ABNF.OPCODE_TEXT, "unexpected")],
        "eof": [(ABNF.OPCODE_CLOSE, b"")],
        "control": [(ABNF.OPCODE_PING, b""), (ABNF.OPCODE_PONG, b""), (ABNF.OPCODE_BINARY, b"valid")],
    }
    received = iter(frames[kind])
    connection = WebSocketConnection("localhost", 1)
    connection.socket = SimpleNamespace(
        recv_data=lambda **kwargs: next(received), recv=lambda: next(received)[1],
        shutdown=lambda *args: None, close=lambda: None)
    connection._running = connection.connected = True
    observed, messages = [], []
    connection.set_disconnect_callback(observed.append)

    def consume(data):
        messages.append(data)
        connection.disconnect()

    connection.set_message_callback(consume)
    connection._recv_worker()
    if kind == "control":
        assert messages == [b"valid"] and observed == []
    else:
        assert len(observed) == 1
        assert ("server closed" if kind == "eof" else "protocol error") in observed[0]
