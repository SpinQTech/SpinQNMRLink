Triangulum JSON WebSocket 协议
==================================

Python 后端通过 WebSocket 文本帧与设备服务通信，URL 由 host、port、websocket_path、websocket_secure 构造，无需设备原生库。

实现边界
------------

``transport.py`` 管理 socket、文本帧、轮询等待和关闭；``protocol.py`` 构造消息并解码测量；``session.py`` 管理认证、心跳、关联任务和有界资源清理。每个会话独立维护状态和一个接收线程。创建 SDK 和准备参数不连接设备。

认证与心跳
------------

.. code-block:: json

   {"msg_id":"user_login_request","account":"<account>","password":"<password>"}
   {"msg_id":"user_login_response","return_code":0,"session_id":"<session>"}
   {"msg_id":"heartbeat","session_id":"<session>"}
   {"msg_id":"user_logout_request","session_id":"<session>","account":"<account>"}

登录成功要求 return_code 为整数零且 session_id 为非空字符串。认证后启动应用层心跳，空闲超时或异常消息流会关闭连接。退出登录在关闭预算内等待，然后释放 socket 和接收线程。

任务请求
------------

.. important::

   **通过 ``calcMatrix: true`` 获取密度矩阵，需要三角座客户端 2.0 及以上版本。**

线路请求顶层增加 ``calcMatrix``，对应公开参数 ``calc_matrix``（默认 ``True``），
与 ``task_gates`` 分开。True 请求密度矩阵分量，False 关闭密度矩阵计算。
关闭时客户端返回的空分量数组表示无矩阵数据，仍可正常读取概率；
物理层请求不添加此字段。

线路消息使用 ``push_task_request``，物理层使用 ``push_custom_task_request``。报文还包含 ``session_id``、``task_id``、``task_name``、``task_description``、``task_qubits``、``task_gates``。线路 task_gates 为门序列定义；物理层为 pulse/parameters 对象，task_qubits 为 3。

任务 ID 是有符号 64 位范围内的正十进制字符串，不依赖秒级时间戳。服务端必须在确认和任务事件中返回对应 task_id。任务 ID 与消息类别都必须匹配当前任务，其他任务或重复消息不能覆盖结果。

.. list-table:: 关联响应
   :header-rows: 1

   * - 线路
     - 物理层
     - 含义
   * - push_task_response
     - push_custom_task_response
     - 提交确认，return_code 零接受，其他代码拒绝
   * - task_started_post
     - custom_task_started_post / task_started_post
     - 任务开始通知
   * - task_finished_post
     - custom_task_finished_post
     - 终态与测量数据

已知状态为 W（等待）、R（运行）、S（成功）、F（失败）。 提交接受后保持 PENDING，收到匹配的开始通知后进入 RUNNING，接受回执不代表已经执行。只有 S 且结果解码成功时才报告 COMPLETED。服务端若返回明确的 T/TERMINATED，也会识别为终止，但不据此声明设备支持相关操作。数据缺失或异常不报告成功。终态先于提交确认到达时暂存，确认接受后才处理。

确认丢失或断线报告提交结果未知，确认后超过本地等待上限报告本地超时。两者都不会重发或取消远端任务。重新连接需显式调用，在再次提交前应于设备端核对未解决的任务。

结果与验证
------------

物理任务对匹配的 task_id 同时接受 ``custom_task_started_post`` 和通用
``task_started_post``。仅首次有效开始通知设置执行时钟；即使开始先于 ACK、
或两个别名重复到达，也不会重置计时。开始后使用执行时限而非排队时限，
接受与结束报文仍按任务类型分别匹配。

线路执行概率和可选 execution_matrix 转成公开字段，可选的保真度、坐标和比特数缺失时保持缺失。物理层先核对图表结构及至少一个有限数值点，再将 graph_result_compressed 保留为 graph。无 GUI 解码器要求 Qt 长度头严格匹配，解码内容最多为 64 MiB；空测量或损坏测量报告处理失败。成功结果中的 ``protocol_raw`` 保留接收的提交确认、开始和结束报文，认证字段会脱敏。

离线数据根据协议实现构造，不是设备测量。本地回环测试验证真实 HTTP WebSocket 握手及客户端掩码帧。硬件、固件和平台安装验证单独记录于 :doc:`../validation`。

.. literalinclude:: ../../../examples/triangulum/circuit.py
   :language: python

根据提交的 ``calc_matrix`` 选择密度矩阵或状态向量解析，分量数量分别须为
``(2**n)**2`` 或 ``2**n``；不匹配时报本地结果处理失败。缺失或 null 的矩阵
仍为可选数据，密度矩阵分量保持平铺，存储顺序未知时不作猜测。
