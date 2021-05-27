#  2020 Tommaso Ciussani and Giacomo Giuliari
from math import sqrt, log, ceil
from typing import List, Optional, Tuple

from icarus_simulator.strategies.atk_feasibility_check.base_feas_strat import (
    BaseFeasStrat,
)
from icarus_simulator.structure_definitions import (
    Edge,
    PathData,
    DirectionData,
    BwData,
    PairData,
    AtkFlowSet,
    PairInfo,
)
from icarus_simulator.utils import get_ordered_idx, get_edges


class ProbFeasStrat(BaseFeasStrat):
    def __init__(self, beta: float, **kwargs):
        super().__init__()
        self.beta = beta
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "prb"

    @property
    def param_description(self) -> str:
        return f"{self.beta}"

    # Important note: this only works for single-target attacks!
    def compute(
        self,
        congest_edges: List[Edge],
        path_data: PathData,
        bw_data: BwData,
        direction_data: DirectionData,
        max_uplink_increase: int,
    ) -> Tuple[Optional[AtkFlowSet], int, int]:
        isl_num = int(len([ed for ed in bw_data if -1 not in ed]) / 2)
        gamma = 1 / (isl_num ** 2)
        assert (
            len(congest_edges) == 1
        )  # Otherwise, this strategy does not work yet. Needs some brain work to adapt.
        target = congest_edges[0]
        needed_hosts = bw_data[target].get_remaining_bw()

        # Prepare a list of sorted probabilities -> sort is for the greedy algorithm
        prob_map: PairData = {}
        for dire, pairs in direction_data.items():
            for p in pairs:
                if p not in prob_map:
                    prob_map[p] = PairInfo()
                prob_map[p].prob += 1
                prob_map[p].directions.add(dire)
        for p in prob_map:
            ord_p = get_ordered_idx(p)[0]
            prob_map[p].prob /= len(path_data[ord_p])
            prob_map[p].tot = len(path_data[ord_p])

        pair_list = list(prob_map.keys())
        pair_list.sort(key=lambda k: prob_map[k].prob, reverse=True)

        # Compute the probabilistic structure
        mean, min_mean = (
            0.0,
            sqrt(log(self.beta) * (log(self.beta) - 2 * needed_hosts))
            + needed_hosts
            - log(self.beta),
        )
        link_means, link_max_means, link_caps = {}, {}, {}
        atk_flow_set = set()

        # For each pair, check how many sdpairs we can add to the attack set
        for pair in pair_list:
            # Count how many directions in the pair traverse each edge
            prob, tot, dirs = (
                prob_map[pair].prob,
                prob_map[pair].tot,
                prob_map[pair].directions,
            )
            link_counts = {}
            for di in dirs:
                for link in get_edges(
                    di, excl_end=1
                ):  # -1, because the last edge is the flooded one
                    if link not in link_means:
                        if link[0] == -1:
                            cap = min(
                                bw_data[link].get_remaining_bw(), max_uplink_increase
                            )
                        else:
                            cap = bw_data[link].get_remaining_bw()
                        link_caps[link], link_means[link] = cap, 0.0
                        link_max_means[link] = (
                            -sqrt(log(gamma) * (log(gamma) - 8 * cap))
                            - log(gamma)
                            + 2 * cap
                        ) / 2
                    if link not in link_counts:
                        link_counts[link] = 0
                    link_counts[link] += 1

            # Compute minimum number of hosts needed to flood
            if prob == 1.0:
                fits = int(ceil(needed_hosts - mean))
            else:
                fits = int(ceil((min_mean - mean) / prob))

            # Enforce no self-bnecks: Check how many can fit in the links without having too large link mean
            for link in link_counts:
                link_prob = link_counts[link] / tot
                if link_prob == 1.0:
                    fits_link = int(link_caps[link] - link_means[link])
                else:
                    fits_link = int(
                        (link_max_means[link] - link_means[link]) / link_prob
                    )
                fits = min(fits, fits_link)
                if fits <= 0:
                    break
            # If no host can fit, continue to next pair
            if fits <= 0:
                continue

            # Update min/max means if prob is 1, otw update mean
            if prob == 1.0:
                needed_hosts -= fits
                if needed_hosts <= 0:
                    min_mean = 0.0
                else:
                    min_mean = (
                        sqrt(log(self.beta) * (log(self.beta) - 2 * needed_hosts))
                        + needed_hosts
                        - log(self.beta)
                    )
            else:
                mean += prob * fits

            atk_flow_set.add((pair, fits))
            if mean >= min_mean:  # Do not update link means if you can exit
                break

            for link in link_counts:
                link_prob = link_counts[link] / tot
                # If the prob is 1, allocation is deterministic: all hosts will be allocated to the current link
                # In this case, update the cap and the max_mean, without updating the mean
                # Otherwise, update the mean
                if link_prob == 1.0:
                    link_caps[link] = max(link_caps[link] - fits, 0)
                    cap = link_caps[link]
                    # We do not need any if/else here, because the max with 0 takes care of it
                    link_max_means[link] = max(
                        (
                            -sqrt(log(gamma) * (log(gamma) - 8 * cap))
                            - log(gamma)
                            + 2 * cap
                        )
                        / 2,
                        0,
                    )
                else:
                    link_means[link] += (link_counts[link] / tot) * fits

        if mean < min_mean:  # If not successful, return None
            return None, -1, -1

        # Determine the probabilistic number of flows on target and the maximum increase
        on_trg = ceil(
            mean + bw_data[target].get_remaining_bw() - needed_hosts
        )  # mean covers needed_hosts, not rest
        detect = -1
        for link in link_caps:
            if link[0] == -1:
                incr = ceil(
                    link_means[link]
                    + min(  # This covers the final capacity, the next line accounts for optim
                        bw_data[link].get_remaining_bw(), max_uplink_increase
                    )
                    - link_caps[link]
                )
                if incr > detect:
                    detect = incr

        return atk_flow_set, on_trg, detect
