# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Configure independent Lab and Triangulum sessions directly in Python."""

from spinqnmrlink import LabSettings, SDKSettings, SpinQNMRLink, TriangulumSettings


def create_sdk(
    lab_host, lab_account, lab_password, triangulum_host, triangulum_account, triangulum_password
):
    """Return an unconnected SDK; credentials can be strings or env:VARIABLE references."""
    return SpinQNMRLink(
        SDKSettings(
            lab=LabSettings(
                host=lab_host,
                port=8181,
                account=lab_account,
                password=lab_password,
            ),
            triangulum=TriangulumSettings(
                host=triangulum_host,
                port=55444,
                account=triangulum_account,
                password=triangulum_password,
            ),
        )
    )


def inspect_sessions(
    lab_host, lab_account, lab_password, triangulum_host, triangulum_account, triangulum_password
):
    """Inspect configured sessions offline. Call device.open() when ready to connect."""
    with create_sdk(
        lab_host,
        lab_account,
        lab_password,
        triangulum_host,
        triangulum_account,
        triangulum_password,
    ) as sdk:
        lab = sdk.device("lab")
        triangulum = sdk.device("triangulum")
        print("Lab ready:", lab.is_ready)
        print("Triangulum ready:", triangulum.is_ready)
        print("Lab experiments:", [experiment.key for experiment in lab.list_experiments()])
        print(
            "Triangulum experiments:",
            [experiment.key for experiment in triangulum.list_experiments()],
        )


if __name__ == "__main__":
    # Documentation-only credentials; these sessions remain offline.
    inspect_sessions(
        "192.0.2.20",
        "example-account",
        "example-password",
        "192.0.2.10",
        "example-account",
        "example-password",
    )
