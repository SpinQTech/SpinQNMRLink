Lab THREE experiments
==========================================

.. toctree::
   :maxdepth: 1

   physical_custom
   physical_pauli
   tomography
   circuit_pulse
   circuit
   hybrid_circuit


Three-qubit experiments use the same connection and result-retrieval methods as two-qubit experiments. Switch the experiment platform to three-qubit mode before running an example; the ``lab.three.*`` experiment keys require the authoritative server mode THREE.

Three-qubit physical-layer custom measurement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/physical_custom.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitPhysicalCustomParameters`` to set the pulse sequence, acquisition channels, sampling frequency, sample count, and density-matrix option. Public ``sample_qubits`` uses zero-based indices ``0``, ``1`` and ``2``. The adapter converts acquisition indices to the wire numbering.

Three-qubit Pauli-component measurement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/physical_pauli.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitPhysicalPauliParameters`` to select the Pauli components to measure. Coefficients in the result follow the submitted ``step_list`` order.

Three-qubit state tomography
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/tomography.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitPhysicalTomographyParameters`` to set the state-preparation pulses and acquisition parameters. The result object stores density-matrix, probability, and fit data.

Three-qubit circuit-layer test pulse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/circuit_pulse.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitCircuitPulseParameters`` to submit circuit-layer test pulses. ``qubit_index`` uses the numbers ``0``, ``1``, and ``2``.

Three-qubit quantum circuit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/circuit.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitCircuitParameters`` to submit a three-qubit circuit. Target and control qubits use the numbers ``0``, ``1``, and ``2``; use ``-1`` when no control qubit is required.

Three-qubit hybrid circuit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../examples/lab/three/hybrid_circuit.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LabThreeQubitMixingCircuitParameters`` to submit a hybrid circuit, following the example for circuit steps and acquisition parameters.

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **data_updates**: data received while the experiment is running
- **graph**: data grouped by chart name
- **chart_streams**: chart data grouped by task, group, channel, qubit, step, and chart name
- **final_data**: data returned when the experiment completes
