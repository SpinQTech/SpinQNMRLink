# Changelog

## 1.0.0 — pending first public release / 首次公开发布前整理（2026-10-27）

### SDK fixes / SDK 修复

- Physical tasks accept `task_started_post` and `custom_task_started_post`, retain the first matching start, populate timing metadata and apply execution timeout after start. / 物理层兼容两种开始通知，保留首次有效开始时间，填充阶段计时，并在开始后正确使用执行超时。

- Density-matrix support through `calcMatrix: true` requires Triangulum client 2.0 or newer. / `calcMatrix: true` 密度矩阵功能要求三角座客户端 2.0 及以上版本。

- Triangulum circuit requests send top-level `calcMatrix` from strict Boolean `calc_matrix` (default true). True requests density components; false accepts probabilities with empty matrix arrays, retaining a state vector only if supplied. Nonempty component counts are validated. / 三角座电路请求顶层发送 `calcMatrix`，公开参数 `calc_matrix` 默认为 true；true 请求密度矩阵，false 时兼容概率结果与空矩阵数组，仅在实际返回时保留状态向量，并校验非空分量数量。

- Sampling frequency is one strict integer choice: 10000, 20000, 50000 or 100000 Hz. Public example parameters reject other values before submission. / 采样率为严格整数四选一，示例参数在提交前拒绝其他值。
- `run(timeout=..., queue_timeout=...)` separates execution and queue waiting; acknowledgement keeps its own budget. Queue waiting defaults to unlimited. Local timeouts do not cancel or replay tasks. Results and timeout errors include phase information. / 分离执行、排队和提交确认时限，排队默认不限时；本地超时不取消、不重放任务，结果及超时异常包含阶段信息。
- `subscribe_disconnect()` and retained disconnect details expose transport/heartbeat failures with credential redaction. Queue waiting keeps heartbeat monitoring active; callbacks and concurrent close operations clean up safely. / 提供断连订阅及保留的脱敏诊断，排队期间持续监测心跳，并修复回调及并发关闭流程。
- Triangulum accepts optional circuit matrices and preserves vector/density-matrix components without guessing matrix order. Lab circuit result types follow the submitted mode. / 三角座兼容可选电路矩阵，保留向量及密度矩阵分量且不猜测排列顺序；Lab 结果类型与提交模式一致。
- Lab distinguishes WebSocket control frames from business data and rejects empty/malformed messages. Transport failures notify once per connection. / Lab 区分 WebSocket 控制帧与业务数据，拒绝空报文和异常报文，每次连接的传输故障只通知一次。
- Configuration examples use literals: Lab reserved credentials and Triangulum User Center credentials. Environment references remain optional. / 配置示例使用字面值，分别说明 Lab 预留字段和三角座用户中心凭据，环境变量引用仍可选。

### Distribution and validation / 打包与验证

- Local client integration verified both circuit matrix modes and physical FID/FFT acquisition. Physical phase timing accepts both generic and custom start notifications. / 本机客户端已验证电路矩阵两种模式及物理 FID/FFT 采集；物理阶段计时已兼容通用及专用开始通知。

- Example JSON in source archives is limited to the public manifest and configuration template. Local profiles are excluded, including cached manifest entries; distribution checks reject unapproved configurations before installation. / 示例 JSON 只打包公开清单与配置模板，排除本地配置及缓存条目，并在安装前检查发行包内容。
- Default mypy applies the existing NumPy/Pydantic skip policy to their stubs, preserving the Python 3.8 target and public-source checks. / 默认 mypy 将已有依赖跳过规则应用到类型声明，保持 Python 3.8 目标及公开源码检查范围。
- Current local checks, environment and pending platform/hardware work are recorded in [validation_status.json](validation_status.json). This is an unpublished local candidate. / 当前离线验证、环境及待完成的平台和实机验证见验证记录；本条描述尚未公开发布的本地候选版本。

### Initial scope / 初始功能范围

- One `spinqnmrlink` SDK for independent Lab and Triangulum device sessions.
- A catalogue of 35 experiments with typed snake_case parameters and offline protocol checks.
- Explicit execution deadlines and distinct task failure states.
- Both device adapters communicate directly in Python; network workers start when a device opens.
- Chinese and English documentation with per-page language switching.
- Standalone Python examples with English parameter explanations and measurement access, four separate Lab TWO chapters, advanced offline/save workflows, measured-data scans and development checks.

Hardware validation and unsupported-platform plans are recorded separately in `validation_status.json`.
