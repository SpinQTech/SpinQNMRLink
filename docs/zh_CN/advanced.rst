进阶流程
========

离线序列化、结果保存和数据质量评估分别放在这些源码中。基础实验源码专注于配置、执行和读取测量结果。源码解释使用英文。

离线参数验证
------------

.. code-block:: python

   from examples.lab.two.principles.rabi import build_parameters
   from examples.advanced.offline_parameters import check_parameters

   request = check_parameters("lab.two.rabi", build_parameters())
   print(request["wire"])  # Offline reference request; no measured data.

.. literalinclude:: ../../examples/advanced/offline_parameters.py
   :language: python

结果保存与评估
--------------

.. code-block:: python

   from examples.lab.two.principles.rabi import run_experiment
   from examples.advanced.save_and_assess import save_and_assess

   result = run_experiment("connection_config.local.json", timeout=300)
   assessment = save_and_assess(result, "experiment_results/rabi.json")

.. literalinclude:: ../../examples/advanced/save_and_assess.py
   :language: python

任务完成与数据结构有效不代表科学目标达成。单点科学评估返回 NOT_ASSESSED，应结合校准后的扫描或实验专属分析。保存的文档包含原始数据、实际非敏感参数和 SDK 元信息。
