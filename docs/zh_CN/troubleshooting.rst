故障排查
============

若无法导入 SDK，先执行 ``conda activate spinqnmrlink``，确认 IDE 选中同一环境；在项目根目录运行 ``python -m pip show SpinQNMRLink``。环境名称若自定，使用实际名称。不要依赖仓库内固定的解释器路径。

配置失败时检查顶层设备名称、端口类型和范围、环境变量。配置错误会省略凭据输入值。

Lab 已连接但未就绪时，确认登录成功，且服务端已提供权威模式、设备信息、参数和队列状态。TWO 模式不能执行 THREE 任务。选择 WebSocket/WSS 不会开启服务端端点。

Triangulum 连接失败时检查设备 WebSocket 服务、地址、端口、路径、ws/wss 设置和凭据。登录返回 ``return_code=2`` （账号或密码错误）时，确认已在三角座客户端软件的 **用户中心** 创建用户账号和密码，并在连接配置中使用同一组凭据，步骤见 :doc:`configuration`。心跳或协议异常会关闭会话，未解决任务在重新打开前须核对设备队列。

三角座物理层实验（``triangulum.physical``）需要 **三角座客户端软件 1.6.1 及以上版本**；较低版本不支持该实验。连接和登录成功后仍无法运行物理实验时，先检查客户端版本，详见 :doc:`triangulum/physical`。

回执丢失或本地等待超时后，应记录任务 ID 和最后状态，到设备队列核对并处理该任务，再决定重连或运行。本地清理后远端任务仍可能继续，不能重发结果不明确的提交。

Triangulum 成功通知中的必需测量若缺失或异常，执行接口报告实验失败。对于已返回的结果，评估工具将缺失或无效的测量标记为结构不完整，不代表科学成功。Rabi 或弛豫拟合不佳时应检查脉冲校准、样品、扫描范围及原始测量。


异常断开诊断
------------

通过公共 Device 订阅异常断开，无须访问私有后端：

.. code-block:: python

   unsubscribe = device.subscribe_disconnect(
       lambda event: print(event.reason, event.task_ids, dict(event.diagnostics))
   )
   device.open()
   # ... run experiments ...
   device.close()
   print(device.last_disconnect_reason)
   unsubscribe()

正常主动关闭不触发故障事件；真实异常保留首个原因并通知一次。``last_disconnect_event`` 和 ``last_disconnect_reason`` 在 close 后保留，新一轮 open 时重置。回调在独立观察线程执行，应及时返回；一个回调抛异常不影响其他回调。关闭会在预算内处理已排队通知；阻塞回调超过关闭预算会报告清理超时。

三角座心跳诊断包含最近接收、最近发送、最近实际心跳发送的本地 monotonic 时刻、空闲秒数和心跳阈值。尚未发出心跳时相应字段为 ``None``；没有版本证据时 ``server_version=None``。凭据从错误原因中隐藏，不上传外部平台。空业务消息、非法 Unicode 和协议错误也会走相同故障通知路径。排队超时可通过 ``ExperimentTimeoutError.phase == "queue"`` 区分于执行超时。
