# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Initialize connection module.
"""

from .connection import TCPConnection, WebSocketConnection
from .protocol import Protocol
from .heartbeat import HeartbeatManager
from .events import ChartKey, ProtocolEvent, QueueSnapshot, UnknownMessage
from .models import ChartChunk, DeviceInfo, QubitModeCapability, Task, TaskState
from .request import (
    DuplicateTaskIdError,
    ProtocolErrorCode,
    RequestRecoveryAction,
    QubitModeMismatchError,
    QubitModeUnsupportedError,
    RequestOutcomeUnknownError,
    RequestResponse,
    RequestResponseTimeoutError,
)

__all__ = [
    'TCPConnection',
    'WebSocketConnection',
    'Protocol',
    'HeartbeatManager',
    'ChartKey',
    'ProtocolEvent',
    'QueueSnapshot',
    'UnknownMessage',
    'ChartChunk',
    'DeviceInfo',
    'QubitModeCapability',
    'Task',
    'TaskState',
    'DuplicateTaskIdError',
    'ProtocolErrorCode',
    'RequestRecoveryAction',
    'QubitModeMismatchError',
    'QubitModeUnsupportedError',
    'RequestOutcomeUnknownError',
    'RequestResponse',
    'RequestResponseTimeoutError',
]
