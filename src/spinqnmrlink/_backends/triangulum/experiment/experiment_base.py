# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Private protocol parameter definitions; no network or resource ownership."""

from abc import abstractmethod
from pydantic import BaseModel, ConfigDict
from spinqnmrlink._core.experiment_core import ExperimentResultCore


class ExperimentResult(ExperimentResultCore):
    pass


class ExperimentParameter(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    @abstractmethod
    def get_parameters(self):
        raise NotImplementedError
