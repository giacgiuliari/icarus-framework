#  2020 Tommaso Ciussani and Giacomo Giuliari
from typing import Set, List

from icarus_simulator.strategies.atk_geo_constraint.base_geo_constraint_strat import (
    BaseGeoConstraintStrat,
)
from icarus_simulator.structure_definitions import GridPos


class GridConstrStrat(BaseGeoConstraintStrat):
    def __init__(self, grid_points: List[int], **kwargs):
        super().__init__()
        self.grid_points = grid_points
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "grd"

    @property
    def param_description(self) -> str:
        return ",".join([str(i) for i in self.grid_points])

    def compute(self, grid_pos: GridPos) -> Set[int]:
        return set(self.grid_points)
