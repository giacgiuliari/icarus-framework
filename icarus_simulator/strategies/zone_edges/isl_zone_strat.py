#  2020 Tommaso Ciussani and Giacomo Giuliari
from icarus_simulator.strategies.zone_edges.base_zone_edges_strat import (
    BaseZoneEdgesStrat,
)
from icarus_simulator.structure_definitions import Edge


class ISLZoneStrat(BaseZoneEdgesStrat):
    @property
    def name(self) -> str:
        return "isl"

    @property
    def param_description(self) -> None:
        return None

    def compute(self, edge: Edge) -> bool:
        return -1 not in edge
