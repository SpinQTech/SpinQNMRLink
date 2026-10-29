"""Exercise the actual standalone sources without equipment or GUI dependencies."""

import contextlib
import ctypes
import importlib.util
import io
import json
import math
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from spinqnmrlink import DeviceType, ExperimentResult, list_experiments
from spinqnmrlink.errors import ExperimentTimeoutError

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = json.loads(
    (ROOT / "tests/fixtures/protocol_parameters.json").read_text(encoding="utf-8")
)


MANIFEST = json.loads((ROOT / "examples/manifest.json").read_text(encoding="utf-8"))
SOURCE_PATHS = {entry["experiment_key"]: ROOT / entry["source"] for entry in MANIFEST}

FREQUENCY_KEYS = (
    "triangulum.physical", "lab.two.spin_echo", "lab.two.dynamic_decoupling",
    "lab.two.shaped_pulse", "lab.two.optimized_pulse", "lab.two.physical.custom",
    "lab.two.physical.pauli", "lab.two.physical.tomography", "lab.two.circuit.pulse",
    "lab.two.circuit.gates", "lab.three.physical_custom",
)
INVALID_FREQUENCIES = (
    0, 9999, 10001, 30000, 40000, 60000, 70000, 80000, 90000, 100001, 200000,
    "20000", 20000.0, True, [10000, 20000],
)


def load_source(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_example(key):
    return load_source(SOURCE_PATHS[key], "example_" + key.replace(".", "_"))


@pytest.mark.parametrize("key", FREQUENCY_KEYS)
@pytest.mark.parametrize("frequency", (10000, 20000, 50000, 100000))
def test_example_sample_frequency_choices(key, frequency):
    parameters = load_example(key).build_parameters()
    values = parameters.model_dump()
    values["sample_frequency"] = frequency
    changed = type(parameters)(**values)
    wire = changed.to_wire()
    # THREE/TWO put sampling settings directly in params, Triangulum nests them.
    assert wire.get("parameters", wire)["sampleFre"] == frequency
    assert changed.sample_frequency == frequency


@pytest.mark.parametrize("key", FREQUENCY_KEYS)
@pytest.mark.parametrize("frequency", INVALID_FREQUENCIES)
def test_example_sample_frequency_rejects_other_values(key, frequency):
    parameters = load_example(key).build_parameters()
    values = parameters.model_dump()
    values["sample_frequency"] = frequency
    with pytest.raises(ValidationError):
        type(parameters)(**values)


@pytest.mark.parametrize("key", FREQUENCY_KEYS)
@pytest.mark.parametrize("frequency", INVALID_FREQUENCIES)
def test_example_sample_frequency_assignment_rejects_other_values(key, frequency):
    parameters = load_example(key).build_parameters()
    original = parameters.sample_frequency
    with pytest.raises(ValidationError):
        parameters.sample_frequency = frequency
    assert parameters.sample_frequency == original
    parameters.to_wire()


@pytest.mark.parametrize("key", FREQUENCY_KEYS)
def test_sample_frequency_schema_has_exact_choices(key):
    parameters = load_example(key).build_parameters()
    field = type(parameters).model_json_schema()["properties"]["sample_frequency"]
    assert field["enum"] == [10000, 20000, 50000, 100000]
    assert "step" not in field and "multipleOf" not in field


OFFLINE_HELPER = load_source(ROOT / "examples/advanced/offline_parameters.py", "offline_helper")


def test_manifest_covers_catalogue_and_four_disjoint_lab_two_chapters():
    assert set(SOURCE_PATHS) == {entry.key for entry in list_experiments()}
    assert len(MANIFEST) == len(SOURCE_PATHS) == 35
    expected = {"principles": 10, "algorithms": 8, "technology": 4, "research": 5}
    for chapter, count in expected.items():
        entries = [entry for entry in MANIFEST if entry["chapter"] == chapter]
        assert len(entries) == count
        for entry in entries:
            assert entry["mode"] == "TWO"
            assert Path(entry["source"]).parent.name == chapter
    assert not list((ROOT / "examples/lab/two").glob("*.py"))
    for entry in MANIFEST:
        for language in ("en", "zh_CN"):
            page = (
                ROOT
                / "docs"
                / language
                / Path(entry["source"]).relative_to("examples").with_suffix(".rst")
            )
            assert page.is_file()
    for language in ("en", "zh_CN"):
        for chapter in expected:
            chapter_text = (ROOT / "docs" / language / "lab/two" / chapter / "index.rst").read_text(
                encoding="utf-8"
            )
            assert "lab/three" not in chapter_text


def test_advanced_saving_retains_raw_data_and_reports_missing_measurements(tmp_path):
    helper = load_source(ROOT / "examples/advanced/save_and_assess.py", "save_helper")
    result = ExperimentResult(
        DeviceType.LAB,
        "lab.two.rabi",
        "test-id",
        "COMPLETED",
        {"result": {}},
        {"parameters": {"sample_path": 0}},
    )
    destination = tmp_path / "nested/result.json"
    with contextlib.redirect_stdout(io.StringIO()):
        assessment = helper.save_and_assess(result, destination)
    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["raw"] == result.raw
    assert document["metadata"] == result.metadata
    assert document["assessment"] == assessment
    assert assessment["execution_validation"] == "INCOMPLETE"
    assert assessment["scientific_assessment"] == "NOT_ASSESSED"


def test_direct_typed_configuration_remains_offline_without_threads(monkeypatch):
    helper = load_source(ROOT / "examples/common/configure_devices.py", "connection_helper")
    before = {thread.ident for thread in threading.enumerate()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Configuring sessions must not load native libraries")

    monkeypatch.setattr(ctypes, "CDLL", forbidden)
    with contextlib.redirect_stdout(io.StringIO()):
        helper.inspect_sessions("192.0.2.20", "test", "test", "192.0.2.10", "test", "test")
    assert before == {thread.ident for thread in threading.enumerate()}


def test_copied_example_uses_the_callers_configuration_path(monkeypatch, tmp_path):
    copied = tmp_path / "rabi.py"
    copied.write_text(SOURCE_PATHS["lab.two.rabi"].read_text(encoding="utf-8"), encoding="utf-8")
    module = load_source(copied, "copied_rabi")
    result = ExperimentResult(
        DeviceType.LAB, "lab.two.rabi", "test-id", "COMPLETED", {"result": {"real": 1.0}}, {}
    )
    events = []
    install_session(module, monkeypatch, [result], events)
    monkeypatch.chdir(tmp_path)
    with contextlib.redirect_stdout(io.StringIO()):
        assert module.run_experiment() is result
    assert events[0] == ("config", "connection_config.local.json")
    assert events[-1] == "close"


@pytest.mark.parametrize("key", REFERENCES)
def test_standalone_source_parameters_match_protocol_without_connections(key, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline examples must not connect or load libraries")

    before = {thread.ident for thread in threading.enumerate()}
    monkeypatch.setattr(ctypes, "CDLL", forbidden)
    module = load_example(key)
    monkeypatch.setattr(module.SpinQNMRLink, "from_config", forbidden)
    parameters = module.build_parameters()
    request = OFFLINE_HELPER.check_parameters(key, parameters)
    assert request["experiment_key"] == key
    assert request["wire"] == REFERENCES[key]
    assert module.build_parameters() is not parameters
    assert before == {thread.ident for thread in threading.enumerate()}
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "spinqnmrlink.cli" not in source
    assert "argparse" not in source
    assert "OFFLINE_ONLY" not in source
    assert "__file__" not in source
    assert not any("\u4e00" <= character <= "\u9fff" for character in source)


def install_session(module, monkeypatch, results, events):
    """A session double checks order, arguments and cleanup around source code."""
    results = iter(results)

    class Session:
        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, *error):
            events.append("close")

        def device(self, device_type):
            events.append(("device", device_type))
            return self

        def open(self):
            events.append("open")

        def create_experiment(self, key, parameters):
            events.append(("prepare", key, parameters.to_wire()))

            def run(*, timeout, queue_timeout=None):
                assert "open" in events
                events.append(("run", timeout))
                events.append(("queue_timeout", queue_timeout))
                result = next(results)
                if isinstance(result, Exception):
                    raise result
                return result

            return SimpleNamespace(run=run)

    def from_config(path):
        events.append(("config", path))
        return Session()

    monkeypatch.setattr(module, "SpinQNMRLink", SimpleNamespace(from_config=from_config))


@pytest.mark.parametrize("entry", list_experiments(), ids=lambda entry: entry.key)
def test_standalone_source_lifecycle_returns_actual_measurements_without_saving(
    entry, monkeypatch, tmp_path
):
    module = load_example(entry.key)
    data = {
        "graph": [{"fidRe": [[0, 1]]}],
        "real": 0.0,
        "mod": 1.0,
        "width": 40,
        "probabilities": [0, 0, 0, 0, 0, 0, 0, 1],
        "final_data": {"test": "measurement"},
    }  # Test-double data, not a hardware measurement.
    monkeypatch.chdir(tmp_path)
    result = ExperimentResult(
        DeviceType(entry.device_type),
        entry.key,
        "test/task",
        "COMPLETED",
        {"result": data} if entry.device_type == "lab" else data,
        {"parameters": module.build_parameters().model_dump(mode="json")},
    )
    events = []
    install_session(module, monkeypatch, [result], events)
    with contextlib.redirect_stdout(io.StringIO()):
        returned = module.run_experiment("test-config.json", timeout=12, queue_timeout=600)
    assert returned is result
    assert ("device", entry.device_type) in events
    assert ("run", 12) in events
    assert ("queue_timeout", 600) in events
    assert events[-1] == "close"
    assert returned.data == data
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("key", ("lab.two.rabi", "lab.three.circuit", "triangulum.circuit"))
def test_standalone_source_timeout_propagates_and_closes_without_output(key, monkeypatch, tmp_path):
    module = load_example(key)
    failure = ExperimentTimeoutError("Task exceeded the local deadline")
    events = []
    install_session(module, monkeypatch, [failure], events)
    with pytest.raises(ExperimentTimeoutError):
        module.run_experiment("test-config.json", timeout=1)
    assert events[-1] == "close"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("entry", list_experiments(), ids=lambda entry: entry.key)
def test_basic_sources_reject_missing_measurements_and_close_sessions(entry, monkeypatch):
    module = load_example(entry.key)
    result = ExperimentResult(
        DeviceType(entry.device_type),
        entry.key,
        "test-id",
        "COMPLETED",
        {"result": {}} if entry.device_type == "lab" else {},
        {},
    )
    events = []
    install_session(module, monkeypatch, [result], events)
    with contextlib.redirect_stdout(io.StringIO()), pytest.raises(ValueError):
        module.run_experiment("test-config.json")
    assert events[-1] == "close"


def load_scan(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "examples/lab/two/principles" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scan_sources_validate_points_offline_and_reject_invalid_settings(monkeypatch):
    rabi = load_scan("rabi_scan")
    relaxation = load_scan("relaxation_scan")

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline scan must not create a session")

    for module in (rabi, relaxation):
        monkeypatch.setattr(module.SpinQNMRLink, "from_config", forbidden)
    with contextlib.redirect_stdout(io.StringIO()):
        assert len(rabi.run_scan(offline=True)["points"]) == 9
        assert len(relaxation.run_scan("t1", offline=True)["points"]) == 4
        assert len(relaxation.run_scan("t2", offline=True)["points"]) == 6
    with pytest.raises(ValueError):
        rabi.build_scan(channel=2)
    with pytest.raises(ValueError):
        rabi.build_scan(widths_us=[0, 40])
    with pytest.raises(ValueError):
        relaxation.build_scan("invalid")
    with pytest.raises(ValueError):
        relaxation.build_scan("t2", delays_us=[-10, 0, 100])


def test_rabi_scan_fits_actual_amplitudes_and_retains_all_raw_points(monkeypatch, tmp_path):
    module = load_scan("rabi_scan")
    widths = list(range(0, 401, 40))
    results = [
        ExperimentResult(
            DeviceType.LAB,
            "lab.two.rabi",
            str(width),
            "COMPLETED",
            {"result": {"real": math.sin(2 * math.pi * width / 160), "graph": {"signal": [1]}}},
            {},
        )
        for width in widths
    ]
    events = []
    install_session(module, monkeypatch, results, events)
    with contextlib.redirect_stdout(io.StringIO()):
        document = module.run_scan(
            "test-config.json", widths_us=widths, timeout=12, output_directory=tmp_path
        )
    assert len(document["raw_results"]) == len(widths)
    assert abs(document["fit"]["period_us"] - 160) < 1
    assert document["assessment"]["execution_validation"] == "PASS"
    assert events[-1] == "close"
    assert json.loads((tmp_path / "rabi_scan.json").read_text(encoding="utf-8"))["raw_results"] == [
        result.to_dict() for result in results
    ]


@pytest.mark.parametrize("kind", ("t1", "t2"))
def test_relaxation_scan_reads_correct_amplitude_and_closes_on_bad_data(
    kind, monkeypatch, tmp_path
):
    module = load_scan("relaxation_scan")
    field = "real" if kind == "t1" else "mod"
    results = [
        ExperimentResult(
            DeviceType.LAB,
            "lab.two." + kind,
            str(index),
            "COMPLETED",
            {"result": {field: value, "graph": {"signal": [1]}}},
            {},
        )
        for index, value in enumerate((3.0, 2.0, 1.0))
    ]
    events = []
    install_session(module, monkeypatch, results, events)
    with contextlib.redirect_stdout(io.StringIO()):
        document = module.run_scan(
            kind, "test-config.json", delays_us=[0, 100, 200], output_directory=tmp_path
        )
    assert [row["amplitude"] for row in document["measurements"]] == [3, 2, 1]
    assert document["assessment"]["scientific_assessment"] == "NOT_ASSESSED"
    assert events[-1] == "close"
    bad = ExperimentResult(DeviceType.LAB, "lab.two." + kind, None, "COMPLETED", {"result": {}}, {})
    events = []
    install_session(module, monkeypatch, [bad], events)
    with pytest.raises(ValueError, match="finite relaxation amplitude"):
        module.run_scan(
            kind, "test-config.json", delays_us=[0, 100, 200], output_directory=tmp_path
        )
    assert events[-1] == "close"
