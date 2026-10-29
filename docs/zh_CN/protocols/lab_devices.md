# Lab 设备快照与回调模型

这些类型和回调方法属于 Lab 内部适配器，不是公开设备 API。公开用户通过 `lab.is_ready`、`lab.capabilities` 和返回的 `ExperimentResult` 查看状态与结果，详见[设备说明](../devices.rst)、[API 文档](../api.rst)和[结果说明](../parameters.rst)。

本页介绍设备信息和事件回调中常用的数据类型。设备参数的具体含义和允许范围请参考设备说明。

## 设备快照

- `DeviceInfo`：稳定字段为 `connected`、`lock_state`、`temperature`，来自
  `s_post_device_info` 中的 `connected`、`lockState`、`temperature`。
- `s_post_device_param`：保留 `pulseParam`、`ppsParam`、`sampleParam`、
  `lockParam`、`shimmingParam`、`currentShimming` 及原始字段。
- `s_post_sample_calibration_data`：通过 `get_sample_calibration()` 读取样品标定结果。返回值包含 `sampleLock`、`calibrateResult` 和 `raw`；未提供的标定值为 `None`。
- `s_post_lock_data`：可通过 `raw` 读取锁场数据的原始 JSON。

没有单独定义的字段会保存在 `raw` 或原始事件中，用户可以在需要时读取。

## 实验和队列事件

- `QueueSnapshot`：模式、队列和 `current_task_id`。
- `ProtocolEvent`：`msg_id`、模式、载荷类型、载荷和完整信封。
- `UnknownMessage`：SDK 尚未识别的消息。
- `ChartKey`：由 `task_id`、`group`、`chart_name`、`path`、`qubit` 和 `step` 组成的图表数据标识。

这些快照与事件描述后端解码过程，并非全部通过公开设备方法暴露。`get_sample_calibration()` 也属于内部后端方法。

内部后端回调在独立线程中运行。事件队列满时，接收线程会等待队列腾出空间，事件不会因队列已满而丢失。公开 `lab.close()` 断开后端并停止回调线程，重新打开会话时启动新的线程。

回调函数发生异常时，SDK 会继续处理后续消息。回调中不宜执行长时间阻塞的操作。

## 双比特与三比特数据

设备、校准、队列、任务状态和谱线数据分别按照 `QubitMode.TWO` 和
`QubitMode.THREE` 保存。切换比特模式后，SDK 会等待相应模式的设备信息、设备参数和队列信息。
