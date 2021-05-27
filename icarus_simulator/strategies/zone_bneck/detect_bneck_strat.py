#  2020 Tommaso Ciussani and Giacomo Giuliari
import copy

from typing import List

from icarus_simulator.strategies.zone_bneck.base_zone_bneck_strat import (
    BaseZoneBneckStrat,
)
from icarus_simulator.structure_definitions import (
    PathEdgeData,
    Edge,
    AttackData,
    BwData,
)


class DetectBneckStrat(BaseZoneBneckStrat):
    @property
    def name(self) -> str:
        return "dtct"

    @property
    def param_description(self) -> None:
        return None

    def compute(
        self,
        bw_data: BwData,
        atk_data: AttackData,
        path_edges: PathEdgeData,
        tot_cross_zone_paths: int,
    ) -> List[List[Edge]]:
        incrs = {ed: atk_data[ed].detectability for ed in path_edges}
        costs = {ed: (incrs[ed] / len(path_edges[ed])) for ed in path_edges}
        sorted_path_edges = sorted(costs.items(), key=lambda k: k[1])

        # Then pick edges until full coverage is reached, with 3 specific attempts
        inf = 90000000000000  # High value given to the already chosen edges
        bnecks = []
        for attempt_id in range(3):
            costs_copy = copy.deepcopy(costs)
            covered_paths, picked_edges, best_ed = set(), [], None

            # Force insertion of the 1st, 2nd and 3rd best elements in each attempt, to shake things up
            try:
                best_ed = sorted_path_edges[attempt_id][0]  # Get the key of the edge
            except IndexError:  # The edge cannot be inserted, not enough candidates
                continue
            picked_edges.append(best_ed)
            costs_copy[best_ed] = inf
            covered_paths.update(path_edges[best_ed])

            # Insert the rest of the edges
            while len(covered_paths) < tot_cross_zone_paths:
                # First, update the cost function to only include the non-covered paths
                # costs[ed] = detectability / new_paths_covered
                for ed in costs_copy:
                    if costs_copy[ed] < inf:
                        diff_len = len(path_edges[ed].difference(covered_paths))
                        if diff_len == 0:
                            costs_copy[ed] = inf  # useless, does not cover anything new
                        else:
                            costs_copy[ed] = incrs[ed] / diff_len

                best_ed = min(costs_copy, key=lambda k: costs_copy[k])
                if (
                    costs_copy[best_ed] == inf
                ):  # No more edges to choose from, we chose all of them
                    break
                picked_edges.append(best_ed)
                costs_copy[best_ed] = inf
                covered_paths.update(path_edges[best_ed])

            # Greedily remove the redundant links
            # Criterion (minimised, maximised): (min_redundancy, atk_bw)
            redundancies = [0] * tot_cross_zone_paths
            for pe in picked_edges:
                for p in path_edges[pe]:
                    redundancies[p] += 1
            # Pick the most redundant one each time and remove it
            while True:
                removable_edges = []
                for pe in picked_edges:
                    removable, min_redundancy = True, 999999
                    for p in path_edges[pe]:
                        min_redundancy = min(min_redundancy, redundancies[p])
                        if redundancies[p] - 1 == 0:
                            removable = False
                            break
                    if removable:
                        removable_edges.append(
                            (min_redundancy, bw_data[pe].get_remaining_bw(), pe)
                        )
                if len(removable_edges) == 0:
                    break
                chosen = min(removable_edges, key=lambda k: (k[0], -k[1]))[2]
                for p in path_edges[chosen]:
                    redundancies[p] -= 1
                picked_edges.remove(chosen)

            # Check if the found bottleneck covers all the paths to be covered
            covered_paths = set()
            for link in picked_edges:
                covered_paths.update(path_edges[link])
            if len(covered_paths) == tot_cross_zone_paths:
                bnecks.append(picked_edges)

        return bnecks
