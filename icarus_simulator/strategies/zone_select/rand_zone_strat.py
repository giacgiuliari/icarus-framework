#  2020 Tommaso Ciussani and Giacomo Giuliari
import random

from typing import Tuple, List

from icarus_simulator.strategies.zone_select.base_zone_select_strat import (
    BaseZoneSelectStrat,
)
from icarus_simulator.structure_definitions import GridPos


class RandZoneStrat(BaseZoneSelectStrat):
    def __init__(self, samples: int, **kwargs):
        super().__init__()
        self.samples = samples
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "ran"

    @property
    def param_description(self) -> str:
        return f"{self.samples}"

    def compute(self, grid_pos: GridPos) -> List[Tuple[int, int]]:
        random.seed("Icarus")
        indices, locs, grid_pts = [], set(), list(grid_pos.keys())
        for i in range(self.samples):
            loc1, loc2 = tuple(random.sample(grid_pts, 2))
            indices.append((loc1, loc2))
        return indices
