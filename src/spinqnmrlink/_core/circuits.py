# Copyright 2026 SpinQ Technology Co., Ltd.
# SPDX-License-Identifier: GPL-3.0-only
"""Shared circuit scheduling and display behavior."""


class CircuitBase:
    """Common gate list behavior; serialization remains package-owned."""

    def __init__(self, qubits_num: int, *, max_qubits: int) -> None:
        if qubits_num <= 0 or qubits_num > max_qubits:
            raise ValueError(
                f"Invalid qubits number, must be between 1 and {max_qubits}"
            )
        self.qubits_num = qubits_num
        self.circuit = []

    def __lshift__(self, gate):
        self.append(gate)
        return self

    def append(self, gate) -> None:
        current_timeslot = gate.timeslot
        while True:
            occupied_positions = set()
            for existing_gate in self.circuit:
                if existing_gate.timeslot != current_timeslot:
                    continue
                occupied_positions.add(existing_gate.qubitIndex)
                if existing_gate.controlQubit >= 0:
                    occupied_positions.add(existing_gate.controlQubit)
                if existing_gate.controlQubit2 >= 0:
                    occupied_positions.add(existing_gate.controlQubit2)

            positions = {gate.qubitIndex}
            if gate.controlQubit >= 0:
                positions.add(gate.controlQubit)
            if gate.controlQubit2 >= 0:
                positions.add(gate.controlQubit2)
            if positions.isdisjoint(occupied_positions):
                gate.timeslot = current_timeslot
                break
            current_timeslot += 1
        self.circuit.append(gate)

    def print_circuit(self) -> None:
        print("--------------------------------")
        gates_by_timeslot = {}
        for gate in self.circuit:
            gates_by_timeslot.setdefault(gate.timeslot, []).append(gate)
        for timeslot in sorted(gates_by_timeslot):
            gate_strings = []
            for gate in gates_by_timeslot[timeslot]:
                indexes = [gate.qubitIndex]
                if gate.controlQubit >= 0:
                    indexes.append(gate.controlQubit)
                if gate.controlQubit2 >= 0:
                    indexes.append(gate.controlQubit2)
                gate_strings.append(f"{gate.type}({','.join(map(str, indexes))})")
            print(f"TS {timeslot}: {' '.join(gate_strings)}")
        print("--------------------------------")
