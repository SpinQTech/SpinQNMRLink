Configuration
=============

The root accepts ``lab`` and/or ``triangulum``. Common fields are ``host``, ``port``, ``account``, ``password``, ``connection_timeout`` and ``request_timeout``. The delivered template uses literal values. Settings representations and SDK errors redact credentials.

Prepare a local configuration
-----------------------------

From the repository root, copy the template to a new local file. Edit the existing file instead if you already have one:

.. code-block:: console

   python -c "from shutil import copyfile; copyfile('examples/connection_config.example.json', 'connection_config.local.json')"

Keep only the device sections you use. Replace ``host`` and ``port`` with the actual service address. Both fields are required; template ports are examples.

- Lab ``account`` and ``password`` are reserved fields. Keep the template's nonempty literals or use your deployment's existing reserved values. The SDK validates type and nonempty format without adding an account-validity check. The existing session handshake and authoritative mode/state synchronization must still complete before READY.
- Triangulum retains its existing authentication: first create an account and password in the client software's **User Center (用户中心)**, then enter the same values in ``triangulum.account`` and ``triangulum.password``. The ``replace-with-...`` placeholders cannot log in. Writing JSON does not create an account.

.. literalinclude:: ../../examples/connection_config.example.json
   :language: json

The local configuration is ignored by Git. Optional ``env:VARIABLE`` references remain supported; those variables must exist before loading. The default template and experiment examples do not require environment variables.

Source distributions include only the public template and manifest as example JSON. Local profiles are excluded and checked before release; keep the template's addresses and credentials as placeholders.

Settings and timeouts
---------------------

Lab adds ``transport`` (``tcp`` or ``websocket``), ``websocket_path``, ``websocket_secure``, heartbeat and reconnect settings. Triangulum accepts ``websocket_path`` (default empty), ``websocket_secure`` (default False), ``heartbeat_interval`` (10 seconds), ``heartbeat_timeout`` (30 seconds) and ``max_message_bytes`` (32 MiB). Initial login omits session_id; heartbeat and task messages use the authenticated session_id.

Connection and request-acknowledgement budgets each default to 10 seconds. Closing defaults to a 5-second cleanup budget. Acknowledgement uses ``request_timeout`` independently of the execution budget.

.. code-block:: python

   result = experiment.run(timeout=300, queue_timeout=600)

``timeout`` is a finite positive execution-wait budget starting at the first matching started/RUNNING notification. Optional ``queue_timeout`` starts after acceptance and defaults to ``None`` (unlimited queue waiting); when provided it must also be finite and positive. Example functions default execution to 300 seconds and forward ``queue_timeout``. Heartbeat loss, explicit close and interruption still interrupt queue waiting.

Timeout errors retain ``task_id`` and ``status`` and expose ``phase`` as ``queue`` or ``execution``. Local timeouts never cancel or replay remote tasks. See :doc:`parameters` for phase-specific timing metadata.

Connection settings are immutable. Construct snake_case parameters in ``build_parameters()`` and pass them to ``run_experiment(parameters=...)``. Unknown fields and invalid nested values are rejected before submission. For programmatic configuration, pass ``SDKSettings(lab=LabSettings(...), triangulum=TriangulumSettings(...))`` to ``SpinQNMRLink``. Reading JSON or constructing settings never starts a connection.
