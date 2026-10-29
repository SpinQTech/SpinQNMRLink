# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Request/response models for the SpinQLAB communication protocol."""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import threading
import time
from typing import Any, Dict, Optional

from ..utils.types import QubitMode


class ProtocolErrorCode(IntEnum):
    """Known response codes while preserving unknown raw integer codes."""

    SUCCESS = 0
    LOGIN_REPEAT_LOGIN = 1
    LOGIN_ACCOUNT_PASSWD_ERROR = 2
    NOT_LOGIN = 998
    UNKNOWN_ERROR = 999
    QUBIT_MODE_MISMATCH = 1001
    QUBIT_MODE_UNSUPPORTED = 1002
    QUBIT_RUNTIME_NOT_READY = 1003
    INVALID_QUBIT_MODE = 1004


class RequestRecoveryAction(str, Enum):
    """Caller action prescribed by protocol v2.0 response semantics."""

    NONE = "NONE"
    REFRESH_MODE = "REFRESH_MODE"
    USE_SUPPORTED_MODE = "USE_SUPPORTED_MODE"
    RETRY_LATER = "RETRY_LATER"
    FIX_REQUEST = "FIX_REQUEST"


@dataclass(frozen=True)
class RequestResponse:
    """Completed response correlated with the request that produced it."""

    sequence_id: int
    request_msg_id: str
    response_msg_id: str
    target_qubit_mode: Optional[QubitMode]
    server_qubit_mode: Optional[QubitMode]
    raw_code: int
    message: str
    task_id: Optional[str]
    raw_data: Dict[str, Any]

    @property
    def success(self) -> bool:
        return self.raw_code == ProtocolErrorCode.SUCCESS

    @property
    def known_error(self) -> Optional[ProtocolErrorCode]:
        try:
            return ProtocolErrorCode(self.raw_code)
        except ValueError:
            return None

    @property
    def caller_may_retry(self) -> bool:
        """Whether the protocol explicitly leaves retry to the caller."""
        return self.raw_code == ProtocolErrorCode.QUBIT_RUNTIME_NOT_READY

    @property
    def must_not_retry_unchanged(self) -> bool:
        """Whether resending the identical request would violate the protocol."""
        return self.raw_code in (
            ProtocolErrorCode.QUBIT_MODE_UNSUPPORTED,
            ProtocolErrorCode.INVALID_QUBIT_MODE,
        )

    @property
    def recommended_action(self) -> RequestRecoveryAction:
        """Translate protocol error semantics without performing the action."""
        return {
            int(ProtocolErrorCode.QUBIT_MODE_MISMATCH): RequestRecoveryAction.REFRESH_MODE,
            int(ProtocolErrorCode.QUBIT_MODE_UNSUPPORTED): RequestRecoveryAction.USE_SUPPORTED_MODE,
            int(ProtocolErrorCode.QUBIT_RUNTIME_NOT_READY): RequestRecoveryAction.RETRY_LATER,
            int(ProtocolErrorCode.INVALID_QUBIT_MODE): RequestRecoveryAction.FIX_REQUEST,
        }.get(self.raw_code, RequestRecoveryAction.NONE)


@dataclass
class PendingRequest:
    """Internal request state retained until a matching response arrives."""

    session_id: str
    sequence_id: int
    request_msg_id: str
    expected_response_msg_id: str
    target_qubit_mode: Optional[QubitMode]
    task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed: threading.Event = field(default_factory=threading.Event, repr=False)
    response: Optional[RequestResponse] = field(default=None, repr=False)
    error: Optional[BaseException] = field(default=None, repr=False)
    timeout_timer: Optional[threading.Timer] = field(default=None, repr=False)


class QubitModeMismatchError(RuntimeError):
    """Raised before sending when target mode differs from the server mode."""


class QubitModeUnsupportedError(RuntimeError):
    """Raised before sending a mode the SDK or server has rejected."""


class RequestResponseTimeoutError(TimeoutError):
    """Raised when a tracked request does not receive its response in time."""


class RequestOutcomeUnknownError(ConnectionError):
    """Raised when transport loss makes an in-flight request outcome unknown."""


class DuplicateTaskIdError(RuntimeError):
    """Raised before sending a task ID already used by this client instance."""
