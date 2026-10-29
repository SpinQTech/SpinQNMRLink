Lab 三比特实验
==================

.. toctree::
   :maxdepth: 1

   physical_custom
   physical_pauli
   tomography
   circuit_pulse
   circuit
   hybrid_circuit


三比特实验与双比特实验使用相同的连接和结果获取方法。运行前需要在实验平台切换到三比特模式，``lab.three.*`` 实验键要求服务端权威模式为 THREE。

三比特物理层自定义测量
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/physical_custom.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitPhysicalCustomParameters`` 设置脉冲、采样通道、采样频率、采样点数和是否计算密度矩阵。公开 ``sample_qubits`` 使用 ``0``、``1``、``2`` 编号，适配器负责转换为协议采样编号。

三比特 Pauli 分量测量
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/physical_pauli.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitPhysicalPauliParameters`` 选择需要测量的 Pauli 分量。返回结果中的系数顺序与提交的 ``step_list`` 对应。

三比特量子态层析
~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/tomography.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitPhysicalTomographyParameters`` 设置态制备脉冲和采集参数。结果对象用于保存密度矩阵、概率和拟合数据。

三比特线路层测试脉冲
~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/circuit_pulse.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitCircuitPulseParameters`` 提交线路层测试脉冲。``qubit_index`` 使用 ``0``、``1``、``2`` 编号。

三比特量子线路
~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/circuit.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitCircuitParameters`` 提交三比特量子线路。目标比特和控制比特使用 ``0``、``1``、``2`` 编号；没有控制比特时使用 ``-1``。

三比特混合线路
~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/hybrid_circuit.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

使用 ``LabThreeQubitMixingCircuitParameters`` 提交混合线路，并按照示例设置线路步骤和采集参数。

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **data_updates**: 实验运行过程中收到的数据
- **graph**: 按图表名称整理的数据
- **chart_streams**: 按任务、分组、通道、比特、步骤和图表名称整理的数据
- **final_data**: 实验完成时返回的数据
