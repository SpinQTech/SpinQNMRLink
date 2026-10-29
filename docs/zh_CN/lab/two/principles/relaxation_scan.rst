T1/T2 弛豫扫描
====================

这是完整扫描流程，按实际校准调整脉冲宽度与扫描范围。保存实际原始点，拟合质量与任务状态分别报告。源码解释使用英文。

使用 SciPy 拟合需安装 ``plot`` extra。当前 T1/T2 拟合至少需要三个有限数值测量点。
输入延迟与拟合寿命均使用微秒：T1 范围为 10000～60000000，T2 为 1000～20000000。
R-squared >= 0.8 判为 GOOD，>= 0.6 判为 ESTIMATE，其余为 POOR。
应结合实际扫描与校准检查拟合，这些范围和质量标签不代表科学验证通过。

.. literalinclude:: ../../../../../examples/lab/two/principles/relaxation_scan.py
   :language: python
