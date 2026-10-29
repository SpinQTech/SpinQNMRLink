Parameters, units and results
==========================================================

Use ``parameters_for(key)`` to obtain the exact typed model for an experiment. Its fields are snake_case. Validate offline using ``parameters.to_wire()``; this preserves the existing server protocol.

``Pulse`` uses ``channel`` (zero-based), ``width_us``, ``amplitude_percent``, ``phase_deg`` and ``detuning_hz``. ``Gradient`` uses ``path``, ``voltage_v`` and ``duration_us``. Circuit gate indices are zero-based; rotation angles use degrees. Public Lab THREE ``sample_qubits`` are also zero-based and are converted to protocol indices 1, 2, 3 by the adapter. Triangulum physical ``sample_qubits`` retains the device's ``sampleQubit`` protocol values unchanged; the Lab THREE conversion does not apply.

Public relaxation times use seconds. Triangulum physical-layer serialization converts seconds to microseconds. Lab TWO sampling counts must be powers of two from 1024 to 16384, with one exception: ``lab.two.spin_echo`` also accepts 16000. Triangulum physical-layer counts are from 1 to 16000. THREE constraints are validated by their own models. Do not reuse one experiment's sampling limits for another. Sampling frequency is one integer Hz value from ``10000, 20000, 50000, 100000``. Other rates such as 30000 or 40000 are not supported; floats, strings, booleans and lists are rejected.

Experiment pages below show parameter tables generated from actual models and reference values. These are configuration examples, not authoritative calibration values. The schema plus device serializer defines the accepted constraints; undocumented device frequency units are retained without inventing a conversion.

``ExperimentResult`` contains device type, experiment key, available task ID, remote status, raw backend data and metadata (SDK version, UTC timestamps and actual public parameters). ``data`` selects Lab's result object or Triangulum's direct data. Missing optional fields may be absent or ``None`` depending on the adapter; no missing measurement is replaced by a synthetic value. Complex values serialize as real/imaginary objects; non-finite numbers are rejected when exporting JSON.

Triangulum circuits require probabilities with the submitted circuit's dimension. Fidelity, state vector, qubit-count echo and coordinates are optional. ``assess_result`` checks dimensions against submitted parameters when available and does not mark an otherwise valid result incomplete just because these optional fields were omitted. Scientific assessment remains NOT_ASSESSED.

Triangulum physical completion requires a decodable chart containing at least one finite point. Compressed charts have an exact Qt length header and a 64 MiB decoded-size limit; malformed or empty charts raise a result-processing failure. The original graph representation is retained in the result.

Submission rejection, processing/remote failure, termination, local wait timeout and unknown submission outcome are separate errors. A local timeout does not cancel or prove completion of the remote task. The SDK blocks another task in an unresolved session; an explicit close/open creates a fresh session, and the operator must first reconcile the prior task on the device. Automatic reconnect never replays submissions.

Lab THREE uses the common pulse and gradient models: ``pulse.h_pulse`` accepts channel 0 only; gradient durations must be integer microseconds. THREE circuits use the common ``Circuit(qubits=3, ...)`` model.


Missing or null optional ``execution_matrix`` returns the actual probabilities alone. ``2^n`` complex positions retain ``state_vector``; ``(2^n)^2`` positions produce ``density_matrix`` with the original flat ``real``/``imag`` components, ``shape=[2^n, 2^n]`` and ``order=None``. This explicitly means storage order is unknown: the SDK does not reshape the components into an assumed two-dimensional layout. Incorrect dimensions or unequal component lengths still fail parsing.

Timing metadata separates ``submitted_at_utc``, ``acknowledged_at_utc``, ``execution_started_at_utc`` and ``finished_at_utc``. Legacy ``started_at_utc`` remains the submission-call time, not the execution start. ``queue_duration_seconds`` measures acceptance to start and ``execution_duration_seconds`` measures start to completion. Start preceding ACK gives zero queue duration. A valid terminal result without a start notification leaves execution start and both durations as ``None``. All times are local SDK observations, not device wall-clock measurements.

Triangulum physical timing recognizes both ``task_started_post`` and
``custom_task_started_post`` for the submitted task. Duplicate starts retain the
first timestamp; matching starts switch queue waiting to execution waiting.
