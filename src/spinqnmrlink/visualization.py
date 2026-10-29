# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Optional plotting. Importing the SDK never imports a GUI toolkit."""


def plot_result(result):
    """Plot only curves actually supplied by the device."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError("Install SpinQNMRLink[plot] to plot results") from None
    data = result.data or {}
    from ._core.graphs import graph_curves

    curves = graph_curves(data.get("graph", []))
    plotted = False
    for group in curves:
        if not isinstance(group, dict):
            continue
        for name, points in group.items():
            if points and all(isinstance(p, (tuple, list)) and len(p) == 2 for p in points):
                plt.plot([p[0] for p in points], [p[1] for p in points], label=name)
                plotted = True
    if not plotted:
        raise ValueError("No plottable device curves were returned")
    plt.title(result.experiment_key)
    plt.xlabel("Device chart x (units defined by the experiment)")
    plt.ylabel("Device chart y")
    plt.legend()
    plt.show()
