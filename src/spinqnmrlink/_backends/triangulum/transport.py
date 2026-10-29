# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Bounded text WebSocket transport. Each object owns exactly one connection."""

import threading


class WebSocketTransport:
    def __init__(self, settings):
        self.settings = settings
        self.socket = None
        self._send_lock = threading.Lock()

    def open(self, timeout):
        import websocket

        host = self.settings.host
        if ":" in host and not host.startswith("["):
            host = "[" + host + "]"
        path = self.settings.websocket_path
        url = "{}://{}:{}{}".format(
            "wss" if self.settings.websocket_secure else "ws", host, self.settings.port, path
        )
        self.socket = websocket.create_connection(url, timeout=timeout, enable_multithread=True)
        self.socket.settimeout(0.1)

    def send(self, text):
        with self._send_lock:
            if self.socket is None:
                raise ConnectionError("WebSocket is closed")
            self.socket.send(text)

    def receive(self):
        import websocket

        try:
            opcode, value = self.socket.recv_data(control_frame=True)
        except websocket.WebSocketTimeoutException:
            return None
        if opcode == websocket.ABNF.OPCODE_CLOSE:
            raise ConnectionError("WebSocket was closed by the peer")
        if opcode in (websocket.ABNF.OPCODE_PING, websocket.ABNF.OPCODE_PONG):
            return None
        if opcode != websocket.ABNF.OPCODE_TEXT:
            raise ConnectionError("Triangulum requires JSON text WebSocket frames")
        if len(value) > self.settings.max_message_bytes:
            raise ConnectionError("Triangulum message exceeded its size limit")
        return value.decode("utf-8") if isinstance(value, bytes) else value

    def close(self):
        socket, self.socket = self.socket, None
        if socket is not None:
            socket.shutdown()  # No blocking WebSocket close handshake.
