"""Validate every experiment source offline; no device credentials are needed."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    spec = importlib.util.spec_from_file_location(
        "offline_parameters", ROOT / "examples/advanced/offline_parameters.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    entries = json.loads((ROOT / "examples/manifest.json").read_text(encoding="utf-8"))
    for entry in entries:
        request = helper.check_example(ROOT / entry["source"])
        assert request["experiment_key"] == entry["experiment_key"]
    print("All {} standalone experiment sources passed offline validation.".format(len(entries)))


if __name__ == "__main__":
    main()
