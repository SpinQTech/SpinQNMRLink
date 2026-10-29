# Copyright 2025 SpinQ Technology Co., Ltd.
#
# SPDX-License-Identifier: GPL-3.0-only

"""
Quantum Gate Classes
"""
import json
from spinqnmrlink._backends.lab.utils.pulse import Pulse
from pydantic import Field
from typing import List, ClassVar
from spinqnmrlink._core.gates import GateModel

class Gate(GateModel):
    """
    Quantum gate class, representing quantum gates that can be added to a quantum circuit
    """
    allowed_types: ClassVar[List[str]] = ['H','I','X','Y','Z','X90','Y90','Z90','Rx','Ry','Rz','T','Td','S','Sd','CNOT','CZ']

class CustomGate(Gate):
    customType: str = Field(default='custom', description="The type of the custom gate")
    gateJson: str = Field(default="", description="The json of the custom gate")
    pulses: List[Pulse] = Field(default=[], description="The pulses of the custom gate")

    def __init__(self, customType: str, gateJson: str = "", pulses: List[Pulse] = [], **kwargs):
        super().__init__(**kwargs)
        self.customType = customType
        if gateJson != "" and self._validate_json(gateJson):
            self.gateJson = gateJson
            self.pulses = self._parse_gate_json(gateJson)
        elif pulses != []:
            self.pulses = pulses

    def _validate_json(self, gateJson: str) -> bool:
        """
        Validate the gate json
        """
        pulse_dict = json.loads(gateJson)
        if "pulse" in pulse_dict:
            if "channel1_pulse" in pulse_dict["pulse"] and "channel2_pulse" in pulse_dict["pulse"]:
                ch1_pulse = pulse_dict["pulse"]["channel1_pulse"]
                ch2_pulse = pulse_dict["pulse"]["channel2_pulse"]
                for i,p in enumerate(ch1_pulse):
                    for key in p:
                        if key not in ["width", "amplitude", "phase", "detuning"]:
                            raise ValueError(f"Invalid gate json at channel1_pulse[{i}], \"{key}\" is not in the channel1_pulse, but got {p}")
                        if p["width"] < 0 or p["width"] > 20000000:
                            raise ValueError(f"Invalid gate json at channel1_pulse[{i}], width must be between 0 and 20000000, but got {p['width']}")
                        if p["amplitude"] < 0 or p["amplitude"] > 100:
                            raise ValueError(f"Invalid gate json at channel1_pulse[{i}], amplitude must be between 0 and 100, but got {p['amplitude']}")
                        if p["detuning"] < -10000 or p["detuning"] > 10000:
                            raise ValueError(f"Invalid gate json at channel1_pulse[{i}], detuning must be between -10000 and 10000, but got {p['detuning']}")
                for i,p in enumerate(ch2_pulse):
                    for key in p:
                        if key not in ["width", "amplitude", "phase", "detuning"]:
                            raise ValueError(f"Invalid gate json at channel2_pulse[{i}], \"{key}\" is not in the channel2_pulse")
                        if p["width"] < 0 or p["width"] > 20000000:
                            raise ValueError(f"Invalid gate json at channel2_pulse[{i}], width must be between 0 and 20000000, but got {p['width']}")
                        if p["amplitude"] < 0 or p["amplitude"] > 100:
                            raise ValueError(f"Invalid gate json at channel2_pulse[{i}], amplitude must be between 0 and 100, but got {p['amplitude']}")
                        if p["detuning"] < -10000 or p["detuning"] > 10000:
                            raise ValueError(f"Invalid gate json at channel2_pulse[{i}], detuning must be between -10000 and 10000, but got {p['detuning']}")
                if len(ch1_pulse) != len(ch2_pulse):
                    raise ValueError("Invalid gate json, channel1_pulse and channel2_pulse must have the same length")
                return True
            else:
                raise ValueError("Invalid gate json, pulse dictionary must be in the gate json")
        else:
            raise ValueError(f"Invalid gate json, pulse dictionary must be in the gate json, but got {gateJson}")

    def _parse_gate_json(self, gateJson: str) -> List[Pulse]:
        """
        Parse the gate json
        """
        gate_dict = json.loads(gateJson)
        pulse = []
        if "pulse" in gate_dict:
            pulse_dict = gate_dict["pulse"]
        else:
            raise ValueError("Invalid gate json, pulse dictionary must be in the gate json")

        if "channel1_pulse" in pulse_dict:
            for p in pulse_dict["channel1_pulse"]:
                pulse.append(Pulse(path=0, phase=p["phase"], amplitude=p["amplitude"], width=p["width"]))
        if "channel2_pulse" in pulse_dict:
            for p in pulse_dict["channel2_pulse"]:
                pulse.append(Pulse(path=1, phase=p["phase"], amplitude=p["amplitude"], width=p["width"]))
        return pulse

    def _gate_json_to_dict(self, pulses: List[Pulse]) -> dict:
        """
        Convert gate json to dictionary
        """
        channel1_pulse = []
        channel2_pulse = []
        for p in pulses:
            if p.path == 0:
                channel1_pulse.append(p.to_dict())
            else:
                channel2_pulse.append(p.to_dict())
        return {
            "channel1_pulse": channel1_pulse,
            "channel2_pulse": channel2_pulse
        }

    def to_json(self) -> str:
        if self.gateJson != "":
            return self.gateJson
        else:
            pulses = self._gate_json_to_dict(self.pulses)
            json_dict = {
                "description": {
                    "DATE": "",
                    "FIDELITY": "",
                    "OWNER": "",
                    "SLICES": "",
                    "TITLE": "",
                    "TOTALPULSEWIDTH": ""
                },
                "pulse": pulses
            }
            return json.dumps(json_dict, ensure_ascii=False)

    def to_dict(self) -> dict:
        gate_dict = super().to_dict()
        gate_dict['customType'] = self.customType
        return gate_dict
