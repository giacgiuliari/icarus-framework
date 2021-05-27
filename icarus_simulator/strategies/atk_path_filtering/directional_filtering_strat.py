#  2020 Tommaso Ciussani and Giacomo Giuliari
from typing import List

from icarus_simulator.strategies.atk_path_filtering.base_path_filtering_strat import (
    BasePathFilteringStrat,
)
from icarus_simulator.structure_definitions import (
    Edge,
    PathData,
    EdgeData,
    DirectionData,
)


class DirectionalFilteringStrat(BasePathFilteringStrat):
    @property
    def name(self) -> str:
        return "dir"

    @property
    def param_description(self) -> None:
        return None

    def compute(
        self,
        edges: List[Edge],
        edge_data: EdgeData,
        path_data: PathData,
        allowed_sources: List[int],
    ) -> DirectionData:
        direction_data = {}
        for edge in edges:
            inv_ed = (edge[1], edge[0])
            idxs_in_order = edge_data[edge].paths_through
            idxs_in_rev = edge_data[inv_ed].paths_through

            # Avoid duplicate indices. It can occur that gnd-sat-gnd paths are in both lists
            set_in_order, set_in_rev = set(idxs_in_order), set(idxs_in_rev)
            set_in_rev.difference_update(set_in_order)
            idxs_in_rev = list(set_in_rev)

            # Extract the path in the correct order
            idxs = idxs_in_order + idxs_in_rev
            for i, idx in enumerate(idxs):
                in_order = i < len(idxs_in_order)
                base_path = path_data[(idx[0], idx[1])][idx[2]][0]
                pair = idx[0], idx[1]
                if not in_order:
                    base_path = base_path[::-1]
                    pair = idx[1], idx[0]
                # Skip if the source is not in the allowed sources
                if -base_path[0] not in allowed_sources:
                    continue

                # Path truncation
                # Cut the path at the target if ed[1] != -1. In this case the whole path is kept.
                if edge[1] != -1:
                    last_idx = base_path.index(edge[1])
                    truncated = tuple([-1] + base_path[1 : last_idx + 1])
                else:
                    truncated = tuple([-1] + base_path[1:-1] + [-1])

                # Note that we are not adding ordered pairs! Sending data from a to b is different
                # than sending from b to a, the probability of hitting the target is different!
                if truncated not in direction_data:
                    direction_data[truncated] = []
                direction_data[truncated].append(pair)  # Add multiple times if needed

        return direction_data
