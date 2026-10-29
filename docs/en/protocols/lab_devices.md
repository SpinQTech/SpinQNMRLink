# Lab device snapshots and callback models

These types and callback methods belong to the private Lab adapter, not the public device API. Public users inspect `lab.is_ready`, `lab.capabilities` and returned `ExperimentResult` objects; see [devices](../devices.rst), [API reference](../api.rst) and [results](../parameters.rst).

This page introduces the data types commonly used for device information and event callbacks. Refer to the device documentation for the meaning and permitted range of individual device parameters.

## Device snapshots

- `DeviceInfo`: stable fields are `connected`, `lock_state` and `temperature`, decoded from `connected`, `lockState` and `temperature` in `s_post_device_info`.
- `s_post_device_param`: preserves `pulseParam`, `ppsParam`, `sampleParam`, `lockParam`, `shimmingParam`, `currentShimming` and all raw fields.
- `s_post_sample_calibration_data`: read sample calibration results with `get_sample_calibration()`. The returned value contains `sampleLock`, `calibrateResult`, and `raw`; missing calibration values are `None`.
- `s_post_lock_data`: access the original lock data JSON through `raw`.

Fields without a dedicated definition remain available in `raw` or in the original event.

## Experiment and queue events

- `QueueSnapshot`: mode, queue, and `current_task_id`.
- `ProtocolEvent`: `msg_id`, mode, payload type, payload, and the complete envelope.
- `UnknownMessage`: a message the SDK does not recognize.
- `ChartKey`: identifies chart data by `task_id`, `group`, `chart_name`, `path`, `qubit`, and `step`.

These snapshots and events describe backend decoding; they are not all exposed through public device methods. `get_sample_calibration()` is also a private backend method.

Private backend callbacks run on a separate thread. If the event queue fills, the receive thread waits for space instead of dropping events. Public `lab.close()` disconnects the backend and stops its callback thread; opening a new session starts new workers.

If a callback raises an exception, the SDK records it and continues receiving subsequent messages. Avoid long-running work inside a callback.

## Two-qubit and three-qubit data

Device, calibration, queue, task-state and spectrum data are isolated by `QubitMode.TWO` and `QubitMode.THREE`. After a mode change the SDK waits for device information, parameters and queue snapshots for that mode.
