Research Experiments
========================================

.. note::

   This teaching narrative uses public snake_case parameters. Detailed bounds and reference values are generated from the models on each experiment page. The figures illustrate the teaching material; hardware validation is recorded separately in the validation guide.

.. toctree::
   :maxdepth: 1

   physical_custom
   physical_pauli
   physical_tomography
   circuit_pulse
   circuit_gates



This chapter covers the parameters and results for Lab TWO physical-layer and circuit-layer experiments.

Physical-Layer Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../../examples/lab/two/research/physical_custom.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **type_setting**: physical-layer measurement mode

    - ``0``: custom measurement
    - ``1``: Pauli-component measurement
    - ``2``: quantum-state tomography

- **step_list**: measurement step numbers for Pauli-component measurements. For ``type_setting=1``, provide a non-empty list of numbers from 1 to 6.

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``-1`` for both channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **sample_count**: number of samples, from ``1024`` to ``16384``; the value must be a power of two
- **sample_frequency**: sampling frequency in Hz, from ``10000`` to ``100000`` preferably in increments of 10000 Hz
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``2000000``
- **relaxation_seconds**: relaxation delay in seconds, from ``0`` to ``30``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``
- **p_frequency_shift**: phosphorus frequency offset in Hz, from ``-1000`` to ``1000``
- **p_frequency_demo**: phosphorus demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each physical-layer step
- **pauli_matrix**: Pauli-component coefficients returned when ``type_setting=1``
- **matrix**: density matrix returned when ``type_setting=2``, with ``real`` and ``imag`` components
- **probability**: probability distribution returned when ``type_setting=2``

Circuit-Layer Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../../../examples/lab/two/research/circuit_gates.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **using_pulse**: selects the submitted representation. Set it to ``True`` to submit ``pulses`` or ``False`` to submit ``circuit``.
- **gradients**: gradient sequence; see ``spinqnmrlink.Gradient``
- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **Circuit**: the quantum circuit and its gates; see ``spinqnmrlink.Circuit``
- **sample_path**: acquisition channel: ``-1`` for both channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **sample_count**: number of samples, from ``1024`` to ``16384``; the value must be a power of two
- **sample_frequency**: sampling frequency in Hz, from ``10000`` to ``100000`` preferably in increments of 10000 Hz
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``1000``
- **relaxation_seconds**: relaxation delay in seconds, from ``0`` to ``30``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``
- **p_frequency_shift**: phosphorus frequency offset in Hz, from ``-1000`` to ``1000``
- **p_frequency_demo**: phosphorus demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each circuit-layer step
- **matrix**: density matrix with real and imaginary components
- **probability**: probability data
- **fidelity**: state fidelity when the server returns a target-state comparison
- **gateNums**: total number of gates
- **hFre_offset**: hydrogen frequency offset (Hz)
- **pFre_offset**: phosphorus frequency offset (Hz)
- **pulseControlTime**: pulse control time (μs)
- **pureTime**: pseudopure-state preparation time (μs)
- **purity**: purity (%)
- **relaxtion**: relaxation time (μs)
- **sampleTime**: sampling time (μs)
- **smt**: The number of comprehensive measurements by the system
