#  2020 Tommaso Ciussani and Giacomo Giuliari
from icarus_simulator.sat_core.coverage import positions_satellite_coverage

from icarus_simulator.strategies.coverage.base_coverage_strat import BaseCoverageStrat
from icarus_simulator.structure_definitions import SatPos, GridPos, Coverage


class AngleCovStrat(BaseCoverageStrat):
    def __init__(self, min_elev_angle: int, **kwargs):
        super().__init__()
        self.min_elev_angle = min_elev_angle
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "ang"

    @property
    def param_description(self) -> str:
        return f"{self.min_elev_angle}°"

    def compute(self, grid_pos: GridPos, sat_pos: SatPos) -> Coverage:
        coverage = positions_satellite_coverage(
            {ka: v.to_geo_pos() for ka, v in grid_pos.items()},
            {ka: v.to_geo_pos() for ka, v in sat_pos.items()},
            self.min_elev_angle,
        )
        return coverage
