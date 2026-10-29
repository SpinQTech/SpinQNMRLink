# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Local task event timestamps; remote wall clocks are never used for deadlines."""

import time
from datetime import datetime, timezone


def mark_execution_started(task, *, monotonic=None, utc=None):
    if getattr(task, "execution_started_monotonic", None) is None:
        task.execution_started_monotonic = time.monotonic() if monotonic is None else monotonic
        task.execution_started_at_utc = utc or datetime.now(timezone.utc).isoformat()


def mark_execution_finished(task):
    if getattr(task, "execution_finished_monotonic", None) is None:
        task.execution_finished_monotonic = time.monotonic()
        task.execution_finished_at_utc = datetime.now(timezone.utc).isoformat()
