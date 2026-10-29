Physical-layer pulse experiment
==============================================================

Send pulses directly and acquire the device response.

.. important::

   Physical-layer experiments (``triangulum.physical``) require **Triangulum client software version 1.6.1 or later**.
   Check and update the client before running; earlier versions do not support physical-layer experiments.

Device: **triangulum**. Transport: **JSON WebSocket**. Prepare the sample and calibrated pulse/frequency values before running.

Open the source below, edit the calibrated settings, then run the file or call the function. Configuration paths are relative to your working directory. Offline validation, saving and assessment are in :doc:`/advanced`.

.. code-block:: python

   from examples.triangulum.physical import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../examples/triangulum/physical.py
   :language: python

.. sdk-parameters:: triangulum.physical

Backend result fields: ``graph``. Device fields retain their original representations.

Before completion, the adapter validates that the graph decodes to at least
one finite chart point. Empty or malformed graphs raise a processing failure.
Compressed chart limits and result preservation are described in :doc:`/parameters`.

A completed task is checked for finite and available data. Scientific evaluation requires the relevant scan, target circuit/state, sample preparation and calibration; the advanced assessment reports NOT_ASSESSED for a single reference point.

Output interpretation
------------------------------------------

The following uses placeholders to explain the output format. It is not a hardware measurement:

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Acquired chart data: <device-chart-data>

The source reads acquired chart data and any available experiment-specific fields. Optional matrix, probability or fidelity fields may be None. Evaluate the scientific target using the preparation, acquisition and calibration for this experiment.
