# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Validate an example's typed parameters without connecting to equipment."""

import importlib.util
from pathlib import Path


def check_parameters(experiment_key, parameters):
    """Return the effective public parameters and their exact wire representation."""
    return {
        "source": "offline reference parameters; not measured data",
        "experiment_key": experiment_key,
        "parameters": parameters.model_dump(mode="json"),
        "wire": parameters.to_wire(),
    }


def check_example(source_path):
    """Import a standalone source file and validate its definition; do not run its main block."""
    path = Path(source_path)
    spec = importlib.util.spec_from_file_location("offline_example_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return check_parameters(module.EXPERIMENT_KEY, module.build_parameters())


if __name__ == "__main__":
    from spinqnmrlink.experiments import serialize_result_document

    # Resolve from your working directory; copying the example does not change this path.
    request = check_example("examples/lab/two/principles/rabi.py")
    print(serialize_result_document(request))
