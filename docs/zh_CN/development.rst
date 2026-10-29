开发与扩展
============

先按 :doc:`installation` 创建并激活 Conda 环境，在项目根目录安装开发依赖。SDK、示例及工具应通过 pathlib 和当前环境的 Python 解释器保持跨平台，不写死 Windows 路径或 shell 启动器。

分层结构
------------

公开 API 管理设备名称、类型化配置、实验验证和结果封装。内部 ``_core`` 保存共享基础逻辑与参考参数，``_backends`` 负责协议序列化、结果解码和 Python 网络会话。后端可依赖核心基础逻辑，核心基础逻辑不能实例化设备。

Lab 的会话、请求关联、模式状态、事件路由和任务管理拆为不同 mixin，由一个内部后端组合。回调线程不能修改另一台设备状态。同一设备同时只允许一个同步 SDK 实验。

新增实验
------------

实现内部参数序列化与结果解码，登记工厂、参考参数及目录条目，必要时补充公开 snake_case 字段映射。加入协议基线、参数和结果失败测试，再加入精确实验键的示例与对应中英文页面。``parameters_for`` 从序列化模型派生公开类型，无需维护另一套手工 schema。

新增设备协议
------------------

实现后端会话约定、明确的就绪状态与协议能力，分离传输、消息编解码和会话状态。Triangulum 的 transport.py 管理 WebSocket，protocol.py 管理 JSON 消息及结果解码，session.py 管理认证、心跳和单任务关联。新增协议需提供离线报文基线与本地回环服务器测试，构造函数不启动连接或线程。

协议生成
------------

``message.proto`` 仅为 Lab 的 Protobuf 协议来源，Triangulum 使用 JSON，不需要 Protobuf 生成。若修改 Lab schema，在独立 Conda 工具环境中运行：

.. code-block:: console

   conda create --name spinq-protocol python=3.10 pip
   conda activate spinq-protocol
   python -m pip install grpcio-tools==1.70.0 protobuf==5.29.3
   python tools/generate_protocol.py
   conda activate spinqnmrlink

命令在项目根目录运行。若主环境使用其他名称，相应修改最后的激活命令。生成的 Python 不手改，设备报文字段与参数单位必须符合实际固件协议。

检查与发行
------------

测试、代码规范、类型、双语严格构建、链接、发行包及示例检查的命令统一见
:download:`贡献指南 <../../CONTRIBUTING.md>`。
贡献与支持入口见 :doc:`community`。

``tools/check_docs.py`` 核对实际 SDK 目录、示例清单、源码的
``EXPERIMENT_KEY``、双语参数表的实验键与引用示例。
同时要求每份源文档都有已构建 HTML，检查本地锚点及语言切换是否指向同一页面。
先完成严格构建，再运行此检查。

测试默认离线运行，真实设备验证记录于 validation_status.json。源码包包含测试、示例及双语文档，SDK 生成纯 Python、平台无关 wheel。保持源码许可证与第三方依赖声明完整。

CI 的平台目标见 :doc:`devices`。每个平台须检查核心测试、源码示例、发行包内容及安装后的 SDK；通过状态须附实际执行证据。
