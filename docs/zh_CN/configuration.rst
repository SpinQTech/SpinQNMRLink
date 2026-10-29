连接配置
==========

顶层只接受 ``lab``、``triangulum``，可配置其中一个或两个。公共字段为 ``host``、``port``、``account``、``password``、``connection_timeout``、``request_timeout``。交付模板直接使用字面值；配置显示及 SDK 错误会隐藏凭据值。

准备本地配置
------------

从仓库根目录复制模板到一个尚不存在的本地文件；已有文件请直接编辑：

.. code-block:: console

   python -c "from shutil import copyfile; copyfile('examples/connection_config.example.json', 'connection_config.local.json')"

仅保留实际使用的设备段，将 ``host`` 和 ``port`` 替换为实际服务地址。两个字段都必须提供，模板端口只是示例。

- Lab 的 ``account``、``password`` 是预留字段。保留模板中的非空字面值，或填写现有部署使用的预留值。SDK 只检查类型及非空格式，不新增账号有效性判定；原有会话握手、权威模式及状态同步仍须完成后才会 READY。
- 三角座使用现有认证机制：先在客户端软件的 **用户中心** 创建账号与密码，再将同一组值填入 ``triangulum.account`` 和 ``triangulum.password``。模板中的 ``replace-with-...`` 不能直接用于登录；填写 JSON 不会创建账号。

.. literalinclude:: ../../examples/connection_config.example.json
   :language: json

本地配置文件被 Git 忽略。仍可按需使用 ``env:变量名`` 引用；此时对应环境变量必须在加载前存在。默认模板和实验示例不依赖环境变量。

源码包中的示例 JSON 只包含公开配置模板和示例清单。本地配置会被排除并在发布前检查；模板中的地址和凭据应保持为占位值。

超时与连接设置
--------------

Lab 额外支持 ``transport`` （``tcp`` 或 ``websocket``）、 ``websocket_path``、``websocket_secure``、心跳和重连设置。三角座支持 ``websocket_path`` （默认空字符串，表示根路径）、 ``websocket_secure`` （默认 False）、 ``heartbeat_interval`` （默认 10 秒）、 ``heartbeat_timeout`` （默认 30 秒）和 ``max_message_bytes`` （默认 32 MiB）。初次登录不发送 session_id，认证成功后的心跳与任务使用返回的 session_id。

连接和请求回执预算默认各 10 秒，关闭资源预算默认 5 秒。请求回执使用 ``request_timeout``，不消耗执行预算。

.. code-block:: python

   result = experiment.run(timeout=300, queue_timeout=600)

``timeout`` 是本任务首次 started/RUNNING 通知之后的执行等待预算，必须是有限正数。``queue_timeout`` 从接受回执后计时，可选、默认为 ``None`` （不限制排队时间），指定时也须为有限正数。默认 example 的执行预算为 300 秒，并透传 ``queue_timeout``。排队仍受心跳失活、关闭连接或用户中断影响。

超时错误保留 ``task_id``、``status``，并通过 ``phase`` 区分 ``queue`` 与 ``execution``。本地超时不会取消或重发远端任务。查看 :doc:`parameters` 中的分阶段时间元数据。

连接配置不可变。可在 ``build_parameters()`` 中构造参数，再通过 ``run_experiment(parameters=...)`` 传入。参数字段使用 snake_case；未知字段和非法嵌套值在提交前拒绝。代码配置使用 ``SDKSettings(lab=LabSettings(...), triangulum=TriangulumSettings(...))`` 传入 ``SpinQNMRLink``。读取 JSON 或构造配置不会启动连接。
