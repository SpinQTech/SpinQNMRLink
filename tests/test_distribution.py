"""Release checks must reject local profiles before attempting installation."""

import importlib.util
import io
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_distribution", ROOT / "tools/check_distribution.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_distributions(directory, *, source_extra=(), wheel_extra=()):
    with zipfile.ZipFile(directory / "sdk-1.0.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("sdk-1.0.0.dist-info/WHEEL", "Root-Is-Purelib: true\nTag: py3-none-any\n")
        for name in wheel_extra:
            wheel.writestr(name, "{}")
    public_files = (
        "tests/test_triangulum_protocol.py",
        "docs/en/installation.rst",
        "docs/zh_CN/installation.rst",
        "examples/manifest.json",
        "examples/connection_config.example.json",
        "tests/fixtures/protocol_parameters.json",
    )
    with tarfile.open(directory / "sdk-1.0.0.tar.gz", "w:gz") as archive:
        for name in public_files + source_extra:
            item = tarfile.TarInfo("sdk-1.0.0/" + name)
            item.size = 2
            archive.addfile(item, io.BytesIO(b"{}"))


@pytest.mark.parametrize("kind", ("source", "wheel"))
@pytest.mark.parametrize("path", (
    "examples/connection_config.json",
    "examples/nested/connection_config.production.local.json",
    "examples/nested/operator-settings.json",
    "connection_profile.local.json",
))
def test_reject_local_configuration_before_install(tmp_path, monkeypatch, kind, path):
    make_distributions(tmp_path, **{kind + "_extra": (path,)})
    checker = load_checker()
    calls = []
    monkeypatch.setattr(checker.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(checker.sys, "argv", ["check_distribution", "--dist-dir", str(tmp_path)])
    monkeypatch.setattr(checker.subprocess, "run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(SystemExit, match="Local or unapproved configuration"):
        checker.main()
    assert calls == []


def test_public_template_manifest_and_protocol_fixtures_are_allowed(tmp_path, monkeypatch):
    make_distributions(tmp_path)
    checker = load_checker()
    calls = []
    monkeypatch.setattr(checker.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(checker.sys, "argv", ["check_distribution", "--dist-dir", str(tmp_path)])
    monkeypatch.setattr(checker.subprocess, "run", lambda *args, **kwargs: calls.append(args))
    checker.main()
    assert len(calls) == 2
