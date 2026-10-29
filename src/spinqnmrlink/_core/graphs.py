# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Headless decoding of Lab curves and Triangulum Qt-compressed graph data."""
import base64
import json
import math
import struct
import zlib

MAX_DECODED_CHART_BYTES = 64 * 1024 * 1024


def graph_curves(graph, *, max_decoded_bytes=MAX_DECODED_CHART_BYTES):
    """Return real chart points; reject mismatches rather than truncating measurements."""
    if isinstance(graph, str):
        if type(max_decoded_bytes) is not int or max_decoded_bytes <= 0:
            raise ValueError("Decoded chart size limit must be a positive integer")
        try:
            compressed = base64.b64decode("".join(graph.split()), validate=True)
            if len(compressed) <= 4:
                raise ValueError("Compressed chart header is missing")
            expected_size = struct.unpack(">I", compressed[:4])[0]
            if expected_size > max_decoded_bytes:
                raise ValueError("Compressed chart exceeds the decoded size limit")
            decoder = zlib.decompressobj()
            payload = decoder.decompress(compressed[4:], max_decoded_bytes + 1)
            if len(payload) > max_decoded_bytes or decoder.unconsumed_tail:
                raise ValueError("Compressed chart exceeds the decoded size limit")
            if not decoder.eof or decoder.unused_data:
                raise ValueError("Compressed chart stream is truncated or has trailing data")
            if len(payload) != expected_size:
                raise ValueError("Compressed chart size does not match its header")
            graph = json.loads(payload.decode("utf-8"))
        except (ValueError, RecursionError, zlib.error, UnicodeDecodeError) as exc:
            raise ValueError("Invalid compressed chart data") from exc
    if not isinstance(graph, list):
        raise ValueError("Chart data must contain a list of curve groups")
    groups = []
    for group in graph:
        if not isinstance(group, dict):
            raise ValueError("Chart group must be an object")
        converted = {}
        for name, points in group.items():
            if isinstance(points, dict):
                x, y = points.get("x"), points.get("y")
                if not isinstance(x, list) or not isinstance(y, list) or len(x) != len(y):
                    raise ValueError("Chart x/y arrays must have equal lengths")
                points = [list(pair) for pair in zip(x, y)]
            if not isinstance(points, list):
                raise ValueError("Chart points must be a list")
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    raise ValueError("Chart points must contain exactly x and y")
                try:
                    valid = all(
                        not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)
                        for v in point
                    )
                except OverflowError:
                    valid = False
                if not valid:
                    raise ValueError("Chart coordinates must be finite numbers")
            converted[name] = points
        groups.append(converted)
    return groups
