Validation evidence
======================================

Unit tests and serialized reference fixtures are offline evidence, not device measurements. CI targets Windows, Linux and macOS Intel with Python 3.8, 3.10 and 3.12, plus macOS ARM64 with Python 3.10 and 3.12. The matrix is detailed in :doc:`devices`. A configured job is not a passed job.

.. literalinclude:: ../../validation_status.json
   :language: json

The latest local candidate is checked on Windows x86_64 with Python 3.12.15.
Current local results cover Python 3.12.15. Linux/macOS platform testing was
reported passed by the user; individual Python/architecture entries were not supplied. Type checking uses the repository's
default configuration and covers six public source modules. Package checks
include local-configuration exclusions as well as isolated wheel installation.

Every hardware experiment remains pending until its device, firmware, configuration, measurement and outcome are recorded. The SDK has no bundled device binaries. Linux/macOS platform verification is tester-reported with matrix details unrecorded; a universal wheel is not proof that every dependency or device service is supported.
