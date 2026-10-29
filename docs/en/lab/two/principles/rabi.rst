Rabi oscillations
==================================

Run one reference point of a Rabi pulse-width scan.

Device: **lab**. Mode: **TWO**. Prepare the sample and calibrated pulse/frequency values before running.

Open the source below in your IDE, edit the calibrated settings in ``build_parameters()``, then run the file or call the function. Configuration paths are relative to your working directory. Offline validation, saving and assessment are in :doc:`/advanced`.

.. code-block:: python

   from examples.lab.two.principles.rabi import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../../../examples/lab/two/principles/rabi.py
   :language: python

.. sdk-parameters:: lab.two.rabi

Backend result fields: ``graph``, ``width``, ``real``. Device fields retain their original representations.

A completed task is checked for finite and available data. Scientific evaluation requires the relevant scan, target circuit/state, sample preparation and calibration; the advanced assessment reports NOT_ASSESSED for a single reference point.

Output interpretation
------------------------------------------

The following uses placeholders to explain the output format. It is not a hardware measurement:

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Measured amplitude: <device-amplitude>
   Pulse-width result: <reported-width-or-None>

Amplitude is a measured device signal, not a normalized probability. A single point cannot estimate a Rabi period or a T1/T2 lifetime; use the full scan in the principles chapter.
