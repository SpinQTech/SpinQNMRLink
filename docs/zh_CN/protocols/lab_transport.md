# Lab 连接与传输配置

示例使用公开 SDK，下方内部连接状态供适配器开发参考；内部后端方法不是公开设备方法。本地配置与凭据设置见[配置说明](../configuration.rst)，公开调用见 [API 文档](../api.rst)。

Lab 可以通过 TCP 或 WebSocket 连接实验设备。连接方式在创建客户端时指定，后续的登录和实验操作相同。

## TCP 连接

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

填写设备服务的实际地址与端口。公开 `LabSettings` 的 `host`、`port`、`account` 和 `password` 必填，只有 `transport` 默认为 `"tcp"`。8181 为示例服务端口。

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

实验平台提供 WebSocket 地址时，将 `transport` 设为 `"websocket"`，并按实际地址填写端口和路径。上例连接的地址为 `ws://192.0.2.20:8181/ws`。

如果实验平台提供 `wss://` 地址，可将 `websocket_secure` 设为 `True`：

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

## 连接参数

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `port` | 必填 | TCP 或 WebSocket 服务端端口，范围为 1 至 65535 |
| `transport` | `"tcp"` | 可选 `tcp` 或 `websocket`；公开配置不接受 `ws` |
| `connection_timeout` | `10.0` 秒 | 建立连接的超时时间 |
| `max_frame_length` | `16 MiB` | 单条 TCP/WS Protobuf 消息的最大长度 |
| `websocket_path` | `"/ws"` | WebSocket URL 路径 |
| `websocket_secure` | `False` | `False` 使用 ws，`True` 使用 wss |
| `heartbeat_interval` | `15.0` 秒 | 心跳发送间隔 |
| `heartbeat_missed_periods` | `2` | 超时前允许缺失的心跳周期数 |
| `auto_reconnect` | `True` | 非主动断开后是否重连 |
| `reconnect_initial_delay` | `1.0` 秒 | 首次重连延迟 |
| `reconnect_max_delay` | `30.0` 秒 | 重连延迟上限 |
| `reconnect_multiplier` | `2.0` | 重连退避倍率 |
| `request_timeout` | `10.0` 秒 | 已跟踪请求的响应超时 |
| `response_cache_size` | `256` | 已完成请求的响应缓存数量 |
| `event_queue_size` | `256` | 事件与公开回调队列容量 |
| `retain_chart_points` | `True` | 是否在内存中保留图表点数据 |
| `device_id` | `None` | 客户端设备编号；未指定时自动生成 |

## 连接状态

公开 `lab.open()` 在超时范围内连接、认证并等待权威设备状态，返回时 `lab.is_ready` 为真；连接或同步失败会抛出异常。公开 `lab.close()` 释放连接与线程，不取消远端任务。SDK 退出上下文时关闭其所有设备会话。

内部后端在此过程中使用以下连接状态：

- `DISCONNECTED`：未连接或连接已断开；
- `CONNECTED`：网络连接已建立；
- `AUTHENTICATED`：登录成功；
- `READY`：设备状态已同步，可以提交实验。

网络意外中断且 `auto_reconnect=True` 时，Lab 内部后端按配置间隔重连。待响应请求可能失败或结果未知，自动重连不会重发实验。重新打开会话前，须在设备端核对未解决任务。显式 `lab.close()` 不会触发自动重连。

## 网络安全

TCP 和 `ws://` 连接本身不加密，适合在可信局域网中使用。如果需要通过其他网络连接实验设备，应配置以下一种保护方式：

- TLS 代理或 `wss://`；
- VPN；
- SSH 等安全隧道；
- 等效的受控内网链路。

日志不会记录密码或完整的会话 ID，但这不能代替连接加密。
