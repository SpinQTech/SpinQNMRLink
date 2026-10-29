Integrated Quantum Technology Experiments
==================================================================================

.. note::

   This teaching narrative uses public snake_case parameters. Detailed bounds and reference values are generated from the models on each experiment page. The figures illustrate the teaching material; hardware validation is recorded separately in the validation guide.

.. toctree::
   :maxdepth: 1

   spin_echo
   dynamic_decoupling
   shaped_pulse
   optimized_pulse



This chapter covers spin echo, dynamical decoupling, and pulse-shaping experiments.

Sample Calibration (Lab Tablet)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before running an experiment, select the sample on the Lab tablet and complete its calibration. The available samples are water (H₂O) and dimethyl phosphite ((CH₃O)₂P(O)H). On the experiment settings screen, choose the sample, select Calibrate and then Start Calibration. Submit the experiment after the tablet reports that calibration is complete; otherwise, the platform may reject the run.

Spin Echo
~~~~~~~~~~~~~~~~~~

Compare the signal and phase under free-precession and spin-echo conditions.

.. literalinclude:: ../../../../../examples/lab/two/technology/spin_echo.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel; the spin-echo experiment uses hydrogen channel ``0``
- **sample_count**: number of samples; use ``16000`` or a power of two from ``1024`` to ``16384``
- **sample_frequency**: integer Hz; choose one of ``10000, 20000, 50000, 100000``
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``2000000``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each spin-echo step
- **coordinate**: spin phase coordinates
- **phase**: phase angle


Dynamic Decoupling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare signals obtained with different pulse sequences.

.. literalinclude:: ../../../../../examples/lab/two/technology/dynamic_decoupling.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **calibrate_sample**: calibrated sample; ``0`` for a phosphorus-containing sample and ``1`` for water
- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **sample_count**: number of samples, from ``1024`` to ``16384``; the value must be a power of two
- **sample_frequency**: integer Hz; choose one of ``10000, 20000, 50000, 100000``
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``2000000``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **p_frequency_shift**: phosphorus frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``
- **p_frequency_demo**: phosphorus demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each dynamical-decoupling step
- **up_state_coupling**: upper state coupling
- **no_coupling**: no coupling
- **down_state_coupling**: down-state coupling

Shaped Pulses
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pulse technique for modulating RF field envelope

.. literalinclude:: ../../../../../examples/lab/two/technology/shaped_pulse.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


- **calibrate_sample**: calibrated sample; ``0`` for a phosphorus-containing sample and ``1`` for water
- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **sample_count**: number of samples, from ``1024`` to ``16384``; the value must be a power of two
- **sample_frequency**: integer Hz; choose one of ``10000, 20000, 50000, 100000``
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``2000000``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **p_frequency_shift**: phosphorus frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``
- **p_frequency_demo**: phosphorus demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each shaped-pulse step
- **coordinate**: single-bit Bloch spherical coordinates
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results

Numerical Pulse Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pulse technology based on optimization algorithm

.. literalinclude:: ../../../../../examples/lab/two/technology/optimized_pulse.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


- **calibrate_sample**: calibrated sample; ``0`` for a phosphorus-containing sample and ``1`` for water
- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **sample_count**: number of samples, from ``1024`` to ``16384``; the value must be a power of two
- **sample_frequency**: integer Hz; choose one of ``10000, 20000, 50000, 100000``
- **sample_delay_us**: acquisition delay in μs, from ``0`` to ``2000000``
- **h_frequency_shift**: hydrogen frequency offset in Hz, from ``-1000`` to ``1000``
- **p_frequency_shift**: phosphorus frequency offset in Hz, from ``-1000`` to ``1000``
- **h_frequency_demo**: hydrogen demodulation frequency in Hz, from ``-1000`` to ``1000``
- **p_frequency_demo**: phosphorus demodulation frequency in Hz, from ``-1000`` to ``1000``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each numerical-pulse step
- **coordinate**: Bloch-sphere coordinates returned for a single-qubit experiment; this field is not returned for a two-qubit experiment
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results
