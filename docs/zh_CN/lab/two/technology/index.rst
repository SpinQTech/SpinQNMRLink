综合量子技术实验
================

.. note::

   教学说明使用公开 snake_case 参数，各实验页面从实际模型生成详细约束和参考值。图示用于教学说明，设备验证记录见验证指南。

.. toctree::
   :maxdepth: 1

   spin_echo
   dynamic_decoupling
   shaped_pulse
   optimized_pulse



本章介绍自旋回波、动力学解耦和脉冲设计等实验。

样品标定（Lab 平板操作）
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

运行实验前，先在 Lab 平板上选择当前样品并完成标定。可选样品包括水（H₂O）和亚磷酸二甲酯（(CH₃O)₂P(O)H）。在实验设置页面选择样品，点击“标定”和“开始标定”，待平板显示标定完成后再提交实验。未完成标定时，平台可能拒绝运行实验。

自旋回波
~~~~~~~~~~~~

比较自由演化与自旋回波条件下的信号和相位

.. literalinclude:: ../../../../../examples/lab/two/technology/spin_echo.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **sample_path**: 采样路径；自旋回波实验固定为氢通道 ``0``
- **sample_count**: 采样点数；可设为 ``16000``，也可使用 1024～16384 范围内的 2 的次方
- **sample_frequency**: 整数 Hz，只能从 ``10000、20000、50000、100000`` 中选一个
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～2000000
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 自旋回波各步骤返回的图表数据
- **coordinate**: 自旋相位坐标
- **phase**: 相位，角度制


动力学解耦
~~~~~~~~~~~~

比较不同脉冲序列下的信号变化

.. literalinclude:: ../../../../../examples/lab/two/technology/dynamic_decoupling.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

- **calibrate_sample**: 标定样品，``0`` 为含磷样品，``1`` 为水
- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **sample_path**: 采样路径：``0`` 为氢通道，``1`` 为磷通道
- **sample_count**: 采样点数，取值范围为 1024～16384，且必须为 2 的次方
- **sample_frequency**: 整数 Hz，只能从 ``10000、20000、50000、100000`` 中选一个
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～2000000
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **p_frequency_shift**: 磷频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000
- **p_frequency_demo**: 磷频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 动力学解耦各步骤返回的图表数据
- **up_state_coupling**: 上态耦合
- **no_coupling**: 无耦合
- **down_state_coupling**: 下态耦合

形状脉冲
~~~~~~~~~~~~

调制射频场包络的脉冲技术

.. literalinclude:: ../../../../../examples/lab/two/technology/shaped_pulse.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^


- **calibrate_sample**: 标定样品，``0`` 为含磷样品，``1`` 为水
- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **sample_path**: 采样路径：``0`` 为氢通道，``1`` 为磷通道
- **sample_count**: 采样点数，取值范围为 1024～16384，且必须为 2 的次方
- **sample_frequency**: 整数 Hz，只能从 ``10000、20000、50000、100000`` 中选一个
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～2000000
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **p_frequency_shift**: 磷频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000
- **p_frequency_demo**: 磷频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 形状脉冲实验各步骤返回的图表数据
- **coordinate**: 单比特布洛赫球坐标
- **matrix**: 量子态的密度矩阵，包含实部（real）和虚部（imag）
- **probability**: 测量结果的概率分布

数值脉冲优化
~~~~~~~~~~~~

基于优化算法的脉冲技术

.. literalinclude:: ../../../../../examples/lab/two/technology/optimized_pulse.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^


- **calibrate_sample**: 标定样品，``0`` 为含磷样品，``1`` 为水
- **Pulse**: 脉冲参数，包括通道、宽度、振幅、相位和频率偏移，详情参阅 ``spinqnmrlink.Pulse``
- **sample_path**: 采样路径：``-1`` 为所有通道，``0`` 为氢通道，``1`` 为磷通道
- **sample_count**: 采样点数，取值范围为 1024～16384，且必须为 2 的次方
- **sample_frequency**: 整数 Hz，只能从 ``10000、20000、50000、100000`` 中选一个
- **sample_delay_us**: 采样延迟（μs），取值范围为 0～2000000
- **h_frequency_shift**: 氢频率偏移（Hz），取值范围为 -1000～1000
- **p_frequency_shift**: 磷频率偏移（Hz），取值范围为 -1000～1000
- **h_frequency_demo**: 氢频率解调（Hz），取值范围为 -1000～1000
- **p_frequency_demo**: 磷频率解调（Hz），取值范围为 -1000～1000

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 数值脉冲优化实验各步骤返回的图表数据
- **coordinate**: 单比特实验返回的布洛赫球坐标；双比特实验不返回该字段
- **matrix**: 量子态的密度矩阵，包含实部（real）和虚部（imag）
- **probability**: 测量结果的概率分布
