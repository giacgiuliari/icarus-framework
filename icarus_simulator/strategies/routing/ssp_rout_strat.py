#  2020 Tommaso Ciussani and Giacomo Giuliari
import networkx as nx
from geopy.distance import great_circle

from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.structure_definitions import (
    GridPos,
    SdPair,
    Coverage,
    LbSet,
    PathInfo,
)


class SSPRoutStrat(BaseRoutingStrat):
    def __init__(self, desirability_stretch: float, **kwargs):
        super().__init__()
        self.desirability_stretch = desirability_stretch
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "ssp"

    @property
    def param_description(self) -> str:
        return f"{self.desirability_stretch}"

    def compute(
        self, pair: SdPair, grid: GridPos, network: nx.Graph, coverage: Coverage
    ) -> LbSet:
        in_grid, out_grid = pair[0], pair[1]
        fiber_len = (
            great_circle(
                (grid[in_grid].lat, grid[in_grid].lon),
                (grid[out_grid].lat, grid[out_grid].lon),
            ).meters
            * self.desirability_stretch
        )
        # Add the gnd nodes to the network, flipping the sign
        for gnd in pair:
            for dst_sat in coverage[gnd]:
                network.add_edge(-gnd, dst_sat, length=coverage[gnd][dst_sat])

        # Compute the shortest path
        lbset: LbSet = []
        try:
            length, path = nx.single_source_dijkstra(
                network, -pair[0], -pair[1], cutoff=fiber_len, weight="length"
            )
            pi: PathInfo = (path, length)
            lbset.append(pi)
        except nx.NetworkXNoPath:
            pass

        # Remove the added nodes
        for gnd in pair:
            network.remove_node(-gnd)
        return lbset
