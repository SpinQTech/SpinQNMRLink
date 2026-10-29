Quantum circuit experiment
====================================================

Run a quantum gate circuit with one to three qubits.

Device: **triangulum**. Transport: **JSON WebSocket**. Prepare the sample and calibrated pulse/frequency values before running.

.. important::

   **Density-matrix support requires Triangulum client version 2.0 or newer.**
   This requirement applies to ``calc_matrix=True`` / ``calcMatrix: true``.

Open the source below, edit the calibrated settings, then run the file or call the function. Configuration paths are relative to your working directory. Offline validation, saving and assessment are in :doc:`/advanced`.

.. code-block:: python

   from examples.triangulum.circuit import build_parameters, run_experiment

   parameters = build_parameters()
   result = run_experiment("connection_config.local.json", parameters=parameters, timeout=300)
   print(result.data)

.. literalinclude:: ../../../examples/triangulum/circuit.py
   :language: python

.. sdk-parameters:: triangulum.circuit

``calc_matrix=True`` (the default) adds top-level ``calcMatrix: true`` to
``push_task_request`` and decodes returned components as ``density_matrix``.
Set ``parameters.calc_matrix = False`` to disable density-matrix calculation.
Client 2.0 returns empty real/imaginary arrays in this mode; these mean no matrix
and do not invalidate the probabilities. A nonempty state vector is retained if
the service supplies it. The submitted
flag determines the representation; returned component counts must match that
mode. Missing matrices stay absent. Density matrices preserve flat real/imaginary
components, ``shape=[2**n, 2**n]`` and ``order=None`` because storage order is unspecified.

Backend result fields: ``fidelity``, ``probabilities``, ``state_vector``, ``density_matrix``, ``qubits_num``, ``coordinate``. Device fields retain their original representations.

``probabilities`` is required; the remaining fields are optional and stay absent
when not supplied by the service. Structural assessment uses the submitted
circuit dimension when the optional qubit-count echo is missing. See
:doc:`/parameters` for result validation rules.

A completed task is checked for finite and available data. Scientific evaluation requires the relevant scan, target circuit/state, sample preparation and calibration; the advanced assessment reports NOT_ASSESSED for a single reference point.

Output interpretation
------------------------------------------

The following uses placeholders to explain the output format. It is not a hardware measurement:

.. code-block:: text

   Task: COMPLETED <task-id-or-None>
   Basis-state probabilities: <measured-probabilities>
   Density matrix, if returned: <measured-matrix-or-None>
   State vector, if returned: <measured-vector-or-None>

This reference circuit applies X to each of three qubits; its ideal target is ``|111>``. Compare actual probabilities with that target using the device basis convention. Ideal expectations are not measured validation evidence.
