Advanced workflows
====================================

Use these sources when you need offline serialization, persistent results or data-quality assessment. The basic experiment sources focus on configuration, execution and reading measurements.

Offline parameter validation
--------------------------------------------------------

.. code-block:: python

   from examples.lab.two.principles.rabi import build_parameters
   from examples.advanced.offline_parameters import check_parameters

   request = check_parameters("lab.two.rabi", build_parameters())
   print(request["wire"])  # Offline reference request; no measured data.

.. literalinclude:: ../../examples/advanced/offline_parameters.py
   :language: python

Saving and assessment
------------------------------------------

.. code-block:: python

   from examples.lab.two.principles.rabi import run_experiment
   from examples.advanced.save_and_assess import save_and_assess

   result = run_experiment("connection_config.local.json", timeout=300)
   assessment = save_and_assess(result, "experiment_results/rabi.json")

.. literalinclude:: ../../examples/advanced/save_and_assess.py
   :language: python

A completed task and structurally valid data do not establish a scientific result. Single-point assessment reports NOT_ASSESSED for the scientific target; use a calibrated scan or experiment-specific analysis. Raw data and actual non-sensitive parameters remain in the saved document.
