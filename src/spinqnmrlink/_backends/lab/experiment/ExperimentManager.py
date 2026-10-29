# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Experiment manager.

Responsible for registering experiments, managing their execution,
waiting for completion, and retrieving results.
"""

from __future__ import annotations

from typing import Type
import importlib
import time
from spinqnmrlink._core.experiment_core import ExperimentManagerCore

from ..utils import LoggerManager
from .experiment_base import Experiment, ExperimentParameter, ExperimentState
from ..utils.types import ExperimentType

# Create logger
logger = LoggerManager.get_logger(name='experiment_manager')

TERMINAL_EXPERIMENT_STATES = frozenset((
    ExperimentState.COMPLETED,
    ExperimentState.TERMINATED,
    ExperimentState.TIMEOUT,
    # Local processing failure, distinct from server task states.
    ExperimentState.FAILED,
))

class ExperimentManager(ExperimentManagerCore):
    logger = logger
    terminal_states = TERMINAL_EXPERIMENT_STATES
    """Manager for experiment lifecycle and dispatch."""
    def __init__(self):
        self.EXPERIMENT_TYPE_MAP = {
            ExperimentType.NMR_PHENOMENON_AND_SIGNAL: ('spinqnmrlink._backends.lab.experiment.exp_pulse', 'ExpPulse', 'ExpPulseParameters'),
            ExperimentType.RABI_OSCILLATIONS: ('spinqnmrlink._backends.lab.experiment.exp_rabi', 'ExpRabi', 'ExpRabiParameters'),
            ExperimentType.QUANTUM_BIT: ('spinqnmrlink._backends.lab.experiment.exp_qubit', 'ExpQubit', 'ExpQubitParameters'),
            ExperimentType.QUANTUM_DECOHERENCE_T1: ('spinqnmrlink._backends.lab.experiment.exp_decot1', 'ExpT1', 'ExpT1Parameters'),
            ExperimentType.QUANTUM_DECOHERENCE_T2: ('spinqnmrlink._backends.lab.experiment.exp_decot2', 'ExpT2', 'ExpT2Parameters'),
            ExperimentType.QUANTUM_CONTROL: ('spinqnmrlink._backends.lab.experiment.exp_qcontrol', 'ExpQControl', 'ExpQControlParameters'),
            ExperimentType.QUANTUM_SYSTEM_INITIALIZATION: ('spinqnmrlink._backends.lab.experiment.exp_sysinit', 'ExpSysInit', 'ExpSysInitParameters'),
            ExperimentType.QUANTUM_GATES_AND_CIRCUIT: ('spinqnmrlink._backends.lab.experiment.exp_qcircuit', 'ExpQCircuit', 'ExpQCircuitParameters'),
            ExperimentType.QUANTUM_STATE_TOMOGRAPHY: ('spinqnmrlink._backends.lab.experiment.exp_qrefactor', 'ExpQRefactor', 'ExpQRefactorParameters'),
            ExperimentType.QUANTUM_COMPUTING_TASK: ('spinqnmrlink._backends.lab.experiment.exp_qtask', 'ExpQTask', 'ExpQTaskParameters'),
            ExperimentType.QUANTUM_ALGORITHM: ('spinqnmrlink._backends.lab.experiment.exp_qalgorithm', 'ExpQAlgorithm', 'ExpQAlgorithmParameters'),
            ExperimentType.SPIN_ECHO: ('spinqnmrlink._backends.lab.experiment.exp_spinecho', 'ExpSpinecho', 'ExpSpinechoParameters'),
            ExperimentType.DYNAMIC_DECOUPLING: ('spinqnmrlink._backends.lab.experiment.exp_dydeco', 'ExpDydeco', 'ExpDydecoParameters'),
            ExperimentType.SHAPE_PULSE: ('spinqnmrlink._backends.lab.experiment.exp_shapePulse', 'ExpShapePulse', 'ExpShapePulseParameters'),
            ExperimentType.NUMERICAL_OPTIMIZATION_PULSE: ('spinqnmrlink._backends.lab.experiment.exp_npopti', 'ExpNpopti', 'ExpNpoptiParameters'),
            ExperimentType.PHYSICAL_LAYER_EXPERIMENT: ('spinqnmrlink._backends.lab.experiment.exp_layer_physical', 'ExpLayerPhysical', 'ExpLayerPhysicalParameters'),
            ExperimentType.CIRCUIT_LAYER_EXPERIMENT: ('spinqnmrlink._backends.lab.experiment.exp_layer_circuit', 'ExpLayerCircuit', 'ExpLayerCircuitParameters')
        }
        self.current_experiment = None
        self.current_experiment_params = None

    def _get_experiment_class(self, experiment_type: ExperimentType) -> tuple[Type[Experiment], Type[ExperimentParameter]]:
        """
        Get the experiment and parameter classes corresponding to the type.

        Args:
            experiment_type: Experiment type.

        Returns:
            Tuple of (experiment class, parameter class).

        Raises:
            ValueError: If the experiment type is not supported.
        """
        if experiment_type not in self.EXPERIMENT_TYPE_MAP:
            raise ValueError(f"Unknown experiment type: {experiment_type}")

        module_path, class_name, parameter_class_name = self.EXPERIMENT_TYPE_MAP[experiment_type]
        try:
            # Dynamically import experiment class
            module = importlib.import_module(module_path)
            experiment_class = getattr(module, class_name)
            parameter_class = getattr(module, parameter_class_name)
            return experiment_class, parameter_class
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import experiment class: {e}")
            raise ValueError(f"Cannot load experiment type: {experiment_type}")

    def register_experiment(self, experiment_type: ExperimentType, handler_map: dict) -> tuple[Experiment, ExperimentParameter]:
        """
        Register an experiment of the given type.

        Args:
            experiment_type: Experiment type.
        """
        if self.current_experiment is not None:
            raise ValueError("Cannot register experiment more than once")

        experiment_class, parameter_class = self._get_experiment_class(experiment_type)

        self.current_experiment_params = parameter_class()
        self.current_experiment = experiment_class(self.current_experiment_params)
        self.current_experiment.register_handler(handler_map)
        return self.current_experiment, self.current_experiment_params

    def register_experiment_instance(
        self,
        experiment: Experiment,
        parameters,
        handler_map: dict,
    ):
        """Register a pre-built experiment while preserving manager lifecycle rules."""
        if self.current_experiment is not None:
            raise ValueError("Cannot register experiment more than once")
        if not isinstance(experiment, Experiment):
            raise TypeError("experiment must be an Experiment instance")
        self.current_experiment = experiment
        self.current_experiment_params = parameters
        experiment.register_handler(handler_map)
        return experiment, parameters

    def deregister_experiment(self):
        """
        Deregister the current experiment.
        """
        if self.current_experiment is not None or self.current_experiment_params is not None:
            self.current_experiment = None
            self.current_experiment_params = None
        else:
            logger.warning("No experiment registered")

    def get_experiment_status(self):
        """Return the current experiment state for the public SDK facade."""
        if self.current_experiment is None:
            logger.error("No experiment registered")
            return None
        return self.current_experiment.get_status()
