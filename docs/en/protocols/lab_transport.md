# Lab connection and transport

The examples use the public SDK. Internal connection states are described below for adapter development; private backend methods are not public device methods. See [configuration](../configuration.rst) for local profiles and credential setup, and [API reference](../api.rst) for public calls.

Lab connects to laboratory devices over TCP or WebSocket. Choose the transport when creating the client; login and experiment operations work the same way with either connection.

## TCP connection

```python
from spinqnmrlink import LabSettings, SDKSettings, SpinQNMRLink

settings = LabSettings(
    host="192.0.2.20", port=8181,
    account="env:LAB_ACCOUNT", password="env:LAB_PASSWORD",
    transport="tcp",
)
with SpinQNMRLink(SDKSettings(lab=settings)) as sdk:
    lab = sdk.device("lab")
    lab.open()
    print(lab.is_ready)
```

Enter the actual device service address and port. Public `LabSettings` requires `host`, `port`, `account` and `password`; only `transport` defaults to `"tcp"`. Port 8181 is the example service port.

## WebSocket

```python
from spinqnmrlink import LabSettings, SDKSettings, SpinQNMRLink

settings = LabSettings(
    host="192.0.2.20", port=8181,
    account="env:LAB_ACCOUNT", password="env:LAB_PASSWORD",
    transport="websocket",
    websocket_path="/ws", websocket_secure=False,
)
with SpinQNMRLink(SDKSettings(lab=settings)) as sdk:
    lab = sdk.device("lab")
    lab.open()
    print(lab.is_ready)
```

If the platform provides a WebSocket address, set `transport` to `"websocket"` and enter its port and path. The example above connects to `ws://192.0.2.20:8181/ws`.

If the platform provides a `wss://` address, set `websocket_secure` to `True`:

```python
from spinqnmrlink import LabSettings, SDKSettings, SpinQNMRLink

settings = LabSettings(
    host="192.0.2.20", port=8181,
    account="env:LAB_ACCOUNT", password="env:LAB_PASSWORD",
    transport="websocket",
    websocket_path="/ws", websocket_secure=True,
)
with SpinQNMRLink(SDKSettings(lab=settings)) as sdk:
    lab = sdk.device("lab")
    lab.open()
    print(lab.is_ready)
```

## Connection parameters

| Parameter | Default | Description |
|---|---:|---|
| `port` | Required | TCP or WebSocket server port, from 1 to 65535 |
| `transport` | `"tcp"` | One of `tcp` or `websocket`; `ws` is not accepted by public settings |
| `connection_timeout` | `10.0` seconds | Connection timeout |
| `max_frame_length` | `16 MiB` | Maximum size of one TCP/WS Protobuf message |
| `websocket_path` | `"/ws"` | WebSocket URL path |
| `websocket_secure` | `False` | `False` selects ws; `True` selects wss |
| `heartbeat_interval` | `15.0` seconds | Heartbeat interval |
| `heartbeat_missed_periods` | `2` | Number of missed heartbeat periods allowed before timeout |
| `auto_reconnect` | `True` | Whether to reconnect after an unexpected disconnection |
| `reconnect_initial_delay` | `1.0` second | Initial reconnection delay |
| `reconnect_max_delay` | `30.0` seconds | Maximum reconnection delay |
| `reconnect_multiplier` | `2.0` | Reconnection backoff multiplier |
| `request_timeout` | `10.0` seconds | Timeout for a tracked request response |
| `response_cache_size` | `256` | Number of completed request responses retained in the cache |
| `event_queue_size` | `256` | Capacity of the event and public-callback queue |
| `retain_chart_points` | `True` | Whether to retain chart points in memory |
| `device_id` | `None` | Client device ID; generated automatically when omitted |

## Connection states

Public `lab.open()` connects, authenticates and waits for authoritative device state within its timeout. It returns when `lab.is_ready` is true; a connection or synchronization failure raises an error. Public `lab.close()` releases the connection and workers without cancelling a remote task. SDK context exit closes all its device sessions.

The private backend uses these connection states during that sequence:

- `DISCONNECTED`: not connected;
- `CONNECTED`: the network connection is open;
- `AUTHENTICATED`: login succeeded;
- `READY`: the device state is synchronized and the client can submit experiments.

If the network drops unexpectedly and `auto_reconnect=True`, the private Lab backend retries using the configured delays. Pending requests can fail or have an unknown outcome. Automatic reconnect never replays an experiment; reconcile unresolved tasks on the equipment before opening a fresh session. Explicit `lab.close()` does not trigger automatic reconnect.

## Network security

TCP and `ws://` do not encrypt the connection. Use them only on a trusted local network. For access across other networks, protect the connection with one of these options:

- A TLS proxy or `wss://`;
- VPN；
- A secure tunnel such as SSH;
- An equivalent controlled private-network connection.

Passwords and full session IDs are omitted from logs, but that does not replace transport encryption.
