Quantum Algorithm
==================================

.. note::

   This teaching narrative uses public snake_case parameters. Detailed bounds and reference values are generated from the models on each experiment page. The figures illustrate the teaching material; hardware validation is recorded separately in the validation guide.

.. toctree::
   :maxdepth: 1

   algorithm_basic
   algorithm_deutsch
   algorithm_bernstein_vazirani
   algorithm_grover
   algorithm_qft
   algorithm_hhl
   algorithm_vqe
   algorithm_qaoa



This chapter covers how to run quantum algorithm experiments and interpret their common result fields.

.. literalinclude:: ../../../../../examples/lab/two/algorithms/algorithm_basic.py
   :language: python
   :linenos:

Experiment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **algorithm_type**: algorithm type; defaults to ``EXP_ALGORITHM_BASIC``
- **grover_bin**: Grover search target: ``0`` = \|00⟩, ``1`` = \|01⟩, ``2`` = \|10⟩, or ``3`` = \|11⟩

    .. list-table::
        :header-rows: 1
        :widths: 40 60

        * - attribute
          - described
        * - ``EXP_ALGORITHM_BASIC``
          - Basic Experiments of Quantum Computing
        * - ``EXP_DEUTSCH``
          - Deutsch algorithm experiment
        * - ``EXP_BERNSTEIN``
          - Bernstein-Vazirani algorithm experiment
        * - ``EXP_GROVER``
          - Grover algorithm experiment
        * - ``EXP_QFT``
          - QFT algorithm experiment
        * - ``EXP_HHL``
          - HHL algorithm experiment
        * - ``EXP_VQE``
          - VQE algorithm experiment
        * - ``EXP_QAOA``
          - QAOA algorithm experiment

- **Gate**: quantum-gate parameters, including the gate type and target qubits; see ``spinqnmrlink.Gate``
- **Circuit**: the quantum circuit and its gates; see ``spinqnmrlink.Circuit``
- **sample_path**: acquisition channel: ``-1`` for all channels, ``0`` for hydrogen, or ``1`` for phosphorus
- **calc_matrix**: whether to calculate the density matrix; defaults to ``True``

Experiment Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Common result fields are listed below:

- **graph**: Chart data, including experimental steps
- **matrix**: Density Matrix of the quantum state, including Real and Imaginary components
- **probability**: Probability Distribution of measurement results
- **fidelity**: fidelity returned by the server
- **gateNums**: number of quantum gates
- **hFre_offset**: hydrogen frequency offset
- **pFre_offset**: phosphorus frequency offset
- **pulseControlTime**: pulse-control time
- **pureTime**: pseudopure-state preparation time
- **purity**: purity
- **relaxtion**: relaxation time
- **sampleTime**: sampling time
- **smt**: number of system-level measurements
