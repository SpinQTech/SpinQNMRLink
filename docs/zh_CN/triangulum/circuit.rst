线路层量子线路实验
==================

按量子门序列构造线路并读取线路执行结果。

设备：**triangulum**，传输：**JSON WebSocket**。运行前准备样品与校准后的脉冲、频率参数。

.. important::

   **密度矩阵功能需要三角座客户端 2.0 及以上版本支持。**
   使用 ``calc_matrix=True`` / ``calcMatrix: true`` 前，请确认客户端版本满足要求。

在 IDE 中打开下方源码，修改参数后直接运行或调用函数。配置路径相对于当前工作目录。离线检查、保存与评估见 :doc:`/advanced`。

.. code-block:: python

   from examples.triangulum.circuit import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../examples/triangulum/circuit.py
   :language: python

.. sdk-parameters:: triangulum.circuit

``calc_matrix=True``（默认）在 ``push_task_request`` 顶层发送 ``calcMatrix: true``，
将返回的分量解析为 ``density_matrix``。设置 ``parameters.calc_matrix = False``
关闭密度矩阵计算。客户端此时返回空的实部、虚部数组，表示没有矩阵数据，
不影响概率结果；若服务实际提供非空状态向量则保留。结果类型依据实际提交的标志，
非空分量数量须与对应模式匹配；
矩阵缺失时仍保持缺失。密度矩阵保留平铺的实部、虚部、
``shape=[2**n, 2**n]`` 和 ``order=None``，因为协议未说明存储顺序。

结果字段：``fidelity``, ``probabilities``, ``state_vector``, ``density_matrix``, ``qubits_num``, ``coordinate``。设备字段保留原始表示。

``probabilities`` 必填，其余字段可选，服务端未返回时保持缺失。
可选的比特数回显缺失时，结构评估按实际提交的线路维度检查。
结果验证规则见 :doc:`/parameters`。

任务完成后检查数据是否存在及有限。科学评估需要相应扫描、目标线路/量子态、样品制备和校准；进阶评估对单参考点返回 NOT_ASSESSED。

输出解读
--------

以下使用占位符解释输出格式，不是硬件测量数据：

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Basis-state probabilities: <measured-probabilities>
   Density matrix, if returned: <measured-matrix-or-None>
   State vector, if returned: <measured-vector-or-None>

参考线路对三个比特分别执行 X，理想目标态为 ``|111>``。应按设备的基态编号约定比较实际概率与目标态，理想预期不代表设备验证证据。
