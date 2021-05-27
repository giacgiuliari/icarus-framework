#  2020 Tommaso Ciussani and Giacomo Giuliari
from icarus_simulator.strategies.grid_weight.base_weight_strat import BaseWeightStrat
from icarus_simulator.structure_definitions import GridPos


class UniformWeightStrat(BaseWeightStrat):
    @property
    def name(self) -> str:
        return "uni"

    @property
    def param_description(self) -> None:
        return None

    def compute(self, grid_pos: GridPos) -> GridPos:
        # Add the default weight for this unweighted grid
        for idx in grid_pos:
            grid_pos[idx].weight = 1.0
        return grid_pos
