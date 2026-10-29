# SpinQNMRLink

[English](README.md) | [中文](README.zh_CN.md)

One Python SDK for **Lab** and **Triangulum** devices. One SDK owns independent sessions for either or both device types, a catalogue of 35 experiments, typed parameters and bounded task execution.

Use it to build Python experiment workflows across the two device families with a shared API for configuration, parameter validation and results. Hardware execution requires a reachable device service, credentials and sample calibration; catalogue browsing and parameter validation work offline.

## Installation

```console
conda create --name spinqnmrlink python=3.10 pip
conda activate spinqnmrlink
python -m pip install -e .
```

We recommend Conda for source checkouts. Install Conda, enter the repository root containing `pyproject.toml`, then run the commands above. Select this environment in your IDE. Python 3.8 is the minimum; 3.8, 3.10 and 3.12 are the test targets. Windows, Linux and macOS use the same installation flow without platform-specific launch scripts. See the [installation guide](docs/en/installation.rst). Lab uses TCP or binary WebSocket; Triangulum uses JSON text WebSocket implemented directly in Python. The SDK contains no device DLL/SO and builds a platform-independent wheel. Platform availability depends on Python dependencies and actual installation checks. See [validation evidence](validation_status.json) for actual checks.

## Quickstart

Verify the installation without hardware or credentials:

```console
python -c "from spinqnmrlink import list_experiments; print(len(list_experiments()))"
```

This prints 35. For a device run, follow [configuration setup](docs/en/configuration.rst) to create `connection_config.local.json` from the template and fill in the service address. Lab uses nonempty reserved account/password fields; Triangulum uses credentials created in the client software's User Center. Literal values work directly; `env:VARIABLE` references are optional. Keep local configurations private. Use the actual device calibration for pulse, frequency and sample values.

```python
from spinqnmrlink import SpinQNMRLink, parameters_for

with SpinQNMRLink.from_config("connection_config.local.json") as sdk:
    lab = sdk.device("lab")
    parameters = parameters_for("lab.two.rabi")
    parameters.pulses[0].width_us = 40  # replace with a calibrated reference value
    experiment = lab.create_experiment("lab.two.rabi", parameters=parameters)
    lab.open()
    result = experiment.run(timeout=300, queue_timeout=600)
    print(result.status, result.data)
```

Constructors, parameter validation and catalogue browsing do not connect. Network connections and receive workers start only in `open()`. Closing the SDK cleans up both sessions. A local timeout does not stop a remote experiment; rejected, failed, terminated and uncertain submissions have distinct errors.

`timeout` limits execution waiting after the first started notification; `queue_timeout` limits queue waiting after acceptance. Omitting `queue_timeout` allows unlimited queue waiting while connection monitoring remains active. Acknowledgement has its own `request_timeout`. Where an experiment exposes `sample_frequency_hz`, choose one integer: `10000`, `20000`, `50000` or `100000` (Hz). See [parameters](docs/en/parameters.rst) for constraints and timing, and [troubleshooting](docs/en/troubleshooting.rst) for disconnect notifications.

**Triangulum density-matrix support requires Triangulum client 2.0 or newer.** This requirement applies to `calc_matrix=True` / `calcMatrix: true`; see the [circuit guide](docs/en/triangulum/circuit.rst).

## Examples and documentation

All 35 standalone Python examples are in [examples](examples/README.md). Rabi and T1/T2 scans provide measured-data analyses. Each basic source shows explicit parameters, execution and measurement access. Call `run_experiment()` for hardware; separate advanced sources provide offline checks, saving and assessment. Lab TWO examples and documentation are organized into four chapters. Examples run without a GUI; install `.[plot]` for optional plotting and fitting, or `.[qt]` for Qt helpers.

Read the [English manual](docs/en/index.rst) or [中文文档](docs/zh_CN/index.rst). For local HTML with per-page language switching:

```console
python -m pip install -e ".[dev,docs]"
python tools/build_docs.py
python tools/check_docs.py
```

Open `docs/_build/html/en/index.html` or `docs/_build/html/zh_CN/index.html` after building.

## Project layout

- `src/spinqnmrlink/`: SDK implementation and device adapters.
- `examples/`: runnable examples for all 35 experiments.
- `docs/`: English and Chinese documentation sources.
- `tests/`: offline SDK regression tests and protocol fixtures.
- `tools/`: documentation, distribution, example and protocol-generation utilities; see [tools/README.md](tools/README.md).

## Contributing and support

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, checks and pull requests, and [development](docs/en/development.rst) for architecture and extension guidance. For help or bug reports, read [SUPPORT.md](SUPPORT.md); report suspected vulnerabilities privately following [SECURITY.md](SECURITY.md). Release notes are in [CHANGELOG.md](CHANGELOG.md).

## License

Python sources use [GPL-3.0-only](LICENSE.txt).
