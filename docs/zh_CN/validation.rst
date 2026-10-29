验证证据
============

单元测试、序列化参考参数属于离线证据，不是设备测量。CI 覆盖 Windows、Linux、macOS Intel 的 Python 3.8、3.10、3.12，以及 macOS ARM64 的 Python 3.10、3.12，具体矩阵见 :doc:`devices`；配置了任务不等于任务已通过。

.. literalinclude:: ../../validation_status.json
   :language: json

当前本地候选版本在 Windows x86_64、Python 3.12.15 上检查。本轮本机验证范围为 Python 3.12.15。
Linux/macOS 已由用户确认测试同事验证通过，具体解释器及架构矩阵未提供。类型检查使用仓库默认配置，
范围为六个公开源码模块。发行包检查同时验证本地配置排除与独立 wheel 安装。

每个硬件实验须记录设备、固件、配置、测量和结论才可标为通过。SDK 不分发设备二进制。Linux/macOS 为测试同事已验证的平台反馈，未单独记录具体矩阵项；通用 wheel 不代表每个平台依赖及设备服务均已验证。
