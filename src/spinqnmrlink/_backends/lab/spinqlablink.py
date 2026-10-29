# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Lab protocol composition. Construction is deferred until Device.open()."""
from ._imports import *  # noqa: F403
from ._session import SessionMixin
from ._requests import RequestsMixin
from ._modes import ModesMixin
from ._events import EventsMixin
from ._tasks import TasksMixin


class SpinQLabLink(SessionMixin, RequestsMixin, ModesMixin, EventsMixin, TasksMixin):
    def __init__(
        self,
        host: str,
        port: int = 8181,
        account: str = "",
        password: str = "",
        connection_timeout: float = 10.0,
        max_frame_length: int = Protocol.DEFAULT_MAX_FRAME_LENGTH,
        transport: str = "tcp",
        websocket_path: str = "/ws",
        websocket_secure: bool = False,
        heartbeat_interval: float = 15.0,
        heartbeat_missed_periods: int = 2,
        auto_reconnect: bool = True,
        reconnect_initial_delay: float = 1.0,
        reconnect_max_delay: float = 30.0,
        reconnect_multiplier: float = 2.0,
        request_timeout: float = 10.0,
        response_cache_size: int = 256,
        event_queue_size: int = 256,
        retain_chart_points: bool = True,
        device_id: Optional[str] = None,
    ):
        normalized_transport = str(transport).strip().lower()
        if normalized_transport == "tcp":
            self.connection = TCPConnection(host, port, timeout=connection_timeout)
        elif normalized_transport in ("ws", "websocket"):
            self.connection = WebSocketConnection(
                host,
                port,
                timeout=connection_timeout,
                path=websocket_path,
                secure=websocket_secure,
            )
            normalized_transport = "websocket"
        else:
            raise ValueError("transport must be 'tcp', 'ws', or 'websocket'")
        self.transport = normalized_transport
        self.connection.set_message_callback(self._handle_transport_data)
        self.connection.set_disconnect_callback(self._on_transport_disconnected)
        self.protocol = Protocol(max_frame_length=max_frame_length)
        self.hardware_connected = False
        self.is_connected = False
        self.logging_in = False
        self.is_logged_in = False
        self._connection_state_lock = threading.RLock()
        self.connection_state = ConnectionState.DISCONNECTED
        self.auto_reconnect = bool(auto_reconnect)
        if reconnect_initial_delay < 0 or reconnect_max_delay < 0:
            raise ValueError("reconnect delays must be non-negative")
        if reconnect_multiplier < 1:
            raise ValueError("reconnect_multiplier must be at least 1")
        self.reconnect_initial_delay = float(reconnect_initial_delay)
        self.reconnect_max_delay = float(reconnect_max_delay)
        self.reconnect_multiplier = float(reconnect_multiplier)
        self._manual_disconnect = False
        self._disconnect_callback = None
        self.last_disconnect_reason = None
        self._reconnect_stop = threading.Event()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_lock = threading.Lock()
        self.account = account
        self.password = password
        LoggerManager.register_secret(account)
        LoggerManager.register_secret(password)
        if device_id is not None and (
            not isinstance(device_id, str) or not device_id.strip()
        ):
            raise ValueError("device_id must be a non-empty string or None")
        self.device_id = (
            device_id.strip()
            if device_id is not None
            else f"SpinQLabLink-{str(uuid.uuid4()).upper()}"
        )
        self.session_id = ""
        self._qubit_mode_lock = threading.RLock()
        self._current_qubit_mode: Optional[QubitMode] = QubitMode.TWO
        self.qubit_mode_protocol_error: Optional[str] = None
        self._sequence_lock = threading.Lock()
        self._sequence_id = 0
        self._request_lock = threading.RLock()
        self._pending_requests: Dict[Tuple[str, int], PendingRequest] = {}
        if request_timeout <= 0:
            raise ValueError("request_timeout must be positive")
        if not isinstance(response_cache_size, int) or response_cache_size <= 0:
            raise ValueError("response_cache_size must be a positive integer")
        self.request_timeout = float(request_timeout)
        self.response_cache_size = response_cache_size
        self._request_responses: OrderedDict[int, RequestResponse] = OrderedDict()
        self._request_errors: OrderedDict[int, BaseException] = OrderedDict()
        self._last_request_error: Optional[RequestResponse] = None
        self._duplicate_response_count = 0
        self._unmatched_response_count = 0
        self._submitted_task_ids = set()
        self._sdk_supported_qubit_modes = frozenset((QubitMode.TWO, QubitMode.THREE))
        self._unsupported_qubit_modes = set()
        self.retain_chart_points = bool(retain_chart_points)
        self._event_observers = []
        self._unknown_message_observers = []
        self._chart_consumers = []
        self._mode_chart_consumers = []
        self._connection_state_observers = []
        self._qubit_mode_observers = []
        self._observer_lock = threading.RLock()
        self._event_queue_size = event_queue_size
        self._observer_dispatcher = OrderedCallbackDispatcher(maxsize=event_queue_size)
        self._experiment_decoders: Dict[str, Any] = {}
        self._queue_snapshots_by_mode: Dict[QubitMode, QueueSnapshot] = {}
        self._sample_calibration_by_mode: Dict[QubitMode, Dict[str, Any]] = {}
        self._chart_streams_by_mode: Dict[
            QubitMode, Dict[ChartKey, Dict[str, Any]]
        ] = {}
        self._active_chart_boundaries_by_mode: Dict[QubitMode, set] = {}
        self._task_states_by_mode: Dict[QubitMode, Dict[str, str]] = {}
        self._required_mode_snapshot_kinds = frozenset(
            ("device_info", "device_param", "queue")
        )
        self._received_mode_snapshot_kinds: Dict[QubitMode, set] = {}
        self._mode_snapshot_sync_pending: Optional[QubitMode] = None
        self._event_dispatcher = OrderedEventDispatcher(
            self._dispatch_received_message,
            maxsize=event_queue_size,
        )

        # Runtime state is isolated by qubit mode.  The public ``device``,
        # ``expMgr`` and ``exp_handler_map`` attributes remain compatibility
        # aliases for the currently authoritative mode.
        self._devices_by_mode: Dict[QubitMode, Device] = {}
        self._experiment_managers_by_mode: Dict[QubitMode, ExperimentManager] = {}
        self._exp_handler_maps_by_mode: Dict[QubitMode, Dict[str, Any]] = {}
        self._experiment_queues_by_mode: Dict[QubitMode, List[Dict[str, Any]]] = {}
        self._activate_mode(QubitMode.TWO, reset_runtime_snapshots=True)

        # Heartbeat manager
        self.heartbeat_manager = HeartbeatManager(
            self._send_message,
            interval=heartbeat_interval,
            missed_periods=heartbeat_missed_periods,
        )
        self.heartbeat_manager.set_timeout_callback(self._on_heartbeat_timeout)

        self.handler_map = {
            MachineType.MSG_RES_USER_LOGIN: self._handle_user_login_res,
            MachineType.MSG_RES_USER_LOGOUT: self._handle_user_logout_res,
            MachineType.MSG_RES_HEARTBEAT: self._handle_heartbeat_res,
            MachineType.MSG_POST_QUBIT_MODE_CHANGED: self._handle_qubit_mode_changed,
            MachineType.MSG_POST_PARAM: self._handle_device_param_post,
            MachineType.MSG_POST_LOCK_DATA: self._handle_lock_data_update_post,
            MachineType.MSG_POST_INFO: self._handle_device_info_post,
            MachineType.MSG_POST_SAMPLE_CALIBRATION: self._handle_sample_calibration_post,
            MachineType.MSG_POST_EXP_QUEUE_UPDATE: self._handle_exp_queue_update_post,
            MachineType.MSG_RES_ADD_EXP_TASK_RES: self._handle_business_response,
            MachineType.MSG_RES_TERMINATE_EXP_TASK_RES: self._handle_business_response,
        }
