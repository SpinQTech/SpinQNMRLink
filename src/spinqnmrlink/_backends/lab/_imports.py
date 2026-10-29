# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
SpinQLabLink

Responsible for managing device connections and disconnections,
retrieving connection status, accessing the experiment manager,
and obtaining device information.
"""

from collections import OrderedDict
from typing import Dict, Any, List, Optional, Tuple, Union
import time
import uuid
import threading
from spinqnmrlink._backends.lab.connection.connection import TCPConnection, WebSocketConnection
from spinqnmrlink._backends.lab.utils import LoggerManager
from spinqnmrlink._backends.lab.utils.logger import summarize_payload
from spinqnmrlink._backends.lab.connection.protocol import Protocol, ProtocolFrameError
from spinqnmrlink._backends.lab.connection.heartbeat import HeartbeatManager
from spinqnmrlink._backends.lab.connection.events import (
    ChartKey,
    OrderedCallbackDispatcher,
    OrderedEventDispatcher,
    ProtocolEvent,
    QueueSnapshot,
    UnknownMessage,
)
from spinqnmrlink._backends.lab.connection.models import QubitModeCapability, Task, TaskState
from spinqnmrlink._backends.lab.connection.json_models import normalize_common_json
from spinqnmrlink._backends.lab.connection.request import (
    DuplicateTaskIdError,
    PendingRequest,
    ProtocolErrorCode,
    QubitModeMismatchError,
    QubitModeUnsupportedError,
    RequestOutcomeUnknownError,
    RequestResponse,
    RequestResponseTimeoutError,
)
from spinqnmrlink._backends.lab.device.device import Device
from spinqnmrlink._backends.lab.utils.types import ConnectionState, ExperimentState, ExperimentType, MachineType, QubitMode
from spinqnmrlink._backends.lab.experiment.ExperimentManager import ExperimentManager
from spinqnmrlink._backends.lab.experiment.exp_three_qubit import ThreeQubitExperiment
from spinqnmrlink._backends.lab.experiment.three_qubit_models import THREE_QUBIT_PARAMETER_TYPES

# Create logger
logger = LoggerManager.get_logger(name='spinqnmrlink._backends.lab')
