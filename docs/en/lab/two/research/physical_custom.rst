Physical-layer custom measurement
==================================================================

Acquire physical-layer signals on the selected channels.

Device: **lab**. Mode: **TWO**. Prepare the sample and calibrated pulse/frequency values before running.

Open the source below in your IDE, edit the calibrated settings in ``build_parameters()``, then run the file or call the function. Configuration paths are relative to your working directory. Offline validation, saving and assessment are in :doc:`/advanced`.

.. code-block:: python

   from examples.lab.two.research.physical_custom import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../../../examples/lab/two/research/physical_custom.py
   :language: python

.. sdk-parameters:: lab.two.physical.custom

Backend result fields: ``graph``. Device fields retain their original representations.

A completed task is checked for finite and available data. Scientific evaluation requires the relevant scan, target circuit/state, sample preparation and calibration; the advanced assessment reports NOT_ASSESSED for a single reference point.

Output interpretation
------------------------------------------

The following uses placeholders to explain the output format. It is not a hardware measurement:

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Acquired chart data: <device-chart-data>

The source reads acquired chart data and any available experiment-specific fields. Optional matrix, probability or fidelity fields may be None. Evaluate the scientific target using the preparation, acquisition and calibration for this experiment.
