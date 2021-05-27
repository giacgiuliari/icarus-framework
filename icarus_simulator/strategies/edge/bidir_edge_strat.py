#  2020 Tommaso Ciussani and Giacomo Giuliari
from typing import Dict

from icarus_simulator.strategies.edge.base_edge_strat import BaseEdgeStrat
from icarus_simulator.structure_definitions import Path, PathId, Edge, TempEdgeInfo
from icarus_simulator.utils import get_edges


class BidirEdgeStrat(BaseEdgeStrat):
    @property
    def name(self) -> str:
        return "bidir"

    @property
    def param_description(self) -> None:
        return None

    # Side effects on temp_edge_data are produced
    def compute(
        self, temp_edge_data: Dict[Edge, TempEdgeInfo], path: Path, path_id: PathId
    ) -> None:
        # Convert the up and downlink to the -1 convention
        first, last = -path[0], -path[-1]
        path[0], path[-1] = -1, -1
        # For each edge in each path, compute stats
        for ed in get_edges(path):
            inv_ed = (ed[1], ed[0])
            if ed not in temp_edge_data:
                # paths_through, centrality, start_points
                temp_edge_data[ed] = TempEdgeInfo([], 0, set())
                temp_edge_data[inv_ed] = TempEdgeInfo([], 0, set())
            # Update paths_through
            # IMPORTANT: paths_through will ONLY contain paths through with the edge in the same order.
            # Also the paths through the opposite edge are through the current edge, but must be taken in reversed form.
            temp_edge_data[ed].paths_through.append(path_id)
            # Update edge centrality
            temp_edge_data[ed].centrality += 1
            temp_edge_data[inv_ed].centrality += 1
            # Update start_points
            temp_edge_data[ed].source_gridpoints.add(first)
            temp_edge_data[inv_ed].source_gridpoints.add(last)
        # Restore the path first and last (gnd) hops
        path[0], path[-1] = -first, -last
