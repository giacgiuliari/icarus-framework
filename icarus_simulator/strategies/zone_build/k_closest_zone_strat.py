#  2020 Tommaso Ciussani and Giacomo Giuliari
import numpy as np

from typing import Tuple, List
from scipy.spatial.ckdtree import cKDTree

from icarus_simulator.sat_core.coordinate_util import geo2cart
from icarus_simulator.strategies.zone_build.base_zone_build_strat import (
    BaseZoneBuildStrat,
)
from icarus_simulator.structure_definitions import GridPos


class KclosestZoneStrat(BaseZoneBuildStrat):
    def __init__(self, size: int, **kwargs):
        super().__init__()
        self.size = size
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "kcl"

    @property
    def param_description(self) -> str:
        return f"{self.size}"

    def compute(
        self, grid_pos: GridPos, center1: int, center2: int
    ) -> Tuple[List[int], List[int]]:
        grid_cart = np.zeros((len(grid_pos), 3))
        grid_map = {}
        for i, grid_id in enumerate(grid_pos):
            grid_map[i] = grid_id
            grid_cart[i] = geo2cart(
                {"elev": 0, "lon": grid_pos[grid_id].lon, "lat": grid_pos[grid_id].lat}
            )

        # Put the homogeneous grid into a KD-tree and query all the points, summing values to the closest grid point
        closest = []
        kd = cKDTree(grid_cart)
        for point in [grid_pos[center1], grid_pos[center2]]:
            _, closest_grid_indices = kd.query(
                geo2cart({"elev": 0, "lon": point.lon, "lat": point.lat}), k=self.size
            )
            if type(closest_grid_indices) == int:
                closest_grid_indices = [closest_grid_indices]
            closest.append([grid_map[idx] for idx in closest_grid_indices])
        return closest[0], closest[1]
