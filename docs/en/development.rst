Development and extension
==================================================

Create and activate a Conda environment following :doc:`installation`, then install development dependencies from the repository root. Keep SDK code, examples and tools portable using pathlib and the active Python interpreter; avoid fixed Windows paths or shell launchers.

Architecture
------------------------

The public API owns device identity, typed settings, experiment validation and result envelopes. Private ``_core`` contains reusable primitives and reference presets. Private ``_backends`` owns wire serializers, result decoders and Python socket sessions. Backend imports may depend on core primitives; core primitives must not instantiate devices.

Lab session, request correlation, mode state, event routing and task management are separate mixins composed by one private backend. Callback threads must not mutate another device's state. A device accepts one active synchronous SDK experiment at a time.

Add an experiment
----------------------------------

Implement its private parameter serializer and decoder, register the factory, add a reference preset and a catalogue entry, and supply the public snake_case mapping where needed. Add a protocol fixture and parameter/result failure tests. Add an exact-key example and matching English/Chinese pages. ``parameters_for`` derives public typed models from serializers, so a second manually maintained schema is unnecessary.

Add a device protocol
--------------------------------------------------------------

Implement the backend session contract, explicit readiness and protocol capabilities. Keep transport, message encoding and session state separate. Triangulum transport.py owns WebSocket I/O, protocol.py owns JSON frames and result decoding, and session.py owns authentication, heartbeat and one correlated task. Add offline message fixtures and a loopback server test. Constructors must not start connections or workers.

Protocol generation
--------------------------------------

``message.proto`` is the source of truth for Lab Protobuf only; Triangulum JSON requires no Protobuf generation. When changing the Lab schema, use a separate Conda tool environment:

.. code-block:: console

   conda create --name spinq-protocol python=3.10 pip
   conda activate spinq-protocol
   python -m pip install grpcio-tools==1.70.0 protobuf==5.29.3
   python tools/generate_protocol.py
   conda activate spinqnmrlink

Run these commands from the repository root; change the final activation name if you chose a different SDK environment. Do not hand-edit generated Python. Device wire fields and parameter units must match the actual firmware protocol.

Checks and release
------------------------------------

Use the local validation commands in the
:download:`contribution guide <../../CONTRIBUTING.md>` for tests, lint, types,
the strict bilingual build, links, distributions and example checks.
Contribution and support entry points are in :doc:`community`.

``tools/check_docs.py`` compares the actual SDK catalogue with the example
manifest, each source's ``EXPERIMENT_KEY`` and both languages' parameter-table
keys and included examples. It also requires all source pages to have built
HTML and checks local fragments and exact counterpart language switches.
Run the strict build before this check.

Tests are offline by default. Record actual hardware evidence in ``validation_status.json``. Source distributions include tests, examples and bilingual sources; the SDK builds a pure-Python, platform-independent wheel. Keep source licenses and dependency notices complete.

See :doc:`devices` for CI platform targets. Each platform checks core tests, source examples, distribution contents and the installed SDK; mark results passed only with actual execution evidence.
