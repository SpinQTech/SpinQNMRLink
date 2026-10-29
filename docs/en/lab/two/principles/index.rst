Principles of Quantum Computing
==============================================================
This chapter introduces the calls, main parameters, and returned results for the basic quantum-computing experiments.

.. note::

   This teaching narrative uses public snake_case parameters. Detailed bounds and reference values are generated from the models on each experiment page. The figures illustrate the teaching material; hardware validation is recorded separately in the validation guide.

.. toctree::
   :maxdepth: 1

   nmr_signal
   rabi
   qubit
   t1
   t2
   control
   initialization
   gates_circuit
   tomography
   computing_task
   rabi_scan
   relaxation_scan



NMR Phenomena and Signals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use an NMR pulse experiment to examine the free-induction decay and its spectrum:

.. literalinclude:: ../../../../../examples/lab/two/principles/nmr_signal.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **freq_h**: hydrogen resonance frequency (MHz), ``0 < freq_h < 100``
- **freq_p**: phosphorus resonance frequency (MHz), ``0 < freq_p < 100``
- **make_pps**: whether to generate a PPS signal
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **custom_freq**: whether to use the frequencies in ``freq_h`` and ``freq_p``; when ``False``, the device lock frequencies are used

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: ../../../../_static/images/nmr_result.png
    :width: 100%
    :align: center
    :alt: NMR pulse experiment result

    FID signal, FFT spectrum, and main-peak Lorentzian fit

The ``graph`` field in the returned result has the following structure:

.. code-block:: text

    {
        "result": {
            "graph": [
                {
                    "<chart_name>": [[x, y], ...]
                },
                ...
            ]
        }
    }

- **graph**: chart data for each experiment step. Keys within a step are taken from the server's ``chart_name`` value, and each value is a list of ``[x, y]`` points. The SDK plotting functions recognize the following traces:

    - **fidRe**: real component of the FID
    - **fidIm**: imaginary component of the FID
    - **fidMod**: FID magnitude
    - **lorenz**: Lorentzian fit of the main spectral peak
    - **fftRe**: real component of the FFT
    - **fftIm**: imaginary component of the FFT
    - **fftMod**: FFT magnitude
    - **fftFit**: fitted FFT trace


Rabi Oscillation Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measure Rabi oscillations across a range of pulse widths to estimate the π/2 and π pulse widths:

.. literalinclude:: ../../../../../examples/lab/two/principles/rabi_scan.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **freq_h**: hydrogen resonance frequency (MHz), ``0 < freq_h < 100``
- **freq_p**: phosphorus resonance frequency (MHz), ``0 < freq_p < 100``
- **make_pps**: whether to generate a PPS signal
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **custom_freq**: whether to use custom frequencies

Code flow analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The scan measures one selected channel per call and records the response at each pulse width. Set channel=0 for hydrogen or channel=1 for phosphorus. Each call is fitted independently; use the current device calibration when setting pulse widths for an experiment.

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: ../../../../_static/images/rabi_result.png
   :width: 100%
   :align: center
   :alt: Rabi oscillation experiment result

   Rabi oscillation fit and rotation pulse widths

Common result fields are listed below:

- **graph**: chart data for the current pulse width
- **width**: Pulse width
- **real**: real part of signal strength

Qubit Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Observe the physical properties of qubits

.. literalinclude:: ../../../../../examples/lab/two/principles/qubit.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **pulses**: pulse sequence

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each experiment step
- **coordinate**: The coordinates of the qubit on the Bloch sphere
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results

T₁ Longitudinal Relaxation Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measure longitudinal-magnetization recovery with an inversion-recovery sequence

.. literalinclude:: ../../../../../examples/lab/two/principles/relaxation_scan.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **pulses**: this example uses an inversion pulse and a variable delay; the delay scans the recovery of longitudinal magnetization

Code flow analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The example scans several delays, reads the real component returned for each run, and fits the inversion-recovery model ``M(t) = C - A exp(-t/T1)``. The plot shows the measurements, fitted curve, T1, and goodness of fit. T1 is the timescale for longitudinal magnetization recovery.


Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: ../../../../_static/images/t1_result.png
   :width: 100%
   :align: center
   :alt: T1 longitudinal-relaxation experiment result

   T₁ inversion-recovery fit

Common result fields are listed below:

- **graph**: chart data for each delay
- **width**: Delay pulse width
- **real**: real part of signal strength
- **coordinate**: The coordinates of the qubit on the Bloch sphere
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results

T₂ Transverse Relaxation Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Measure transverse-magnetization decay with a spin-echo sequence

.. literalinclude:: ../../../../../examples/lab/two/principles/relaxation_scan.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``0`` for hydrogen or ``1`` for phosphorus
- **pulses**: this example uses four pulses:

  - First pulse: a π/2 pulse that creates transverse magnetization
  - Second pulse: the first delay
  - Third pulse: a π pulse that refocuses the spins
  - Fourth pulse: a second delay of equal length

Code flow analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The example varies two equal delays to scan the total echo time and reads the signal magnitude returned for each run. It fits the echo amplitude with the baseline-inclusive exponential model ``S(t) = A exp(-t/T2) + C``. The plot uses the total echo time ``2τ`` on its horizontal axis; T2 describes the decay timescale of the echo envelope.

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: ../../../../_static/images/t2_result.png
   :width: 100%
   :align: center
   :alt: T2 transverse-relaxation experiment result

   T₂ spin-echo decay fit; the horizontal axis shows the total echo time ``2τ``

Common result fields are listed below:

- **graph**: chart data for each total echo time
- **width**: Delay pulse width
- **mod**: Signal strength modulus
- **coordinate**: The coordinates of the qubit on the Bloch sphere
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results

Quantum Control Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using radio frequency fields to regulate the state of qubits

.. literalinclude:: ../../../../../examples/lab/two/principles/control.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **pulses**: this example uses two pulses:

  - First pulse: a π/2 pulse on the hydrogen channel (``path=0``)
  - Second pulse: a π/2 pulse on the phosphorus channel (``path=1``)

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each experiment step
- **coordinate**: The coordinates of the qubit on the Bloch sphere
- **matrix**: The density matrix of two qubit systems, including real and imaginary parts
- **probability**: probability distribution of measurement results

Quantum System Initialization Experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement the initialization process of quantum systems

.. literalinclude:: ../../../../../examples/lab/two/principles/initialization.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **repeat**: repeat count; must be at least ``0`` and defaults to ``5``; this example uses ``9``
- **pulses**: this example uses 12 pulses:

  - First six pulses: hydrogen-channel sequence (path=0) used to initialize the hydrogen nuclear spin
  - Last six pulses: phosphorus-channel sequence (path=1) used to initialize the phosphorus nuclear spin

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each system-initialization step
- **Hlamda**: hydrogen-channel Lambda parameter
- **Plamda**: phosphorus-channel Lambda parameter
- **fidelity**: initialization fidelity returned by the server**fidelity**: state fidelity reported by the server when this field is present
- **matrix**: two-qubit density matrix returned by the server
- **probability**: basis-state probabilities ordered as ``|00⟩``, ``|01⟩``, ``|10⟩``, and ``|11⟩``

Quantum Gates and Circuits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Build quantum gates and quantum circuits based on control operations

.. literalinclude:: ../../../../../examples/lab/two/principles/gates_circuit.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Pulse**: pulse parameters, including channel, width, amplitude, phase, and frequency offset; see ``spinqnmrlink.Pulse``
- **Gate**: quantum-gate parameters, including the gate type and target qubits; see ``spinqnmrlink.Gate``
- **Circuit**: the quantum circuit and its gates; see ``spinqnmrlink.Circuit``

- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **using_pulse**: selects the submitted representation. Set it to ``True`` to submit ``pulses`` or ``False`` to submit ``circuit``.
- **using_custom_gate**: whether to use a custom quantum gate
- **using_custom_pps**: whether to use custom PPS initialization
- **pps_json**: JSON string used for custom PPS initialization
- **pps_repeat**: number of repetitions for custom PPS initialization
- **Hlamda**: hydrogen-channel Lambda value; the system-initialization result can be used here
- **Plamda**: phosphorus-channel Lambda value; the system-initialization result can be used here

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each experiment step
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: basis-state probabilities ordered as ``|00⟩``, ``|01⟩``, ``|10⟩``, and ``|11⟩``

Quantum State Reconstruction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Observation and reconstruction of quantum states

.. literalinclude:: ../../../../../examples/lab/two/principles/tomography.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Gate**: quantum-gate parameters, including the gate type and target qubits; see ``spinqnmrlink.Gate``
- **Circuit**: the quantum circuit and its gates; see ``spinqnmrlink.Circuit``

- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **using_custom_gate**: whether to use a custom quantum gate
- **using_custom_pps**: whether to use custom PPS initialization
- **pps_json**: JSON string used for custom PPS initialization
- **pps_repeat**: number of repetitions for custom PPS initialization
- **Hlamda**: hydrogen-channel Lambda value; the system-initialization result can be used here
- **Plamda**: phosphorus-channel Lambda value; the system-initialization result can be used here

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each tomography step
- **q0_lamda**: spectral-fit parameter for the first qubit
- **q1_lamda**: spectral-fit parameter for the second qubit
- **q0_b**: spectral-fit parameter for the first qubit
- **q1_b**: spectral-fit parameter for the second qubit
- **matrix**: Reconstructed quantum state density matrix, including real and imaginary parts
- **probability**: probability distribution of measurement results
- **fidelity**: state fidelity reported by the server when this field is present
- **purity**: Purity of the quantum state, indicating the degree of mixing of the quantum state
- **entropy**: quantum-state entropy, which quantifies mixedness or uncertainty
- **raw**: complete reconstruction result returned by the server

Quantum Computing Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Carry out real quantum computing tasks

.. literalinclude:: ../../../../../examples/lab/two/principles/computing_task.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Gate**: quantum-gate parameters, including the gate type and target qubits; see ``spinqnmrlink.Gate``
- **Circuit**: the quantum circuit and its gates; see ``spinqnmrlink.Circuit``

- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **using_custom_gate**: whether to use a custom quantum gate
- **using_custom_pps**: whether to use custom PPS initialization
- **pps_json**: JSON string used for custom PPS initialization
- **pps_repeat**: number of repetitions for custom PPS initialization
- **Hlamda**: hydrogen-channel Lambda value; the system-initialization result can be used here
- **Plamda**: phosphorus-channel Lambda value; the system-initialization result can be used here

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: chart data returned for each quantum-computing task step
- **matrix**: The density matrix of the quantum state, including the real and imaginary parts
- **probability**: probability distribution of measurement results
- **fidelity**: fidelity returned by the server**fidelity**: state fidelity reported by the server when this field is present
- **gateNums**: number of quantum gates
- **hFre_offset**: hydrogen frequency offset
- **pFre_offset**: phosphorus frequency offset
- **pulseControlTime**: pulse-control time
- **pureTime**: pseudopure-state preparation time
- **purity**: quantum-state purity
- **relaxtion**: relaxation time
- **sampleTime**: sampling time
- **smt**: number of system-level measurements
