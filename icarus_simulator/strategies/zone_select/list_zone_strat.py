#  2020 Tommaso Ciussani and Giacomo Giuliari
from typing import Tuple, List

from icarus_simulator.strategies.zone_select.base_zone_select_strat import (
    BaseZoneSelectStrat,
)
from icarus_simulator.structure_definitions import GridPos


class ListZoneStrat(BaseZoneSelectStrat):
    def __init__(self, centers: List[Tuple[int, int]], **kwargs):
        super().__init__()
        self.centers = centers
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "lst"

    @property
    def param_description(self) -> str:
        return f"{self.centers}"

    def compute(self, grid_pos: GridPos) -> List[Tuple[int, int]]:
        for tup in self.centers:
            for loc in tup:
                assert loc in grid_pos.keys()
        return self.centers
