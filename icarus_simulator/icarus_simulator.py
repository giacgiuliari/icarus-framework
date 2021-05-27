#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Main interface of the library. Every time an experiment is run, an icarusSimulator object must be created.
The constructor takes a list of phases to run sequentially. This class manages the intermediate and final results,
saving everything with passed property names, and correctly naming the file dumps based on phase dependencies.
"""
from typing import List, Any, Tuple, Set

from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.structure_definitions import PropertyDict, Pname, DependencyDict


class IcarusSimulator:
    def __init__(self, phases: List[BasePhase], results_directory: str):
        self.phases = phases
        self.basedir = results_directory
        self.properties: PropertyDict = {}
        self.dependencies: DependencyDict = {}

    def get_property(self, property_name: str):
        return self.properties[property_name]  # Raises with wrong property name

    def compute_simulation(self):
        # Execute phases sequentially
        for phase in self.phases:
            # Get all necessary input data for the current phase
            input_properties, output_properties = (
                phase.input_properties,
                phase.output_properties,
            )
            phase_name, phase_descr = phase.name, phase.description
            input_values = self._get_input_values(input_properties)

            # Update the phase dependency dictionary and get the filename
            previous = self._update_dependencies(
                output_properties, input_properties, phase_descr
            )
            phase_fname = self._get_phase_fname(phase_name, previous)

            # Execute the phase and update the results
            phase_result = phase.execute_phase(input_values, phase_fname)
            self._update_properties(phase_result, output_properties)

    def _get_input_values(self, input_properties: List[Pname]) -> List[Any]:
        inputs = []
        for inp in input_properties:
            inputs.append(self.properties[inp])
        assert len(inputs) == len(input_properties)
        return inputs

    def _update_dependencies(
        self,
        output_properties: List[Pname],
        input_properties: List[Pname],
        phase_descr: str,
    ) -> Set[str]:
        new_deps = set()
        new_deps.add(phase_descr)
        for inp in input_properties:
            new_deps.update(self.dependencies[inp])
        for outp in output_properties:
            self.dependencies[outp] = new_deps
        return new_deps

    def _get_phase_fname(self, phase_name: str, previous: Set[str]) -> str:
        previous = sorted(list(previous))
        return self.basedir + "/" + phase_name + "||" + "_".join(previous) + ".pkl.bz2"

    def _update_properties(
        self, phase_result: Tuple, output_properties: List[Pname]
    ) -> None:
        for idx, outp in enumerate(output_properties):
            if outp not in self.properties:
                self.properties[outp] = None
            self.properties[outp] = phase_result[idx]
