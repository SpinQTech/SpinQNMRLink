研究型实验
============

.. note::

   教学说明使用公开 snake_case 参数，各实验页面从实际模型生成详细约束和参考值。图示用于教学说明，设备验证记录见验证指南。

.. toctree::
   :maxdepth: 1

   physical_custom
   physical_pauli
   physical_tomography
   circuit_pulse
   circuit_gates



本章介绍Lab 双比特物理层和线路层实验的参数与结果。

物理层实验
~~~~~~~~~~~~

.. literalinclude:: ../../../../../examples/lab/two/research/physical_custom.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

- **type_setting**: 物理层测量方式

    - ``0``：用户自定义测量
    - ``1``：泡利分量测量
    - ``2``：量子态层析重构

- **step_list**: 泡利分量测量使用的步骤编号列表。选择 ``type_setting=1`` 时不能为空，编号取值为 1～6

- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **sample_path**: 采样路径：``-1`` 为双通道，``0`` 为氢通道，``1`` 为磷通道
- **sample_count**: 采样点数，取值范围为 1024～16384，且必须为 2 的次方
- **sample_frequency**: 采样频率（Hz），取值范围为 10000～100000；建议以 10000 Hz 为间隔设置
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～2000000
- **relaxation_seconds**: 弛豫延迟（s），取值范围为 0～30
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000
- **p_frequency_shift**: 磷频率偏移（Hz），取值范围为 -1000～1000
- **p_frequency_demo**: 磷频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 物理层实验各步骤返回的图表数据
- **pauli_matrix**: ``type_setting=1`` 时返回的泡利分量系数
- **matrix**: ``type_setting=2`` 时返回的密度矩阵，包含 ``real`` 和 ``imag``
- **probability**: ``type_setting=2`` 时返回的概率分布

线路层实验
~~~~~~~~~~~~

.. literalinclude:: ../../../../../examples/lab/two/research/circuit_gates.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

- **using_pulse**: 是否使用脉冲序列。设为 ``True`` 时提交 ``pulses``；设为 ``False`` 时提交 ``circuit``
- **gradients**: 梯度序列，详情参阅 ``spinqnmrlink.Gradient``
- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **Circuit**: 量子线路及其中的量子门，详情参阅 ``spinqnmrlink.Circuit``
- **sample_path**: 采样路径：``-1`` 为双通道，``0`` 为氢通道，``1`` 为磷通道
- **sample_count**: 采样点数，取值范围为 1024～16384，且必须为 2 的次方
- **sample_frequency**: 采样频率（Hz），取值范围为 10000～100000；建议以 10000 Hz 为间隔设置
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～1000
- **relaxation_seconds**: 弛豫延迟（s），取值范围为 0～30
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000
- **p_frequency_shift**: 磷频率偏移（Hz），取值范围为 -1000～1000
- **p_frequency_demo**: 磷频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 线路层实验各步骤返回的图表数据
- **matrix**: 密度矩阵，包含实部（real）和虚部（imag）
- **probability**: 概率数据
- **fidelity**: 服务端返回目标态时，对应的保真度
- **gateNums**: 门总数
- **hFre_offset**: 氢频率偏移（Hz）
- **pFre_offset**: 磷频率偏移（Hz）
- **pulseControlTime**: 脉冲控制时间（μs）
- **pureTime**: 赝纯态制备时间（μs）
- **purity**: 纯度（%）
- **relaxtion**: 弛豫时间（μs）
- **sampleTime**: 采样时间（μs）
- **smt**: 系统综合测量次数
