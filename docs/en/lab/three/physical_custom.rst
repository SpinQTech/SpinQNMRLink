3-qubit physical-layer custom measurement
==================================================================================

Acquire the three-qubit pulse response on the selected channels.

Device: **lab**. Mode: **THREE**. Prepare the sample and calibrated pulse/frequency values before running.

Open the source below, edit the calibrated settings, then run the file or call the function. Configuration paths are relative to your working directory. Offline validation, saving and assessment are in :doc:`/advanced`.

.. code-block:: python

   from examples.lab.three.physical_custom import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../../examples/lab/three/physical_custom.py
   :language: python

.. sdk-parameters:: lab.three.physical_custom

Backend result fields: ``graph``, ``data_updates``, ``chart_streams``. Device fields retain their original representations.

A completed task is checked for finite and available data. Scientific evaluation requires the relevant scan, target circuit/state, sample preparation and calibration; the advanced assessment reports NOT_ASSESSED for a single reference point.

Output interpretation
------------------------------------------

The following uses placeholders to explain the output format. It is not a hardware measurement:

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Final server payload: <server-payload-or-None>
   Chart groups: <measured-chart-groups>

Inspect chart streams and the final server payload for the selected experiment. Missing optional fields remain None; the SDK does not invent a density matrix or fidelity.
