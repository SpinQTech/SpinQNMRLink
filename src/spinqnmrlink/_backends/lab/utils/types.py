# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Experiment-related type definitions.
"""
from enum import Enum, IntEnum


class ConnectionState(Enum):
    """Authoritative SDK connection/session lifecycle state."""

    DISCONNECTED = "DISCONNECTED"
    CONNECTED = "CONNECTED"
    AUTHENTICATED = "AUTHENTICATED"
    READY = "READY"


class QubitMode(IntEnum):
    """Qubit business domain defined by communication protocol v2.0."""

    TWO = 0
    THREE = 1


class MachineType():
    # Message type definitions
    MSG_REQ_USER_LOGIN = "c_user_login_req"  # Login request
    MSG_RES_USER_LOGIN = "s_user_login_res"  # Login response
    MSG_REQ_USER_LOGOUT = "c_user_logout_req"  # Logout request
    MSG_RES_USER_LOGOUT = "s_user_logout_res"  # Logout response

    MSG_RES_HEARTBEAT = "heartbeat_res"  # Heartbeat response
    MSG_POST_QUBIT_MODE_CHANGED = "s_post_qubit_mode_changed"  # Authoritative mode changed

    # Experiment message type definitions
    MSG_REQ_ADD_EXP_TASK_REQ = "c_add_exp_task_req"  # Experiment execution request
    MSG_RES_ADD_EXP_TASK_RES = "s_add_exp_task_res"  # Experiment execution response
    MSG_REQ_TERMINATE_EXP_TASK_REQ = "c_terminate_exp_task_req"  # Termination request
    MSG_RES_TERMINATE_EXP_TASK_RES = "s_terminate_exp_task_res"  # Termination response
    # Backward-compatible alias used by existing experiment classes.
    MSG_POST_EXP_TERMINATED = MSG_RES_TERMINATE_EXP_TASK_RES
    MSG_POST_EXP_REMOVED = "s_post_exp_removed"  # Experiment removed
    MSG_POST_EXP_STARTED = "s_post_exp_started"  # Experiment started
    MSG_POST_EXP_STEP_CHANGED = "s_post_exp_step_changed"  # Experiment step changed
    MSG_POST_EXP_DATA_UPDATED = "s_post_exp_data_updated"  # Experiment data updated
    MSG_POST_EXP_CHART_UPDATED_STARTED = "s_post_exp_chart_updated_started"  # Experiment chart update started
    MSG_POST_EXP_CHART_UPDATED = "s_post_exp_chart_updated"  # Experiment chart updated
    MSG_POST_EXP_CHART_UPDATED_FINISHED = "s_post_exp_chart_updated_finished"  # Experiment chart update finished
    MSG_POST_EXP_FINISHED = "s_post_exp_finished"  # Experiment task finished

    # Device-initiated messages
    MSG_POST_PARAM = "s_post_device_param"  # Device parameters
    MSG_POST_LOCK_DATA = "s_post_lock_data"  # Device lock data updated
    MSG_POST_INFO = "s_post_device_info"  # Device information
    MSG_POST_SAMPLE_CALIBRATION = "s_post_sample_calibration_data"  # Sample calibration
    MSG_POST_EXP_QUEUE_UPDATE = "s_post_exp_queue_update"  # Experiment queue updated

class ExperimentType():
    NMR_PHENOMENON_AND_SIGNAL = "EXP_PULSE"
    RABI_OSCILLATIONS = "EXP_RABI"
    QUANTUM_BIT = "EXP_QUBIT"
    QUANTUM_DECOHERENCE_T1 = "EXP_T1"
    QUANTUM_DECOHERENCE_T2 = "EXP_T2"
    QUANTUM_CONTROL = "EXP_QCONTROL"
    QUANTUM_SYSTEM_INITIALIZATION = "EXP_PSTATE"
    QUANTUM_GATES_AND_CIRCUIT = "EXP_QCIRCUIT"
    QUANTUM_STATE_TOMOGRAPHY = "EXP_QREFACTOR"
    QUANTUM_COMPUTING_TASK = "EXP_QALGORITHM"

    QUANTUM_ALGORITHM = "EXP_QALGORITHMS"
    INTRODUCTION_TO_QUANTUM_COMPUTING = "EXP_ALGORITHM_BASIC"
    DEUTSCH_ALGORITHM = "EXP_DEUTSCH"
    BERNSTEIN_VARIRANI_ALGORITHM = "EXP_BERNSTEIN"
    GROVER_ALGORITHM = "EXP_GROVER"
    QFT_ALGORITHM = "EXP_QFT"
    HHL_ALGORITHM = "EXP_HHL"
    VQE_ALGORITHM = "EXP_VQE"
    QAOA_ALGORITHM = "EXP_QAOA"

    SPIN_ECHO = "EXP_SPINECHO"
    DYNAMIC_DECOUPLING = "EXP_DYDECO"
    SHAPE_PULSE = "EXP_SHAPEPULSE"
    NUMERICAL_OPTIMIZATION_PULSE = "EXP_NPOPTI"

    PHYSICAL_LAYER_EXPERIMENT = "EXP_LAYER_PHYSICAL"
    CIRCUIT_LAYER_EXPERIMENT = "EXP_LAYER_CIRCUIT"
    CIRCUIT_LAYER_PULSE_EXPERIMENT = "EXP_LAYER_CIRCUIT_PULSE"
    CIRCUIT_LAYER_CIRCUIT_EXPERIMENT = "EXP_LAYER_CIRCUIT_CIRCUIT"
    MIXING_CIRCUIT_EXPERIMENT = "EXP_MIXING_CIRCUIT"

class ExperimentState():
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    TIMEOUT = "TIMEOUT"
    # A local processing-failure state,
    # not one of the five authoritative task states defined by protocol v2.0.
    FAILED = "FAILED"
