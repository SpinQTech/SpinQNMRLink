# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Communication protocol module.

Responsible for packaging and parsing experiment protocol data.
"""

from collections import deque
import json
from typing import Deque, Dict, Any, List, Optional, Tuple, Union
import struct

from ..utils import LoggerManager
from ..utils.types import QubitMode
from . import message_pb2

# Create logger
logger = LoggerManager.get_logger(name='protocol')


class ProtocolFrameError(ValueError):
    """Raised when a TCP frame violates the wire protocol."""

class Protocol:
    """Communication protocol class responsible for data packing and unpacking."""
    DEFAULT_MAX_FRAME_LENGTH = 16 * 1024 * 1024

    def __init__(self, max_frame_length: int = DEFAULT_MAX_FRAME_LENGTH):
        if not isinstance(max_frame_length, int) or max_frame_length <= 0:
            raise ValueError("max_frame_length must be a positive integer")
        self.remaining_data = b''
        self._decoded_messages: Deque[Dict[str, Any]] = deque()
        self.max_frame_length = max_frame_length
        # Packet header magic number
        self.HEADER_MAGIC = 0xCAFEBABE

    def serialize_message(
        self,
        msg_id: str,
        metadata: Dict[str, Any],
        json_data: Dict[str, Any],
        qubit_mode: Optional[Union[QubitMode, int]] = None,
    ) -> bytes:
        """
        Pack a protobuf message into binary data.

        Args:
            msg_id: Message identifier string.
            metadata: Metadata dictionary.
            json_data: Business JSON data to send.

        Returns:
            Packed binary data.
        """
        try:
            serialized_message = self.serialize_payload(
                msg_id,
                metadata,
                json_data,
                qubit_mode=qubit_mode,
            )
            data_length = len(serialized_message)

            # Assemble header: magic (4 bytes) + length (4 bytes)
            # In '>II', '>' means big-endian, each 'I' is an unsigned 4‑byte integer
            header = struct.pack('>II', self.HEADER_MAGIC, data_length)
            # Assemble full message
            packed_data = header + serialized_message

            return packed_data

        except Exception as e:
            logger.error(f"Message packing failed: {str(e)}")
            return b""

    def serialize_payload(
        self,
        msg_id: str,
        metadata: Dict[str, Any],
        json_data: Dict[str, Any],
        qubit_mode: Optional[Union[QubitMode, int]] = None,
    ) -> bytes:
        """Serialize one raw BaseMessage for WebSocket binary transport."""
        message_data = message_pb2.BaseMessage()
        message_data.msg_id = msg_id
        message_data.metadata.sequence_id = metadata.get("sequence_id")
        message_data.metadata.timestamp = metadata.get("timestamp")
        message_data.metadata.account = metadata.get("account")
        message_data.metadata.session_id = metadata.get("session_id")
        if qubit_mode is not None:
            mode_value = int(qubit_mode)
            if mode_value not in (QubitMode.TWO, QubitMode.THREE):
                raise ValueError(f"Invalid qubit mode: {mode_value}")
            message_data.qubit_mode = mode_value
        message_data.json_data = json.dumps(json_data)
        return message_data.SerializeToString()

    def deserialize_payload(self, data: bytes) -> Dict[str, Any]:
        """Decode one complete WebSocket binary frame as one BaseMessage."""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ProtocolFrameError("WebSocket business frame must be binary")
        if len(data) > self.max_frame_length:
            raise ProtocolFrameError(
                "WebSocket frame payload length "
                f"{len(data)} exceeds configured maximum {self.max_frame_length}"
            )
        try:
            return self._decode_payload(bytes(data))
        except Exception as exc:
            raise ProtocolFrameError(f"Invalid BaseMessage payload: {exc}") from exc

    def _decode_payload(self, message_data: bytes) -> Dict[str, Any]:
        """Decode one complete BaseMessage payload without a TCP header."""
        if not message_data:
            raise ProtocolFrameError("Empty business message payload")
        message = message_pb2.BaseMessage()
        message.ParseFromString(message_data)
        if not message.msg_id.strip():
            raise ProtocolFrameError("Business message must contain a non-empty msg_id")

        metadata = {
            "sequence_id": message.metadata.sequence_id,
            "timestamp": message.metadata.timestamp,
            "account": message.metadata.account,
            "session_id": message.metadata.session_id,
        }
        qubit_mode_present = message.HasField("qubit_mode")
        qubit_mode = int(message.qubit_mode) if qubit_mode_present else int(QubitMode.TWO)
        dict_data = {
            "msg_id": message.msg_id,
            "metadata": metadata,
            "qubit_mode_present": qubit_mode_present,
            "qubit_mode": qubit_mode,
            "qubit_mode_valid": qubit_mode in (QubitMode.TWO, QubitMode.THREE),
        }

        message_type = message.WhichOneof("message_type")
        if message_type == "chart_data":
            dict_data["chart_data"] = {
                "taskId": message.chart_data.task_id,
                "group": message.chart_data.group,
                "chart_name": message.chart_data.chart_name,
                "path": message.chart_data.path,
                "qubit": message.chart_data.qubit,
                "step": message.chart_data.step,
                "points": [[point.x, point.y] for point in message.chart_data.points],
            }
        elif message_type == "json_data":
            dict_data["json_data"] = json.loads(message.json_data)

        return dict_data

    def deserialize_messages(self, data: bytes) -> List[Dict[str, Any]]:
        """Consume a TCP byte chunk and return every complete frame in order.

        Incomplete trailing bytes remain buffered for the next call. A malformed
        header or an excessive payload length is a fatal protocol error: the
        receive buffer is cleared and the caller must close the connection.
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data must be bytes-like")
        self.remaining_data += bytes(data)
        messages: List[Dict[str, Any]] = []

        try:
            while len(self.remaining_data) >= 8:
                magic, length = struct.unpack('>II', self.remaining_data[:8])
                if magic != self.HEADER_MAGIC:
                    raise ProtocolFrameError(
                        f"Invalid header magic number: 0x{magic:08X}"
                    )
                if length > self.max_frame_length:
                    raise ProtocolFrameError(
                        "TCP frame payload length "
                        f"{length} exceeds configured maximum {self.max_frame_length}"
                    )

                total_length = 8 + length
                if len(self.remaining_data) < total_length:
                    break

                payload = self.remaining_data[8:total_length]
                self.remaining_data = self.remaining_data[total_length:]
                try:
                    messages.append(self._decode_payload(payload))
                except Exception as exc:
                    raise ProtocolFrameError(
                        f"Invalid BaseMessage payload: {exc}"
                    ) from exc
        except ProtocolFrameError:
            self.remaining_data = b''
            self._decoded_messages.clear()
            raise

        return messages

    def deserialize_message(self, data: bytes) -> Tuple[bool, Dict[str, Any]]:
        """
        Parse binary data into a protobuf message and handle
        packet sticking/splitting issues.

        Args:
            data: Received binary data.

        Returns:
            Tuple[bool, Dict[str, Any]]: (success flag, parsed message dict).
        """
        if data:
            self._decoded_messages.extend(self.deserialize_messages(data))
        elif not self._decoded_messages:
            self._decoded_messages.extend(self.deserialize_messages(b''))

        if not self._decoded_messages:
            return False, {}
        return True, self._decoded_messages.popleft()
