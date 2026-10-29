# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Lifecycle adapter for protocol-v2 three-qubit task parameter models."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Mapping, Optional, Union

from ..connection.events import ChartKey
from .experiment_base import Experiment, ExperimentResult
from .three_qubit_models import (
    THREE_QUBIT_PARAMETER_TYPES,
    serialize_three_qubit_extra,
)
from ..utils.types import ExperimentState


class ThreeQubitExperimentResult(ExperimentResult):
    """Preserve experiment-specific data without guessing its future schema."""

    def __init__(self) -> None:
        self.data_updates = []
        self.graph = []
        self.chart_streams = []
        self.final_data = None

    def append_graph(self, lines: Dict[str, Any]) -> None:
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        return {
            "data_updates": list(self.data_updates),
            "graph": list(self.graph),
            "chart_streams": list(self.chart_streams),
            "final_data": self.final_data,
        }


class ThreeQubitExperiment(Experiment):
    """Connect Appendix-A parameters to the existing Experiment lifecycle."""

    def __init__(
        self,
        parameters: Any,
        *,
        task_id: Optional[str] = None,
        name: str = "",
        custom_awg_files: Optional[
            Mapping[str, Union[str, Mapping[str, Any]]]
        ] = None,
    ) -> None:
        if not isinstance(parameters, THREE_QUBIT_PARAMETER_TYPES):
            raise TypeError("parameters must be a public three-qubit parameter model")
        super().__init__(parameters)
        if task_id is not None:
            if not isinstance(task_id, str) or not task_id:
                raise ValueError("task_id must be a non-empty string")
            self.id = task_id
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        self.experiment_type = parameters.TASK_TYPE
        self.name = name or f"{self.experiment_type}-{self.id[:8]}"
        self.extra = (
            serialize_three_qubit_extra(custom_awg_files)
            if custom_awg_files is not None
            else None
        )
        self.result = ThreeQubitExperimentResult()
        self._chart_lines: Dict[ChartKey, list] = {}

    @staticmethod
    def _chart_key(data: Dict[str, Any]) -> ChartKey:
        return ChartKey(
            task_id=str(data.get("taskId", "")),
            group=str(data.get("group", "")),
            chart_name=str(data.get("chart_name", "")),
            path=data.get("path") or None,
            qubit=data.get("qubit") or None,
            step=data.get("step") or None,
        )

    @staticmethod
    def _matches_chart_boundary(key: ChartKey, boundary: ChartKey) -> bool:
        key_values = (
            key.task_id,
            key.group or None,
            key.chart_name or None,
            key.path,
            key.qubit,
            key.step,
        )
        boundary_values = (
            boundary.task_id,
            boundary.group or None,
            boundary.chart_name or None,
            boundary.path,
            boundary.qubit,
            boundary.step,
        )
        return key_values[0] == boundary_values[0] and all(
            expected is None or actual == expected
            for actual, expected in zip(key_values[1:], boundary_values[1:])
        )

    def get_experiment_parameter(self) -> Dict[str, Any]:
        task = {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "type": self.experiment_type,
            "params": json.dumps(
                self.parameters.to_dict(),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
        if self.extra is not None:
            task["extra"] = self.extra
        return task

    def _matches(self, data: Dict[str, Any]) -> bool:
        task_id = data.get("taskId")
        return task_id is None or task_id == self.id

    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        if data.get("code") != 0:
            raise RuntimeError(f"Experiment addition failed: {data}")
        task_id = data.get("taskId")
        if task_id:
            self.id = str(task_id)

    def handle_exp_started(self, data: Dict[str, Any]) -> None:
        if not self._matches(data):
            return
        self.state = ExperimentState.RUNNING
        queue = data.get("queue") or []
        matching = next(
            (item for item in queue if item.get("id") == self.id),
            queue[0] if queue else {},
        )
        self.started_at = matching.get("startTime", int(time.time() * 1000))
        if matching.get("name"):
            self.name = matching["name"]

    def handle_exp_step_changed(self, data: Dict[str, Any]) -> None:
        if self._matches(data):
            payload = data.get("data") or {}
            self.step = payload.get("step", self.step)

    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        if self._matches(data):
            self.result.data_updates.append(data.get("data"))

    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        if self._matches(data):
            boundary = self._chart_key(data)
            self._chart_lines = {
                key: points
                for key, points in self._chart_lines.items()
                if not self._matches_chart_boundary(key, boundary)
            }

    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        if not self._matches(data):
            return
        key = self._chart_key(data)
        self._chart_lines.setdefault(key, []).extend(data.get("points", []))

    def handle_exp_chart_data_updated_finished(self, data: Dict[str, Any]) -> None:
        if not self._matches(data):
            return
        boundary = self._chart_key(data)
        completed = [
            (key, points)
            for key, points in self._chart_lines.items()
            if self._matches_chart_boundary(key, boundary)
        ]
        if not completed:
            return

        legacy_graph: Dict[str, Any] = {}
        for key, points in completed:
            point_copy = [list(point) for point in points]
            self.result.chart_streams.append(
                {
                    "taskId": key.task_id,
                    "group": key.group,
                    "chart_name": key.chart_name,
                    "path": key.path,
                    "qubit": key.qubit,
                    "step": key.step,
                    "points": point_copy,
                }
            )
            if key.chart_name in legacy_graph:
                self.result.append_graph({key.chart_name: point_copy})
            else:
                legacy_graph[key.chart_name] = point_copy
        if legacy_graph:
            self.result.append_graph(legacy_graph)

        for key, _ in completed:
            self._chart_lines.pop(key, None)

    def handle_exp_terminated(self, data: Dict[str, Any]) -> None:
        if self._matches(data):
            self.completed_at = int(time.time() * 1000)
            self.state = ExperimentState.TERMINATED

    def handle_exp_removed(self, data: Dict[str, Any]) -> None:
        if self._matches(data):
            self.completed_at = int(time.time() * 1000)
            if self.state not in (
                ExperimentState.COMPLETED,
                ExperimentState.TERMINATED,
                ExperimentState.TIMEOUT,
            ):
                self.state = ExperimentState.TERMINATED

    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        if not self._matches(data):
            return
        self.completed_at = int(time.time() * 1000)
        payload = data.get("data")
        self.result.final_data = payload
        if isinstance(payload, dict) and payload.get("isTerminated") is True:
            self.state = ExperimentState.TERMINATED
        else:
            self.state = ExperimentState.COMPLETED

    def get_status(self) -> str:
        return self.state

    def get_result(self) -> Dict[str, Any]:
        value = self.get_experiment_parameter()
        value.update(
            {
                "startTime": self.started_at,
                "endTime": self.completed_at,
                "state": self.state,
                "result": self.result.get_result(),
            }
        )
        return value


__all__ = ["ThreeQubitExperiment", "ThreeQubitExperimentResult"]
