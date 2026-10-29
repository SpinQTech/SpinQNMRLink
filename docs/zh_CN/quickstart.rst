快速入门
========

先按 :doc:`installation` 激活 Conda 环境并安装 SDK。以下导入示例需在项目根目录执行，``examples`` 是仓库源码目录，不包含在 SDK wheel 中；也可将实验源码复制到自己的项目。

离线验证安装
------------

以下示例无需设备、配置文件或凭据：

.. code-block:: python

   from spinqnmrlink import list_experiments, parameters_for

   print(len(list_experiments()))  # 35 个实验定义。
   parameters = parameters_for("lab.two.rabi")
   print(parameters.to_wire())  # 序列化参考参数，不连接设备。

运行校准后的设备实验
--------------------

按 :doc:`configuration` 准备配置文件中的字面连接值。
本例需要可访问的 Lab 设备服务，且设备已同步为 TWO 模式。
替换模板中的设备地址，在 ``build_parameters()`` 中填写实际样品的校准值；
参考值不代表设备校准结果。

.. code-block:: python

   from examples.lab.two.principles.rabi import build_parameters, run_experiment

   parameters = build_parameters()
   parameters.pulses[0].width_us = 40  # Replace with your calibrated width (us).
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data["real"])  # Actual measured signal amplitude.

调用函数或直接运行实验文件会执行设备实验。离线检查使用 :doc:`advanced` 中独立的明确调用，不设置全局运行开关。配置路径相对于工作目录，源码可复制到自己的项目使用。

Lab 两比特分为 :doc:`lab/two/principles/index`、:doc:`lab/two/algorithms/index`、:doc:`lab/two/technology/index`、:doc:`lab/two/research/index` 四章。Lab 三比特和 Triangulum 独立组织。下方 Rabi 源码仅测一个点，完整曲线见 :doc:`lab/two/principles/rabi_scan`。

.. literalinclude:: ../../examples/lab/two/principles/rabi.py
   :language: python

在 Python 中配置两类会话
------------------------

以下源码展示通过类型化参数直接配置两类设备。创建会话不会连接，``device.open()`` 负责连接与认证。退出上下文会清理所有会话，包括异常退出。

.. literalinclude:: ../../examples/common/configure_devices.py
   :language: python
