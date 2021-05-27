#  2020 Tommaso Ciussani and Giacomo Giuliari
import networkx as nx
from geopy.distance import great_circle

from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.structure_definitions import GridPos, SdPair, Coverage, LbSet


class KDGRoutStrat(BaseRoutingStrat):
    def __init__(self, desirability_stretch: float, k: int, **kwargs):
        super().__init__()
        self.desirability_stretch = desirability_stretch
        self.k = k
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "kdg"

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

        # Compute the possible paths using the chosen criterion
        lbset: LbSet = []
        lengths = {}
        cnt = 0
        while True:
            try:
                length, path = nx.single_source_dijkstra(
                    network, -pair[0], -pair[1], cutoff=fiber_len, weight="length"
                )
            except nx.NetworkXNoPath:
                break

            lbset.append((path, length))
            cnt += 1
            if cnt >= self.k:
                break
            # It makes no sense to find alternate paths in gnd-sat-gnd situation, as they will likely be too long
            if len(path) <= 3:
                break

            # Set used edges to INF length.
            for n in path[1:-1]:
                out_ed = network.edges(n)
                for ed in out_ed:
                    # Exclude up and downlinks from the disjointness
                    if ed not in lengths and (ed[1], ed[0]) not in lengths:
                        lengths[ed] = network[ed[0]][ed[1]]["length"]
                        network[ed[0]][ed[1]]["length"] = float("inf")
        # Restore the infinite lengths
        for ed in lengths:
            network[ed[0]][ed[1]]["length"] = lengths[ed]

        # Delete the added nodes
        for gnd in pair:
            network.remove_node(-gnd)
        return lbset
