Quick start
======================

Activate your Conda environment and install the SDK following :doc:`installation`. Run the import example below from the repository root: ``examples`` is a source directory in the checkout, not part of the SDK wheel. You may also copy an experiment source into your own project.

Check the installation offline
-------------------------------

This example needs no device, configuration file or credentials:

.. code-block:: python

   from spinqnmrlink import list_experiments, parameters_for

   print(len(list_experiments()))  # 35 experiment definitions.
   parameters = parameters_for("lab.two.rabi")
   print(parameters.to_wire())  # Serialized reference parameters; no connection.

Run a calibrated hardware experiment
-------------------------------------

Prepare the configuration and literal credential values following
:doc:`configuration`. A Lab device service must be reachable and synchronized
in TWO mode for this example. Replace the template addresses and edit
sample-calibrated values in ``build_parameters()``; reference values are not
device calibration results.

.. code-block:: python

   from examples.lab.two.principles.rabi import build_parameters, run_experiment

   parameters = build_parameters()
   parameters.pulses[0].width_us = 40  # Replace with your calibrated width (us).
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data["real"])  # Actual measured signal amplitude.

Calling the function or running the experiment file performs a hardware run. Offline checks are explicit, separate functions in :doc:`advanced`; there is no global execution-mode switch. Configuration paths are relative to the working directory, so the source may be copied into your own project.

Lab TWO has four chapters: :doc:`lab/two/principles/index`, :doc:`lab/two/algorithms/index`, :doc:`lab/two/technology/index`, and :doc:`lab/two/research/index`. Lab THREE and Triangulum remain separate. The Rabi source below takes one point; a full curve is in :doc:`lab/two/principles/rabi_scan`.

.. literalinclude:: ../../examples/lab/two/principles/rabi.py
   :language: python

Configure both sessions in Python
---------------------------------

Direct typed configuration for both device sessions is demonstrated below. Creating sessions does not connect; ``device.open()`` connects and authenticates. Context exit cleans up both sessions, including on errors.

.. literalinclude:: ../../examples/common/configure_devices.py
   :language: python
