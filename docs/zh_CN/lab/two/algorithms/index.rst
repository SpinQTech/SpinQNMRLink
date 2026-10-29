量子算法
============

.. note::

   教学说明使用公开 snake_case 参数，各实验页面从实际模型生成详细约束和参考值。图示用于教学说明，设备验证记录见验证指南。

.. toctree::
   :maxdepth: 1

   algorithm_basic
   algorithm_deutsch
   algorithm_bernstein_vazirani
   algorithm_grover
   algorithm_qft
   algorithm_hhl
   algorithm_vqe
   algorithm_qaoa



本章介绍量子算法实验的调用方法及常用结果字段。

.. literalinclude:: ../../../../../examples/lab/two/algorithms/algorithm_basic.py
   :language: python
   :linenos:

实验参数解析
^^^^^^^^^^^^

- **algorithm_type**: 算法类型，默认为 ``EXP_ALGORITHM_BASIC``
- **grover_bin**: Grover 算法的搜索目标：``0`` = \|00⟩、``1`` = \|01⟩、``2`` = \|10⟩、``3`` = \|11⟩

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - 属性
          - 描述
        * - ``EXP_ALGORITHM_BASIC``
          - 量子计算基础实验
        * - ``EXP_DEUTSCH``
          - Deutsch算法实验
        * - ``EXP_BERNSTEIN``
          - Bernstein-Vazirani算法实验
        * - ``EXP_GROVER``
          - Grover算法实验
        * - ``EXP_QFT``
          - QFT算法实验
        * - ``EXP_HHL``
          - HHL算法实验
        * - ``EXP_VQE``
          - VQE算法实验
        * - ``EXP_QAOA``
          - QAOA算法实验

- **Gate**: 量子门参数，包括门类型和目标量子比特，详情参阅 ``spinqnmrlink.Gate``
- **Circuit**: 量子线路及其中的量子门，详情参阅 ``spinqnmrlink.Circuit``
- **sample_path**: 采样路径：``-1`` 为所有通道，``0`` 为氢通道，``1`` 为磷通道
- **calc_matrix**: 是否计算密度矩阵，默认为 ``True``

实验结果解析
^^^^^^^^^^^^

结果中常用的字段如下：

- **graph**: 图表数据，包含实验步骤的数据
- **matrix**: 量子态的密度矩阵，包含实部和虚部
- **probability**: 测量结果的概率分布
- **fidelity**: 服务端返回的保真度
- **gateNums**: 量子门数量
- **hFre_offset**: 氢频率偏移
- **pFre_offset**: 磷频率偏移
- **pulseControlTime**: 脉冲控制时间
- **pureTime**: 赝纯态制备时间
- **purity**: 纯度
- **relaxtion**: 弛豫时间
- **sampleTime**: 采样时间
- **smt**: 系统综合测量次数
