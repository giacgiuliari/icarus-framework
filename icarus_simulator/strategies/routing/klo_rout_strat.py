#  2020 Tommaso Ciussani and Giacomo Giuliari
import networkx as nx

from heapq import heapify, heappop
from geopy.distance import great_circle

from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.structure_definitions import GridPos, SdPair, Coverage, LbSet
from icarus_simulator.utils import (
    get_edge_length,
    get_ordered_idx,
    get_edges,
    similarity,
)


class KLORoutStrat(BaseRoutingStrat):
    def __init__(self, desirability_stretch: float, k: int, esx_theta: float, **kwargs):
        super().__init__()
        self.desirability_stretch = desirability_stretch
        self.k = k
        self.esx_theta = esx_theta
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "klo"

    @property
    def param_description(self) -> str:
        return f"{self.desirability_stretch}k{self.k}th{self.esx_theta}"

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

        # Run the ESX algorithm. Find the shortest path first
        try:
            length, path = nx.single_source_dijkstra(
                network, -pair[0], -pair[1], cutoff=fiber_len, weight="length"
            )
            chosen_paths = [
                {
                    "path": path,
                    "length": length,
                    "heap": [
                        (get_edge_length(network, ed), ed) for ed in get_edges(path)
                    ][1:-1],
                }
            ]
            heapify(chosen_paths[0]["heap"])
            p_c = chosen_paths[0]
        except nx.NetworkXNoPath:
            chosen_paths = []
            p_c = None

        excluded_eds, lengths = set(), {}
        while len(chosen_paths) < self.k and any(
            len(ch["heap"]) > 0 for ch in chosen_paths
        ):
            # Firstly, check if the current p_c can be added to the chosen paths -> all similarities < theta
            sim_values = [
                (
                    similarity(
                        p_c["path"], ch["path"], p_c["length"], ch["length"], network
                    ),
                    len(ch["heap"]),
                    idx,
                )
                for idx, ch in enumerate(chosen_paths)
            ]
            if all(sv[0] <= self.esx_theta for sv in sim_values):
                p_c["heap"] = [
                    (get_edge_length(network, ed), ed) for ed in get_edges(p_c["path"])
                ][1:-1]
                heapify(p_c["heap"])
                chosen_paths.append(p_c)
                sim_values.append(
                    (1.0, len(p_c["heap"]), len(chosen_paths) - 1)
                )  # Append similarity p_c to p_c

            # We want to update p_c by making it more dissimilar from the most similar path available.
            # To do this, we find the most similar path that has edges left in its heap, and remove top edge from net
            sim_values.sort(key=lambda k: k[0], reverse=True)
            most_similar_idx = next(sv[2] for sv in sim_values if sv[1] > 0)
            most_similar = chosen_paths[most_similar_idx]

            top_ed = heappop(most_similar["heap"])[1]
            ord_top = get_ordered_idx(top_ed)[0]
            if ord_top in excluded_eds or ord_top in lengths:
                continue
            lengths[ord_top] = get_edge_length(network, top_ed)
            network[top_ed[0]][top_ed[1]]["length"] = float("inf")

            # Get the shortest path available. Optimisations are put into place:
            # * This code uses setting to float("inf") instead of deleting edges, much faster
            # * Heuristically, the dijkstra call can be done with the cutoff set to fiber_length: it is much easier for
            #   a call to fail bc the path is too long rather than bc the graph is disconnected in this setting
            # * Cutoff reduces runtime considerably in case of no convenient available
            # * If that fails, check for disconnection with BFS
            try:
                length, path = nx.single_source_dijkstra(
                    network, -pair[0], -pair[1], cutoff=fiber_len, weight="length"
                )
                p_c = {"path": path, "length": length}
            except nx.NetworkXNoPath:
                cc = nx.node_connected_component(network, -pair[0])
                if -pair[1] in cc:
                    # Connected: current path is too long and so will be the future ones
                    break
                # Disconnected: this edge must not be removed, or disconnection. Revert.
                network[top_ed[0]][top_ed[1]]["length"] = lengths[ord_top]
                del lengths[ord_top]
                excluded_eds.add(ord_top)

        # Rebuild the original network, then delete the added nodes
        for ed in lengths:
            network[ed[0]][ed[1]]["length"] = lengths[ed]
        for gnd in pair:
            network.remove_node(-gnd)
        return [(ch["path"], ch["length"]) for ch in chosen_paths]
