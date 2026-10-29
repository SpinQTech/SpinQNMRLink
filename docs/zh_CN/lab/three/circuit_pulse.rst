三比特线路层测试脉冲
====================

在线路层运行三比特测试脉冲序列。

设备：**lab**，模式：**THREE**。运行前准备样品与校准后的脉冲、频率参数。

在 IDE 中打开下方源码，修改参数后直接运行或调用函数。配置路径相对于当前工作目录。离线检查、保存与评估见 :doc:`/advanced`。

.. code-block:: python

   from examples.lab.three.circuit_pulse import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../../examples/lab/three/circuit_pulse.py
   :language: python

.. sdk-parameters:: lab.three.circuit_pulse

结果字段：``graph``, ``data_updates``, ``chart_streams``。设备字段保留原始表示。

任务完成后检查数据是否存在及有限。科学评估需要相应扫描、目标线路/量子态、样品制备和校准；进阶评估对单参考点返回 NOT_ASSESSED。

输出解读
--------

以下使用占位符解释输出格式，不是硬件测量数据：

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Final server payload: <server-payload-or-None>
   Chart groups: <measured-chart-groups>

应检查所选实验的图表流和服务端最终数据。可选字段缺失时保留 None，SDK 不构造虚假的密度矩阵或保真度。
