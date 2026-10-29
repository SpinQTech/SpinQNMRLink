"""Synthetic codec inputs only; these fixtures are not device measurements."""

import base64
import json
import struct
import zlib

import pytest

from spinqnmrlink._core.graphs import graph_curves


def test_triangulum_qcompress_graph_decodes_without_qt():
    payload = json.dumps([{"fidRe": {"x": [0, 1], "y": [2, 3]}}]).encode()
    compressed = base64.b64encode(struct.pack(">I", len(payload)) + zlib.compress(payload)).decode()
    assert graph_curves(compressed) == [{"fidRe": [[0, 2], [1, 3]]}]


def test_mismatched_chart_arrays_are_not_silently_truncated():
    with pytest.raises(ValueError, match="equal lengths"):
        graph_curves([{"fidRe": {"x": [0, 1], "y": [2]}}])


def test_nonfinite_lab_coordinates_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        graph_curves([{"fidRe": [[0, float("nan")]]}])


def test_numeric_overflow_in_chart_points_is_reported_as_invalid_data():
    with pytest.raises(ValueError, match="finite"):
        graph_curves([{"fidRe": [[0, 10**400]]}])


@pytest.mark.parametrize("declared_size", (0, 1, 10_000))
def test_compressed_charts_require_an_exact_length_header(declared_size):
    payload = json.dumps([{"fidRe": [[0, 1]]}]).encode()
    graph = base64.b64encode(struct.pack(">I", declared_size) + zlib.compress(payload)).decode()
    with pytest.raises(ValueError):
        graph_curves(graph)


def test_compressed_chart_expansion_is_bounded_even_with_a_forged_header():
    payload = json.dumps([{"fidRe": [[0, 1]] * 1000}]).encode()
    graph = base64.b64encode(struct.pack(">I", 0) + zlib.compress(payload)).decode()
    with pytest.raises(ValueError):
        graph_curves(graph, max_decoded_bytes=128)
