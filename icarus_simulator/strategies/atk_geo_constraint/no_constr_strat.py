#  2020 Tommaso Ciussani and Giacomo Giuliari
from typing import Set

from icarus_simulator.strategies.atk_geo_constraint.base_geo_constraint_strat import (
    BaseGeoConstraintStrat,
)
from icarus_simulator.structure_definitions import GridPos


class NoConstrStrat(BaseGeoConstraintStrat):
    @property
    def name(self) -> str:
        return "no"

    @property
    def param_description(self) -> None:
        return None

    def compute(self, grid_pos: GridPos) -> Set[int]:
        return set(grid_pos.keys())
