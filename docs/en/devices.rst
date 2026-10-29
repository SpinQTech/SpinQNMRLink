Devices and platform support
============================

The public device names are Lab and Triangulum. Each SDK owns at most one instance of each, with independent connections, tasks and failures. There is no automatic device fallback.

Lab uses TCP or binary WebSocket and supports TWO and THREE modes verified against authoritative server state. TWO examples and documentation have four chapters; THREE is separate.

Triangulum implements JSON text WebSocket directly in Python, including authentication, application heartbeat, submission acknowledgement and task-result correlation. Its readiness means an authenticated connection, not a Lab-style state snapshot. Transport failure closes the session; an unresolved task reports an unknown outcome. Reconnection is explicit and tasks are never automatically replayed. See :doc:`protocols/triangulum_protocol` for message and result details.

Cross-platform design
----------------------

Windows, Linux and macOS use the same public API, Conda source installation and Python examples. Both adapters connect to a reachable device service over the network; neither needs a bundled device native library. Constructors and parameter validation remain offline. ``open()`` establishes a session; ``close()`` releases sockets and receivers without cancelling a remote experiment.

The distribution is a ``py3-none-any`` wheel. This describes the SDK's Python-only packaging, not universal availability of its dependencies. Core checks require no GUI; optional plotting and Qt dependencies have separate platform requirements. The client operating system does not change the device service, firmware or supported experiment modes.

Verification targets
---------------------

.. list-table:: Core installation and offline checks
   :header-rows: 1

   * - Client platform
     - Python targets
     - Evidence
   * - Windows x86_64
     - 3.8, 3.10, 3.12
     - Current Python 3.12 offline and loopback checks passed; 3.8/3.10 reruns pending
   * - Linux x86_64
     - 3.8, 3.10, 3.12
     - Tester reported platform pass; individual matrix entry not recorded
   * - macOS Intel
     - 3.8, 3.10, 3.12
     - Tester reported platform pass; individual matrix entry not recorded
   * - macOS ARM64
     - 3.10, 3.12
     - Tester reported platform pass; individual matrix entry not recorded

Python 3.8 on macOS ARM64 is not a verification target. Other architectures and interpreter versions need dependency installation and protocol checks before support is claimed. These targets apply to both adapters. Firmware behavior and real-device measurements remain separate evidence in :doc:`validation`.

Linux and macOS installation/testing were confirmed by the user as completed
by a tester. Exact Python versions and architectures were not supplied; table
rows are CI targets and do not independently certify every matrix entry.
