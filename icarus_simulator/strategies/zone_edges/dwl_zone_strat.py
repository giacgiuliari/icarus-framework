#  2020 Tommaso Ciussani and Giacomo Giuliari
from icarus_simulator.strategies.zone_edges.base_zone_edges_strat import (
    BaseZoneEdgesStrat,
)
from icarus_simulator.structure_definitions import Edge


class DWLZoneStrat(BaseZoneEdgesStrat):
    @property
    def name(self) -> str:
        return "dwl"

    @property
    def param_description(self) -> None:
        return None

    def compute(self, edge: Edge) -> bool:
        return edge[1] == -1
