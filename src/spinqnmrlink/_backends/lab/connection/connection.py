# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Low-level TCP connection implementation.

Provides threaded, queue-based buffered send/receive functionality.
"""

import socket
import time
import threading
import queue
import errno
from typing import Dict, Any, Callable

try:
    import websocket
except ImportError:  # pragma: no cover - exercised only in incomplete installs
    websocket = None

from .protocol import ProtocolFrameError

# Custom timeout exception
class TimeoutError(Exception):
    """Connection timeout exception."""
    pass

from ..utils import LoggerManager

# Create logger
logger = LoggerManager.get_logger(name='connection')

class TCPConnection:
    """TCP connection class used for communication with remote devices."""

    def __init__(self, host: str, port: int, timeout: float = 10.0):
        """
        Initialize a TCP connection.

        Args:
            host: Server hostname or IP.
            port: Server port.
            timeout: Connection timeout in seconds.
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.connected = False
        self.buffer_size = 32768

        # Thread control
        self._running = False
        self._send_thread = None
        self._recv_thread = None

        # TCP is full-duplex: use separate locks for each direction so that
        # a blocking recv never stalls a pending send (critical on Linux).
        self._send_lock = threading.Lock()
        self._recv_lock = threading.Lock()
        self._state_lock = threading.Lock()

        # Message queue
        self._send_queue = queue.Queue()

        self._waiting_responses = {}
        self._message_callback = None
        self._disconnect_callback = None
        self._generation = 0
        self._manual_close = False
        self.last_disconnect_reason = None

    def connect(self) -> bool:
        """
        Connect to the server.

        Returns:
            bool: Whether the connection was successful.
        """
        if self.connected:
            return True

        try:
            self._send_queue = queue.Queue()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Block only during the initial connect; afterwards each worker
            # thread manages its own timeout independently.
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)  # back to blocking; workers set their own

            self._start_workers()

            logger.info(f"Connected successfully: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False

    def disconnect(self, timeout: float = 2.0) -> bool:
        """Close socket before joining workers, bounded by one deadline."""
        deadline = time.monotonic() + timeout
        with self._state_lock:
            self._manual_close = True
            self._running = self.connected = False
            sock, self.socket = self.socket, None
        self._send_queue.put(None)
        self._close_socket(sock)
        workers = (self._recv_thread, self._send_thread)
        for worker in workers:
            if worker is not None and worker is not threading.current_thread():
                worker.join(max(0, deadline - time.monotonic()))
        return all(worker is None or not worker.is_alive() or worker is threading.current_thread()
                   for worker in workers)

    def abort(self, reason: str = "Connection aborted") -> None:
        """Immediately close a failed connection without joining its worker.

        This is safe to call from the receive thread, which is where framing
        errors are detected.
        """
        self._fail(reason, expected_on_close=True)

    def _close_socket(self, sock):
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
    def _start_workers(self):
        with self._state_lock:
            self._generation += 1
            generation = self._generation
            self._manual_close = False
            self.last_disconnect_reason = None
            self._running = self.connected = True
            sock = self.socket
        self._recv_thread = threading.Thread(target=self._recv_worker, args=(sock, generation), daemon=True)
        self._send_thread = threading.Thread(target=self._send_worker, args=(sock, generation, self._send_queue), daemon=True)
        self._recv_thread.start()
        self._send_thread.start()

    @staticmethod
    def _expected_close_error(error):
        return getattr(error, "winerror", None) == 10038 or getattr(error, "errno", None) in (
            errno.EBADF, errno.ENOTSOCK, 10038,
        )

    def _fail(self, reason, generation=None, *, expected_on_close=False):
        with self._state_lock:
            if generation is not None and generation != self._generation:
                return
            if self.last_disconnect_reason is not None or (self._manual_close and expected_on_close):
                return
            self.last_disconnect_reason = reason
            self._running = self.connected = False
            sock, self.socket = self.socket, None
            callback = self._disconnect_callback
        self._send_queue.put(None)
        self._close_socket(sock)
        logger.warning("Transport disconnected: %s", reason)
        if callback:
            try:
                callback(reason)
            except Exception as exc:
                logger.error("Disconnect callback execution error: %s", exc)

    def _send_worker(self, sock=None, generation=None, send_queue=None) -> None:
        """Worker function for the send thread."""
        sock = self.socket if sock is None else sock
        generation = self._generation if generation is None else generation
        send_queue = self._send_queue if send_queue is None else send_queue
        while self._running and self.connected and generation == self._generation:
            try:
                try:
                    data = send_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if data is None:  # sentinel from disconnect()
                    send_queue.task_done()
                    break

                if sock and self.connected:
                    with self._send_lock:
                        self._send_frame(data, sock)
                else:
                    logger.warning("Send failed: Not connected")

                send_queue.task_done()

            except socket.error as e:
                self._fail(f"send error: {e}", generation, expected_on_close=self._expected_close_error(e))
                break
            except Exception as e:
                self._fail(f"send error: {e}", generation, expected_on_close=self._expected_close_error(e))
                break

    def _send_frame(self, data, sock):
        sock.sendall(data)

    def _recv_worker(self, sock=None, generation=None) -> None:
        """Worker function for the receive thread."""
        RECV_TIMEOUT = 1.0

        sock = self.socket if sock is None else sock
        generation = self._generation if generation is None else generation
        while self._running and self.connected and generation == self._generation:
            try:
                if not (sock and self.connected):
                    time.sleep(0.1)
                    continue

                try:
                    sock.settimeout(RECV_TIMEOUT)
                    with self._recv_lock:
                        data = sock.recv(self.buffer_size)

                    if not data:
                        self._fail("server closed the connection", generation, expected_on_close=True)
                        break

                    self._handle_received_message(data)

                except socket.timeout:
                    continue
                except socket.error as e:
                    self._fail(f"receive error: {e}", generation, expected_on_close=self._expected_close_error(e))
                    break

            except Exception as e:
                self._fail(f"receive error: {e}", generation, expected_on_close=self._expected_close_error(e))
                break

    def _handle_received_message(self, data: bytes) -> None:
        """
        Handle received raw message bytes.

        Args:
            data: Raw message bytes.
        """
        if self._message_callback:
            try:
                self._message_callback(data)
            except Exception as e:
                logger.error(f"Message callback execution error: {e}")

    def send(self, data: bytes) -> bool:
        """
        Enqueue data for sending.

        Args:
            data: Data to send.

        Returns:
            bool: Whether the data was enqueued successfully.
        """
        if not self.connected:
            logger.warning("Send failed: Not connected")
            return False

        try:
            self._send_queue.put(data)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

    def wait_for_send_queue(self, timeout: float = 1.0) -> bool:
        """Wait briefly until all queued messages have been written to TCP."""
        deadline = time.time() + timeout
        while self._send_queue.unfinished_tasks and time.time() < deadline:
            time.sleep(0.01)
        return self._send_queue.unfinished_tasks == 0

    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set the message callback function.

        Args:
            callback: Callback which receives the parsed message bytes.
        """
        self._message_callback = callback

    def set_disconnect_callback(self, callback: Callable[[str], None]) -> None:
        self._disconnect_callback = callback

    def _notify_disconnected(self, reason: str) -> None:
        self._fail(reason)

    def is_connected(self) -> bool:
        """
        Check whether the connection is currently established.

        Returns:
            bool: True if connected, otherwise False.
        """
        return self.connected


class WebSocketConnection(TCPConnection):
    """Threaded WebSocket binary transport with the TCP connection API."""

    def __init__(
        self,
        host: str,
        port: int = 8181,
        timeout: float = 10.0,
        path: str = "/ws",
        secure: bool = False,
    ):
        super().__init__(host, port, timeout=timeout)
        normalized_path = "/" + path.lstrip("/")
        scheme = "wss" if secure else "ws"
        self.path = normalized_path
        self.secure = secure
        self.url = f"{scheme}://{host}:{port}{normalized_path}"

    def connect(self) -> bool:
        if self.connected:
            return True
        if websocket is None:
            raise RuntimeError(
                "WebSocket transport requires the 'websocket-client' package"
            )
        try:
            self._send_queue = queue.Queue()
            self.socket = websocket.create_connection(
                self.url,
                timeout=self.timeout,
                enable_multithread=True,
            )
            self.socket.settimeout(None)
            self._start_workers()
            logger.info(f"Connected successfully: {self.url}")
            return True
        except Exception as exc:
            logger.error(f"WebSocket connection failed: {exc}")
            self.connected = False
            self._running = False
            return False

    def _send_frame(self, data: bytes, sock) -> None:
        if websocket is None:
            raise RuntimeError("websocket-client is not installed")
        sock.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    @staticmethod
    def _validate_received_frame(data: Any) -> bytes:
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ProtocolFrameError("WebSocket business frame must be binary")
        if not data:
            raise ProtocolFrameError("Empty WebSocket business payload")
        return bytes(data)

    @staticmethod
    def _expected_close_error(error):
        return TCPConnection._expected_close_error(error) or (
            websocket is not None and isinstance(error, websocket.WebSocketConnectionClosedException)
        )

    def _recv_worker(self, sock=None, generation=None) -> None:
        sock = self.socket if sock is None else sock
        generation = self._generation if generation is None else generation
        while self._running and self.connected and generation == self._generation:
            try:
                opcode, data = sock.recv_data(control_frame=True)
                if opcode == websocket.ABNF.OPCODE_CLOSE:
                    self._fail("WebSocket server closed the connection", generation, expected_on_close=True)
                    break
                if opcode in (websocket.ABNF.OPCODE_PING, websocket.ABNF.OPCODE_PONG):
                    continue
                if opcode != websocket.ABNF.OPCODE_BINARY:
                    raise ProtocolFrameError("WebSocket business frame must be binary")
                self._handle_received_message(self._validate_received_frame(data))
            except ProtocolFrameError as exc:
                self._fail(f"Connection closed after WebSocket protocol error: {exc}", generation)
                break
            except Exception as exc:
                if websocket is not None and isinstance(exc, websocket.WebSocketTimeoutException):
                    continue
                self._fail(f"WebSocket receive error: {exc}", generation,
                           expected_on_close=self._expected_close_error(exc))
                break

    def _close_socket(self, sock):
        if sock is not None:
            try:
                sock.shutdown()  # No potentially blocking WebSocket close handshake.
            except OSError:
                pass
