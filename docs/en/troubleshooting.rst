Troubleshooting
==============================

For import failures, activate your Conda environment and ensure your IDE uses that same interpreter. From the repository root, run ``python -m pip show SpinQNMRLink``. Use your chosen environment name instead of spinqnmrlink if different; do not rely on a fixed repository-local interpreter path.

If configuration fails, check top-level device names, port type/range and environment variables. Configuration errors deliberately omit credential inputs.

If Lab is connected but not ready, verify authentication and that the server has provided authoritative mode, device information, parameters and queue state. THREE tasks are not valid in TWO mode. Selecting WebSocket/WSS does not enable a server endpoint.

For Triangulum connection failures, verify the device WebSocket service, host, port, path, ws/wss setting and credentials. If login returns ``return_code=2`` (account or password error), open the Triangulum client software, confirm that you created the account and password in **User Center (用户中心)**, and use the same credentials in the connection configuration; see :doc:`configuration`. A heartbeat or protocol failure closes the session; inspect the device task queue before reopening an unresolved task.

Physical-layer experiments (``triangulum.physical``) require **Triangulum client software version 1.6.1 or later**; earlier versions do not support this experiment. If connection and login succeed but a physical experiment cannot run, check the client version first; see :doc:`triangulum/physical`.

If an acknowledgement is lost or local waiting times out, record the task ID and last state, check the device queue, and reconcile that task before reconnecting or running again. A remote task can continue after local cleanup. Do not replay uncertain submissions.

A Triangulum success notification with malformed required measurements raises an experiment failure. For returned results, assessment helpers report missing or invalid measurements as structurally incomplete. It is not evidence of scientific success. For poor Rabi or relaxation fits, inspect pulse calibration, sample preparation, scan range and raw measurements.


Unexpected disconnection diagnostics
------------------------------------

Subscribe through the public Device without accessing a private backend:

.. code-block:: python

   unsubscribe = device.subscribe_disconnect(
       lambda event: print(event.reason, event.task_ids, dict(event.diagnostics))
   )
   device.open()
   # ... run experiments ...
   device.close()
   print(device.last_disconnect_reason)
   unsubscribe()

Explicit normal close emits no failure event. Unexpected loss retains the first reason and notifies once per connection. ``last_disconnect_event`` and ``last_disconnect_reason`` survive close and reset on a new open. Callbacks run on a separate observer thread and should return promptly; one callback's exception does not suppress others. Close drains queued notifications within its budget; a blocking callback can cause a cleanup-timeout error.

Triangulum diagnostics include local monotonic times for last receive, last send and last actual heartbeat send, idle seconds and the heartbeat threshold. Before a heartbeat has been sent, its timestamp is ``None``; without version evidence, ``server_version=None``. Reasons redact credentials and are never uploaded externally. Empty business messages, invalid Unicode and protocol errors use the same loss notification path. ``ExperimentTimeoutError.phase == "queue"`` distinguishes queue waiting from execution timeout.
