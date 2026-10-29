# Lab 实验类型与任务参数

本页说明公开实验选择与内部协议类型的对应关系。公开键、字段和单位见[实验目录](../experiments.rst)与[参数说明](../parameters.rst)。

公开调用使用 `parameters_for(key)` 与 `lab.create_experiment(key, parameters=...)`。准备实验可离线进行，`lab.open()` 建立就绪会话，`experiment.run(timeout=...)` 提交并等待结果。内部适配器通过 `ExperimentType` 与 `register_experiment()` 创建后端任务；公开示例不导入内部类型或调用后端注册方法。

## 实验类型

常用实验类型如下：

* 基础实验：NMR 现象与信号、Rabi 振荡、量子比特、T1、T2、量子控制、量子系统初始化、量子线路、量子态重构和量子计算任务；
* 算法实验：基础算法、Deutsch、Bernstein、Grover、QFT、HHL、VQE 和 QAOA；
* 综合实验：自旋回波、动力学解耦、形状脉冲和数值脉冲优化；
* 三比特实验：物理层测量、线路层测试脉冲、量子线路和混合线路。

完整枚举可在 `spinqnmrlink._backends.lab.utils.types.ExperimentType` 中查看。

## 设置参数

下面以 NMR 现象与信号实验为例：

```{literalinclude} ../../../examples/lab/two/principles/nmr_signal.py
:language: python
```

每个实验键使用 `parameters_for(key)` 返回的精确公开模型。NMR 示例在 `custom_freq=False` 时使用设备当前锁场频率，在 `custom_freq=True` 时填写 `freq_h` 和 `freq_p`。各字段的含义、单位和约束见对应实验页面生成的参数表。频率、功率、脉宽和延迟应根据当前设备及样品的校准结果设置。

## 任务信息

运行实验时，SDK 会将实验类型、设备编号、实验参数和创建时间组成实验任务并发送至实验平台。任务状态和开始、结束时间由实验平台在运行过程中更新，用户通常不需要直接创建或修改任务对象。

公开的 `lab.two.*` 与 `lab.three.*` 实验键选择所需模式。适配器映射为内部 `QubitMode.TWO` 与 `QubitMode.THREE`，并核对服务端权威模式；选择实验键不会切换设备模式。详细说明见[三比特协议映射](lab_three_qubit.md)。
