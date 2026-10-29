# Lab 三比特协议映射

本页描述内部参数类与通信字段。公开调用使用[三比特实验目录](../lab/three/index.rst)、snake_case 类型化模型及[参数说明](../parameters.rst)中的零起始编号。

Lab 支持六种三比特实验。通过 `lab.create_experiment()` 选择 `lab.three.*` 键，适配器在内部选择 `QubitMode.THREE`。服务端须已同步为 THREE 模式，公开实验准备与运行无需传入内部 `QubitMode`。

## 实验类型

| 实验 | 参数类 | 实验类型 |
|---|---|---|
| 三比特物理层自定义测量 | `ThreeQubitPhysicalCustomParameters` | `EXP_LAYER_PHYSICAL` |
| 三比特 Pauli 分量测量 | `ThreeQubitPhysicalPauliParameters` | `EXP_LAYER_PHYSICAL` |
| 三比特量子态层析 | `ThreeQubitPhysicalTomographyParameters` | `EXP_LAYER_PHYSICAL` |
| 三比特线路层测试脉冲 | `ThreeQubitCircuitPulseParameters` | `EXP_LAYER_CIRCUIT_PULSE` |
| 三比特量子线路 | `ThreeQubitCircuitParameters` | `EXP_LAYER_CIRCUIT_CIRCUIT` |
| 三比特混合线路 | `ThreeQubitMixingCircuitParameters` | `EXP_MIXING_CIRCUIT` |

表中为内部序列化类，并非公开导入名。物理层三种实验使用相同的通信实验类型，适配器根据公开键 `lab.three.physical_custom`、`lab.three.physical_pauli`、`lab.three.tomography` 分别生成 `compute_type` 值 `0`、`1`、`2`。

## 比特编号

公开 `sample_qubits` 使用互不重复的 0、1、2，适配器转换为内部 `sample_qubit` / 通信 `sampleQubit` 的 1、2、3。公开线路使用 `Circuit(qubits=3, ...)` 与零起始 `Gate` 编号。内部 `qubit_index`、`control_qubit`、`control_qubit2` 仍为零起始，未使用的内部控制字段为 -1。不要向公开模型填写一起始的采集编号。

## 运行实验

三比特实验的基本调用过程如下：

```{literalinclude} ../../../examples/lab/three/circuit.py
:language: python
```

六份示例位于 `examples/lab/three`。运行实验前，请按照设备和样品的标定结果设置脉冲宽度、频率、功率和采集参数。

## 实验结果

内部 `ThreeQubitExperimentResult.get_result()` 解码器返回以下内容：

* `data_updates`：实验过程中收到的数据；
* `graph`：按图表名称整理的结果；
* `chart_streams`：按照任务、通道、比特和步骤整理的图表数据；
* `final_data`：实验完成时返回的结果。

公开执行返回 `ExperimentResult`，通过 `result.data` 读取 Lab 解码结果，通过 `result.raw` 读取后端结果封装。各实验字段见对应示例。
