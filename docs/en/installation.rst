Installation from source
========================

The SDK targets Windows, Linux and macOS. Both device adapters use Python network protocols; no device DLL/SO, compiler or GUI is required for core use. Python 3.8 is the minimum; 3.8, 3.10 and 3.12 are the test targets. For a new source checkout, we recommend a Conda environment with Python 3.10.

Create the environment
----------------------

Install Conda using its `official installation guide <https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html>`_. Use a terminal where Conda is initialized: for example, Anaconda Prompt on Windows or your initialized shell on Linux/macOS. Create and activate a separate environment:

.. code-block:: console

   conda create --name spinqnmrlink python=3.10 pip
   conda activate spinqnmrlink

Follow the `Conda environment guide <https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html>`_ if activation is unavailable. The environment name is yours to choose. These commands do not depend on a repository-local interpreter path.

Install the checkout
---------------------

After cloning or downloading the source, change into the repository root containing ``pyproject.toml``. Install into the activated environment:

.. code-block:: console

   python -m pip install -e .
   python -c "from spinqnmrlink import list_experiments; print(len(list_experiments()))"

The import check prints 35 and does not connect to equipment. Editable installation makes changes to SDK source visible without reinstalling. Use ``python -m pip install .`` instead when you want a regular installation.

Dependencies are declared in ``pyproject.toml`` and installed by pip inside the Conda environment; the SDK is not published as a Conda package. In an IDE, select the Python interpreter of this environment and use the repository root as the working directory. No automatic environment or device-launch script is needed. See :doc:`quickstart` for directly callable Python examples.

Optional features and development
----------------------------------

.. code-block:: console

   python -m pip install -e ".[dev,docs]"

Use this development installation for tests, linting and documentation. Plotting/fitting is optional: ``python -m pip install -e ".[plot]"``. Qt helpers use ``python -m pip install -e ".[qt]"`` and depend on availability of GUI packages for the selected operating system, architecture and Python version. Core networking, catalogues and offline checks work without either extra. Quoting extras also works in shells that interpret square brackets.

Activate the environment in each new terminal. Install any additional Conda packages before pip packages; keep project dependency constraints in ``pyproject.toml``. Python 3.8 dependencies have upper bounds for packages that dropped that interpreter. Platform verification and device integration are recorded separately in :doc:`devices` and :doc:`validation`.
