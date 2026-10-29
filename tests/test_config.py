import json
from pathlib import Path

import pytest
from pydantic import SecretStr

from spinqnmrlink import ConfigurationError, LabSettings, load_settings


def test_example_template_loads_literal_reserved_and_authenticated_fields(monkeypatch):
    for name in ("LAB_ACCOUNT", "LAB_PASSWORD", "TRIANGULUM_ACCOUNT", "TRIANGULUM_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    path = Path(__file__).resolve().parents[1] / "examples/connection_config.example.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    settings = load_settings(path)
    for name in ("lab", "triangulum"):
        section = getattr(settings, name)
        assert section.account.get_secret_value() == document[name]["account"]
        assert section.password.get_secret_value() == document[name]["password"]
        assert document[name]["password"] not in repr(settings)


def test_environment_credentials_and_safe_representation(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_ACCOUNT", "private-account")
    monkeypatch.setenv("TEST_PASSWORD", "private-password")
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "lab": {
                    "host": "localhost",
                    "port": 8181,
                    "account": "env:TEST_ACCOUNT",
                    "password": "env:TEST_PASSWORD",
                }
            }
        )
    )
    settings = load_settings(path)
    assert settings.lab.password.get_secret_value() == "private-password"
    assert "private-password" not in repr(settings)
    assert "private-account" not in repr(settings)


@pytest.mark.parametrize(
    "change",
    [
        {"port": True},
        {"port": 0},
        {"host": " "},
        {"password": "env:ABSENT_SDK_TEST_ENV"},
        {"unknown": 1},
    ],
)
def test_invalid_fields_rejected_without_disclosing_credentials(tmp_path, change):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "lab": {
                    "host": "localhost",
                    "port": 8181,
                    "account": "private-account",
                    "password": "private-password",
                    **change,
                }
            }
        )
    )
    with pytest.raises(ConfigurationError) as caught:
        load_settings(path)
    assert "private-password" not in str(caught.value)
    assert "private-account" not in str(caught.value)


def test_unknown_sections_are_not_accepted(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"spinqlablink": {}}))
    with pytest.raises(ConfigurationError):
        load_settings(path)


@pytest.mark.parametrize("field", ("account", "password"))
def test_empty_secret_objects_cannot_bypass_required_credentials(field):
    values = dict(host="localhost", port=8181, account="test", password="test")
    values[field] = SecretStr("")
    with pytest.raises(ValueError, match="non-empty"):
        LabSettings(**values)
