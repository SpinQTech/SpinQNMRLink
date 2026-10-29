import math
import subprocess
import sys
from pathlib import Path

import pytest

from spinqnmrlink import DeviceType, ExperimentResult, list_experiments, parameters_for
from spinqnmrlink.analysis.rabi import fit_rabi, validate_rabi
from spinqnmrlink.validation import assess_result


def test_rabi_validation_returns_an_assessment_on_normal_path():
    rows = [
        {
            "width_us": x,
            "amplitude": math.sin(2 * math.pi * x / 160),
            "task_completed": True,
            "graph_returned": True,
        }
        for x in range(0, 401, 40)
    ]
    fit = fit_rabi(rows)
    assessment = validate_rabi({"H": {"measurements": rows, "fit": fit}})
    assert assessment["execution_validation"] == "PASS"
    assert assessment["fit_assessment"] == "GOOD"
    assert abs(fit["period_us"] - 160) < 1


def test_missing_result_is_incomplete_not_scientific_success():
    result = ExperimentResult(DeviceType.LAB, "lab.two.rabi", None, "COMPLETED", {"result": {}}, {})
    assessment = assess_result(result)
    assert assessment["execution_validation"] == "INCOMPLETE"
    assert assessment["scientific_assessment"] == "NOT_ASSESSED"


def test_lab_tomography_accepts_fit_coefficients_without_reconstructed_metrics():
    data = {"graph": [{"fidRe": [[0, 1]]}], "q0_lamda": 25.48, "q1_lamda": 25.03,
            "matrix": {}, "probability": [], "fidelity": None, "purity": None, "entropy": None}
    result = ExperimentResult(DeviceType.LAB, "lab.two.tomography", "fixture", "COMPLETED",
                              {"result": data}, {})
    assessment = assess_result(result)
    assert assessment["execution_validation"] == "PASS"
    assert assessment["issues"] == []
    assert assessment["scientific_assessment"] == "NOT_ASSESSED"
    assert result.data["fidelity"] is None


@pytest.mark.parametrize("value", (None, float("nan"), float("inf"), True, "25.03"))
def test_lab_tomography_still_requires_numeric_fit_coefficients(value):
    result = ExperimentResult(DeviceType.LAB, "lab.two.tomography", "fixture", "COMPLETED",
                              {"result": {"graph": [], "q0_lamda": 25.48, "q1_lamda": value}}, {})
    assert assess_result(result)["execution_validation"] == "INCOMPLETE"


def test_lab_pauli_accepts_actual_pauli_matrix_field():
    result = ExperimentResult(DeviceType.LAB, "lab.two.physical.pauli", "fixture", "COMPLETED",
                              {"result": {"graph": [], "pauli_matrix": {"II": 0.25, "IX": 0}}}, {})
    assert assess_result(result)["execution_validation"] == "PASS"


@pytest.mark.parametrize("matrix", ({}, {"II": float("nan")}))
def test_lab_pauli_rejects_empty_or_nonfinite_measurement_data(matrix):
    result = ExperimentResult(DeviceType.LAB, "lab.two.physical.pauli", "fixture", "COMPLETED",
                              {"result": {"graph": [], "pauli_matrix": matrix}}, {})
    assert assess_result(result)["execution_validation"] == "INCOMPLETE"


def test_catalogue_parameters_validate_offline_without_config():
    for item in list_experiments():
        parameters = parameters_for(item.key)
        assert parameters.to_wire()


def test_import_and_catalogue_do_not_import_gui_or_load_ctypes():
    root = Path(__file__).resolve().parents[1]
    script = "import sys;sys.path.insert(0,'src');import spinqnmrlink;spinqnmrlink.parameters_for('triangulum.circuit');assert not any(x in sys.modules for x in ['PyQt5','pyqtgraph','matplotlib.pyplot']);assert 'spinqnmrlink._backends.triangulum.session' not in sys.modules"
    # Preparing parameters must remain offline and independent of ctypes.
    script = (
        "import ctypes;ctypes.CDLL=lambda *a,**k: (_ for _ in ()).throw(AssertionError('loaded native library'));"
        + script
    )
    subprocess.run([sys.executable, "-c", script], cwd=root, check=True)


def test_circuit_assessment_accepts_missing_optional_measurements():
    result = ExperimentResult(
        DeviceType.TRIANGULUM,
        "triangulum.circuit",
        "fixture-task",
        "COMPLETED",
        {"probabilities": [1.0, 0.0]},
        {"parameters": {"qubits_num": 1}},
    )
    assessment = assess_result(result)
    assert assessment["execution_validation"] == "PASS"
    assert assessment["scientific_assessment"] == "NOT_ASSESSED"
    assert set(result.data) == {"probabilities"}


@pytest.mark.parametrize("qubits", (True, -1, 4, "1"))
def test_circuit_assessment_rejects_invalid_optional_qubit_counts(qubits):
    result = ExperimentResult(
        DeviceType.TRIANGULUM,
        "triangulum.circuit",
        None,
        "COMPLETED",
        {"probabilities": [1.0, 0.0], "qubits_num": qubits},
        {},
    )
    assert assess_result(result)["execution_validation"] == "INCOMPLETE"


def test_circuit_assessment_checks_dimensions_against_submitted_parameters():
    result = ExperimentResult(
        DeviceType.TRIANGULUM,
        "triangulum.circuit",
        None,
        "COMPLETED",
        {"probabilities": [1.0, 0.0]},
        {"parameters": {"qubits_num": 3}},
    )
    assert assess_result(result)["execution_validation"] == "INCOMPLETE"


@pytest.mark.parametrize("key", ("triangulum.circuit", "lab.two.rabi"))
def test_result_assessment_reports_numeric_overflow_as_incomplete(key):
    data = (
        {"probabilities": [10**400, 0], "qubits_num": 1}
        if key == "triangulum.circuit"
        else {"result": {"real": 10**400, "graph": [{"fidRe": [[0, 1]]}]}}
    )
    result = ExperimentResult(
        DeviceType.TRIANGULUM if key == "triangulum.circuit" else DeviceType.LAB,
        key, None, "COMPLETED", data, {},
    )
    assert assess_result(result)["execution_validation"] == "INCOMPLETE"
