#  2020 Tommaso Ciussani and Giacomo Giuliari
import networkx as nx
from geopy.distance import great_circle

from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.structure_definitions import GridPos, SdPair, Coverage, LbSet


class KSPRoutStrat(BaseRoutingStrat):
    def __init__(self, desirability_stretch: float, k: int, **kwargs):
        super().__init__()
        self.desirability_stretch = desirability_stretch
        self.k = k
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "ksp"

    @property
    def param_description(self) -> str:
        return f"{self.desirability_stretch}k{self.k}"

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
        # Add the gnd nodes
        for gnd in pair:
            for dst_sat in coverage[gnd]:
                network.add_edge(-gnd, dst_sat, length=coverage[gnd][dst_sat])

        # Compute the first n shortest paths
        lbset: LbSet = []
        cnt = 0
        gen = nx.shortest_simple_paths(network, -pair[0], -pair[1], weight="length")
        for path in gen:
            path_length = 0.0
            for i in range(len(path) - 1):
                path_length += network[path[i]][path[i + 1]]["length"]
            if path_length > fiber_len:
                break
            lbset.append((path, path_length))
            cnt += 1
            if cnt >= self.k:
                break
        # Remove the added nodes
        for gnd in pair:
            network.remove_node(-gnd)
        return lbset
