参数单位与结果
==============

``parameters_for(key)`` 返回该实验的精确类型模型，字段统一为 snake_case。``parameters.to_wire()`` 可离线验证并保留原服务端协议。

``Pulse`` 使用 ``channel``（从零编号）、``width_us``、``amplitude_percent``、``phase_deg``、``detuning_hz``。``Gradient`` 使用 ``path``、``voltage_v``、``duration_us``。线路门的比特索引从零编号，旋转角使用度。公开 Lab THREE ``sample_qubits`` 也从零编号，由适配器转换为协议编号 1、2、3。Triangulum 物理层的 ``sample_qubits`` 沿用设备 ``sampleQubit`` 协议原值，不执行 Lab THREE 的编号转换。

公开弛豫时间使用秒，Triangulum 物理层序列化时转换为微秒。
Lab TWO 采样点数一般须为 1024 到 16384 的二次幂；
``lab.two.spin_echo`` 另允许 16000。Triangulum 物理层允许 1 到 16000。
THREE 由自身模型验证，不混用不同实验的采样范围。
采样频率必须是单个整数 Hz，仅允许 ``10000、20000、50000、100000`` 四档。30000、40000 等范围内的非档位值也不支持；浮点数、文本、布尔值和列表均拒绝。

各实验页面的参数表由实际模型与参考值生成。参考值用于配置演示，不代表实际校准结果。模型与序列化器共同定义约束；没有明确单位的设备频率设置保持原值，不擅自换算。

``ExperimentResult`` 包含设备类型、实验键、可获取的任务 ID、远端状态、原接口数据及元信息（SDK 版本、UTC 时间、实际公开参数）。``data`` 选择 Lab 的结果对象或 Triangulum 的直接数据。未返回的可选字段按适配器行为保持缺失或 ``None``，不以合成值代替测量。复数导出为实部/虚部对象，非有限数值禁止导出为 JSON。

Triangulum 线路要求概率数组符合提交线路的维度，保真度、态向量、比特数回显和坐标为可选字段。
``assess_result`` 在存在实际提交参数时按其核对维度，不因省略可选字段将正常结果判为不完整。
科学评估仍为 NOT_ASSESSED。

Triangulum 物理实验完成时，图表须可解码且至少包含一个有限数值点。
压缩图表要求 Qt 长度头与解压后内容严格一致，解码内容最多为 64 MiB；
损坏或空图表报告结果处理失败，返回结果保留原始图表表示。

提交拒绝、本地处理或远端失败、终止、本地等待超时、提交结果未知分别报错。本地超时不取消远端任务，也不证明任务结束。未解决任务的会话禁止继续提交；显式关闭并重新打开会建立新会话，操作前应在设备端核对原任务。自动重连不重发实验。

Lab THREE 也使用公共脉冲和梯度模型：``pulse.h_pulse`` 只接受通道 0，梯度时长须为整数微秒。三比特线路使用公共 ``Circuit(qubits=3, ...)`` 模型。


可选 ``execution_matrix`` 缺失或为 null 时只返回实际概率。若有 ``2^n`` 个复数位置，保留 ``state_vector``；若有 ``(2^n)^2`` 个位置，则返回 ``density_matrix``，含原始平铺 ``real``/``imag``、``shape=[2^n, 2^n]`` 和 ``order=None``。``None`` 明确表示行列存储顺序未知，SDK 不擅自重排为二维矩阵。错误维度或实虚长度不一致仍报解析错误。

时间元数据中的 ``submitted_at_utc`` 为提交调用时刻，``acknowledged_at_utc`` 为接受回执的本地观察时刻，``execution_started_at_utc`` 为首次有效开始通知时刻，``finished_at_utc`` 为完成的本地观察时刻。旧 ``started_at_utc`` 保留为提交调用时刻，不能视为设备执行开始。``queue_duration_seconds`` 从接受到开始计算，``execution_duration_seconds`` 从开始到完成计算；started 先于 ACK 时排队时长记为 0。只有合法终态而没有开始通知时，执行开始和两项时长均为 ``None``，不猜测设备计时。这些值均为 SDK 本地观测，不是设备墙钟。

三角座物理层阶段计时同时识别匹配任务的 ``task_started_post`` 和
``custom_task_started_post``。重复通知保留首次时间，匹配开始后由排队等待切换到执行等待。
