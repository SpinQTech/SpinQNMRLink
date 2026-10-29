Triangulum JSON WebSocket protocol
==================================

The Python backend communicates with the device service over text WebSocket frames. The URL is constructed from host, port, websocket_path and websocket_secure. No device native library is required.

Implementation boundaries
--------------------------

``transport.py`` owns the socket, text frames, polling timeouts and shutdown. ``protocol.py`` builds messages and decodes measurements. ``session.py`` owns authentication, heartbeat, a correlated task and bounded cleanup. Each session has independent state and one receive worker. Creating the SDK or preparing parameters does not connect.

Authentication and heartbeat
-----------------------------

.. code-block:: json

   {"msg_id":"user_login_request","account":"<account>","password":"<password>"}
   {"msg_id":"user_login_response","return_code":0,"session_id":"<session>"}
   {"msg_id":"heartbeat","session_id":"<session>"}
   {"msg_id":"user_logout_request","session_id":"<session>","account":"<account>"}

Login succeeds only with an integer return_code of zero and a non-empty session_id. Heartbeat starts after authentication. Idle sessions and malformed streams are closed. Logout waits within the close budget, then the socket and receive worker are released.

Task requests
---------------

.. important::

   **Triangulum client 2.0 or newer is required for density-matrix support**
   through ``calcMatrix: true``.

Circuit requests include top-level ``calcMatrix`` from public ``calc_matrix``
(default ``True``). It is separate from ``task_gates``. True requests density-matrix
components; False disables density-matrix calculation. The client may then return
empty component arrays, which mean absent matrix data. Physical requests omit this field.

Circuit messages use ``push_task_request``; physical messages use ``push_custom_task_request``. The remaining envelope fields are ``session_id``, ``task_id``, ``task_name``, ``task_description``, ``task_qubits`` and ``task_gates``. For circuits, task_gates is the serialized gate definition. For physical experiments, it is the pulse/parameters object, and task_qubits is 3.

Task identifiers are positive decimal strings within the signed 64-bit range, generated independently of second-resolution timestamps. The service must echo the task_id in acknowledgement and task events. Both the identifier and message family must match the current task; unrelated and duplicate messages cannot overwrite it.

.. list-table:: Correlated responses
   :header-rows: 1

   * - Circuit
     - Physical
     - Meaning
   * - push_task_response
     - push_custom_task_response
     - Submission acknowledgement; return_code zero accepts, other codes reject
   * - task_started_post
     - custom_task_started_post / task_started_post
     - Task started notification
   * - task_finished_post
     - custom_task_finished_post
     - Terminal task state and measurements

Physical tasks accept both ``custom_task_started_post`` and generic
``task_started_post`` for the matching task ID. Only the first start sets the
execution clock, even if it arrives before ACK or both aliases arrive. Once
started, the execution budget applies instead of the queue budget. ACK and
finish message families remain specific to the task kind.

The documented task-state codes are W (waiting), R (running), S (success) and F (failure). Acceptance keeps the SDK task PENDING; a matching start notification changes it to RUNNING. An acceptance acknowledgement alone does not mean execution has started. Only S can produce COMPLETED after successful decoding. Explicit T/TERMINATED is also classified as termination when supplied by a service, but availability is not a capability claim. Missing or malformed measurements never produce a successful result. A finish arriving before acknowledgement is retained until acceptance is confirmed.

Missing acknowledgement or disconnection produces an unknown outcome. An acknowledged task exceeding the local deadline produces a local timeout. Neither condition replays or cancels the remote task. Reconnection is explicit; verify unresolved tasks on the equipment before submitting more work.

Results and validation
-----------------------

Circuit execution probabilities and optional execution_matrix components are decoded into public fields. Missing optional fidelity, coordinates or qubit-count fields remain absent. Physical results retain graph_result_compressed as graph after checking its decoded structure and at least one finite chart point. The headless decoder requires an exact Qt length header and limits decompressed content to 64 MiB; empty or malformed measurements produce a processing failure. Successful results also contain ``protocol_raw`` with received submission/start/finish messages; authentication fields are redacted.

Offline fixtures are reconstructed from the protocol implementation and are not equipment measurements. The local loopback test exercises an actual HTTP WebSocket upgrade and masked client frames. Hardware validation, firmware behavior and platform installation evidence are recorded separately in :doc:`../validation`.

.. literalinclude:: ../../../examples/triangulum/circuit.py
   :language: python

The submitted ``calc_matrix`` selects density-matrix or state-vector decoding.
Nonempty components must number ``(2**n)**2`` or ``2**n`` respectively; a mismatch is a
local result-processing failure. Missing/null matrices remain optional. Flat
density components preserve their storage order as unknown rather than guessing it.
