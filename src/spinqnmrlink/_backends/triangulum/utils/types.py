# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
实验类型枚举结构体
"""
class ExperimentType():
    CIRCUIT_LAYER_EXPERIMENT = "EXP_CIRCUIT_LAYER"
    PHYSICAL_LAYER_EXPERIMENT = "EXP_PHYSICAL_LAYER"

class ExperimentState():
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
