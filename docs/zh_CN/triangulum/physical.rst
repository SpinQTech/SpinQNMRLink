物理层脉冲实验
==============

配置脉冲和采样参数，采集设备响应。

.. important::

   三角座物理层实验（``triangulum.physical``）仅支持 **三角座客户端软件 1.6.1 及以上版本**。
   运行前请确认并升级客户端版本；较低版本不支持物理层实验。

设备：**triangulum**，传输：**JSON WebSocket**。运行前准备样品与校准后的脉冲、频率参数。

在 IDE 中打开下方源码，修改参数后直接运行或调用函数。配置路径相对于当前工作目录。离线检查、保存与评估见 :doc:`/advanced`。

.. code-block:: python

   from examples.triangulum.physical import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../examples/triangulum/physical.py
   :language: python

.. sdk-parameters:: triangulum.physical

结果字段：``graph``。设备字段保留原始表示。

判为完成前，适配器确认图表可解码且至少有一个有限数值点。
空图表或损坏图表报告结果处理失败。
压缩图表限制与原始结果保留规则见 :doc:`/parameters`。

任务完成后检查数据是否存在及有限。科学评估需要相应扫描、目标线路/量子态、样品制备和校准；进阶评估对单参考点返回 NOT_ASSESSED。

输出解读
--------

以下使用占位符解释输出格式，不是硬件测量数据：

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Acquired chart data: <device-chart-data>

源码读取采集图表及可用的实验专属字段。可选的矩阵、概率和保真度可能为 None，应结合该实验的制备、采集和校准评估科学目标。
