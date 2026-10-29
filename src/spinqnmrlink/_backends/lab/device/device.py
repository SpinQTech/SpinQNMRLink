# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Device module.

Responsible for storing and managing device parameters and providing
a unified data access interface.
"""

from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass
import json
from spinqnmrlink._backends.lab.utils import LoggerManager

# Create logger
logger = LoggerManager.get_logger(name='device')

@dataclass
class DeviceStatus:
    """Data class representing device status."""
    connected: bool = False
    lock_state: bool = False
    temperature: float = 0.0

@dataclass
class LockData:
    """Data class representing lock field information."""
    frequency: float = 0.0
    frequency0: float = 0.0  # Hydrogen frequency
    frequency1: float = 0.0  # Phosphorus frequency
    frequency2: float = 0.0  # Lock field frequency
    has_peak: bool = False
    mt: float = 0.0
    ppm: float = 0.0
    voltage: float = 0.0

class DeviceParams:
    """Device parameter wrapper."""
    def __init__(self, params: Dict[str, Any] = None):
        self._params = params or {}

    @property
    def current_shimming(self) -> float:
        """Get current shimming value."""
        return self._params.get("currentShimming", 0.0)

    @property
    def lock_param(self) -> Dict[str, Any]:
        """Get lock-field parameters."""
        return self._params.get("lockParam", {})

    @property
    def pps_param(self) -> Dict[str, Any]:
        """Get PPS parameters."""
        return self._params.get("ppsParam", {})

    @property
    def pulse_param(self) -> Dict[str, Any]:
        """Get pulse parameters."""
        return self._params.get("pulseParam", {})

    @property
    def sample_param(self) -> Dict[str, Any]:
        """Get sampling parameters."""
        return self._params.get("sampleParam", {})

    @property
    def shimming_param(self) -> Dict[str, Any]:
        """Get shimming parameters."""
        return self._params.get("shimmingParam", {})

    def get_param(self, param_path: str, default=None) -> Any:
        """
        Get a nested parameter value via a dotted path.

        Args:
            param_path: Parameter path, e.g. "pulseParam.f_Q1".
            default: Default value to return if the path does not exist.

        Returns:
            The parameter value or default.
        """
        parts = param_path.split('.')
        current = self._params

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to a dictionary."""
        return self._params

    def __str__(self) -> str:
        """String representation of device parameters."""
        return json.dumps(self._params, ensure_ascii=False, indent=2)

class Device:
    """
    Device class.

    Responsible for storing device parameters and providing a unified
    data access interface.
    """
    def __init__(self, device_id: str, device_type: str, device_params: Dict[str, Any] = None):
        """
        Initialize a device instance.

        Args:
            device_id: Device ID.
            device_type: Device type.
            device_params: Dictionary of initial device parameters.
        """
        self.device_id = device_id
        self.device_type = device_type
        self._params = DeviceParams(device_params)
        self._lock_data = LockData()
        self._status = DeviceStatus()
        self._observers = []

    def register_observer(self, callback: Callable[['Device', str], None]) -> None:
        """
        Register an observer for data updates.

        Args:
            callback: Callback invoked when device data is updated, receiving
                      the device instance and the update type.
        """
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback: Callable[['Device', str], None]) -> None:
        """
        Unregister a previously registered data update observer.

        Args:
            callback: Callback to unregister.
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self, update_type: str) -> None:
        """
        Notify all observers that device data has been updated.

        Args:
            update_type: Update type, e.g. 'params', 'lock_data', 'status'.
        """
        for observer in self._observers:
            observer(self, update_type)

    def set_device_params(self, device_params: Dict[str, Any]) -> None:
        """
        Set device parameters.

        Args:
            device_params: Dictionary of device parameters.
        """
        self._params = DeviceParams(device_params)
        logger.debug("Device parameters updated")
        self._notify_observers('params')

    def set_lock_data_post(self, lock_data_post: Dict[str, Any]) -> None:
        """
        Set lock-field data.

        Args:
            lock_data_post: Dictionary containing lock-field data.
        """
        if "locking" in lock_data_post:
            locking = lock_data_post["locking"]
            self._lock_data = LockData(
                frequency=locking.get("frequency", 0.0),
                frequency0=locking.get("frequency0", 0.0),
                frequency1=locking.get("frequency1", 0.0),
                frequency2=locking.get("frequency2", 0.0),
                has_peak=locking.get("hasPeak", False),
                mt=locking.get("mt", 0.0),
                ppm=locking.get("ppm", 0.0),
                voltage=locking.get("voltage", 0.0)
            )
        logger.debug("Lock-field data updated")
        self._notify_observers('lock_data')

    def set_temp_data_post(self, temp_data_post: Dict[str, Any]) -> None:
        """
        Set device status data.

        Args:
            temp_data_post: Dictionary containing device status data.
        """
        self._status = DeviceStatus(
            connected=temp_data_post.get("connected", False),
            lock_state=temp_data_post.get("lockState", False),
            temperature=temp_data_post.get("temperature", 0.0)
        )
        logger.debug(
            f"Device status updated: connected={self._status.connected}, "
            f"lock_state={self._status.lock_state}, temperature={self._status.temperature}"
        )
        self._notify_observers('status')

    # Methods for retrieving device information

    @property
    def params(self) -> DeviceParams:
        """Get the device parameter object."""
        return self._params

    @property
    def lock_data(self) -> LockData:
        """Get the lock-field data object."""
        return self._lock_data

    @property
    def status(self) -> DeviceStatus:
        """Get the device status object."""
        return self._status

    def get_frequencies(self) -> Dict[str, float]:
        """
        Get device frequency information.

        Returns:
            A dictionary containing hydrogen, phosphorus, and lock-field frequencies.
        """
        return {
            "H": self._lock_data.frequency0,
            "P": self._lock_data.frequency1,
            "lock": self._lock_data.frequency2
        }

    def get_pulse_amplitudes(self) -> Dict[str, float]:
        """
        Get pulse amplitude parameters.

        Returns:
            A dictionary containing amplitudes for each channel.
        """
        pulse_param = self._params.pulse_param
        return {
            "am_Lock": float(pulse_param.get("am_Lock", 0)),
            "am_H": float(pulse_param.get("am_Q1", 0)),
            "am_P": float(pulse_param.get("am_Q2", 0))
        }

    def get_pulse_phases(self) -> Dict[str, float]:
        """
        Get pulse phase parameters.

        Returns:
            A dictionary containing phases for each channel.
        """
        pulse_param = self._params.pulse_param
        return {
            "phaseQ0": float(pulse_param.get("phaseQ1_0", 0)),
            "phaseQ1": float(pulse_param.get("phaseQ2_0", 0))
        }

    def get_qubit_params(self) -> Dict[str, Dict[str, float]]:
        """
        Get qubit-related parameters.

        Returns:
            A dictionary containing parameters for each qubit.
        """
        pps_param = self._params.pps_param
        return {
            "Q0": {
                "lamda1": float(pps_param.get("Q1_lamda1", 0)),
                "lamda2": float(pps_param.get("Q1_lamda2", 0)),
                "noise": float(pps_param.get("Q1_noise", 0)),
                "ratio": float(pps_param.get("Q1_ratio", 0)),
                "amplitude": float(pps_param.get("am_Q1", 0)),
                "width": float(pps_param.get("width_Q1", 0))
            },
            "Q1": {
                "lamda1": float(pps_param.get("Q2_lamda1", 0)),
                "lamda2": float(pps_param.get("Q2_lamda2", 0)),
                "noise": float(pps_param.get("Q2_noise", 0)),
                "ratio": float(pps_param.get("Q2_ratio", 0)),
                "amplitude": float(pps_param.get("am_Q2", 0)),
                "width": float(pps_param.get("width_Q2", 0))
            }
        }

    def get_shimming_values(self) -> Dict[str, float]:
        """
        Get shimming values.

        Returns:
            A dictionary containing shimming values for each channel.
        """
        shimming_param = self._params.shimming_param
        result = {}
        for i in range(14):  # Shimming channels 0–13
            key = f"path{i}"
            if key in shimming_param:
                result[key] = float(shimming_param[key])
        return result

    def is_connected(self) -> bool:
        """
        Check whether the device is currently connected.

        Returns:
            Device connection status.
        """
        return self._status.connected

    def is_locked(self) -> bool:
        """
        Check whether the device is currently lock-field engaged.

        Returns:
            Device lock-field status.
        """
        return self._status.lock_state

    def get_temperature(self) -> float:
        """
        Get device temperature.

        Returns:
            Device temperature.
        """
        return self._status.temperature

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert all device information to a dictionary.

        Returns:
            A dictionary containing all device information.
        """
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "params": self._params.to_dict(),
            "lock_data": {
                "frequency": self._lock_data.frequency,
                "frequency0": self._lock_data.frequency0,
                "frequency1": self._lock_data.frequency1,
                "frequency2": self._lock_data.frequency2,
                "has_peak": self._lock_data.has_peak,
                "mt": self._lock_data.mt,
                "ppm": self._lock_data.ppm,
                "voltage": self._lock_data.voltage
            },
            "status": {
                "connected": self._status.connected,
                "lock_state": self._status.lock_state,
                "temperature": self._status.temperature
            }
        }

    def to_json(self) -> str:
        """
        Convert all device information to a JSON string.

        Returns:
            JSON string representation of the device information.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        """String representation of the device."""
        return f"Device(id={self.device_id}, type={self.device_type}, connected={self._status.connected}, locked={self._status.lock_state}, temp={self._status.temperature}°C)"
