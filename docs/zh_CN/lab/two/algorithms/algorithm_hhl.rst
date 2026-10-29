HHL 线性方程算法
====================

运行内置教学算法线路。

设备：**lab**，模式：**TWO**。运行前准备样品与校准后的脉冲、频率参数。

在 IDE 中打开下方源码，先修改 ``build_parameters()`` 中的校准参数，再直接运行文件或调用函数。配置路径相对于当前工作目录。离线检查、保存与评估见 :doc:`/advanced`。

.. code-block:: python

   from examples.lab.two.algorithms.algorithm_hhl import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../../../examples/lab/two/algorithms/algorithm_hhl.py
   :language: python

.. sdk-parameters:: lab.two.algorithm.hhl

结果字段：``graph``, ``fidelity``, ``gateNums``, ``hFre_offset``, ``pFre_offset``, ``pulseControlTime``, ``pureTime``, ``purity``, ``relaxtion``, ``sampleTime``, ``smt``, ``matrix``, ``probability``。设备字段保留原始表示。

任务完成后检查数据是否存在及有限。科学评估需要相应扫描、目标线路/量子态、样品制备和校准；进阶评估对单参考点返回 NOT_ASSESSED。

输出解读
--------

以下使用占位符解释输出格式，不是硬件测量数据：

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Acquired chart data: <device-chart-data>

源码读取采集图表及可用的实验专属字段。可选的矩阵、概率和保真度可能为 None，应结合该实验的制备、采集和校准评估科学目标。
