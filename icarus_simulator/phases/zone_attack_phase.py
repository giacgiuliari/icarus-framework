#  2020 Tommaso Ciussani and Giacomo Giuliari

import itertools
from typing import List, Tuple
from geopy.distance import great_circle

from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.strategies.atk_detect_optimisation.base_optim_strat import (
    BaseOptimStrat,
)
from icarus_simulator.strategies.atk_feasibility_check.base_feas_strat import (
    BaseFeasStrat,
)
from icarus_simulator.strategies.atk_geo_constraint.base_geo_constraint_strat import (
    BaseGeoConstraintStrat,
)
from icarus_simulator.strategies.atk_path_filtering.base_path_filtering_strat import (
    BasePathFilteringStrat,
)
from icarus_simulator.strategies.zone_bneck.base_zone_bneck_strat import (
    BaseZoneBneckStrat,
)
from icarus_simulator.strategies.zone_build.base_zone_build_strat import (
    BaseZoneBuildStrat,
)
from icarus_simulator.strategies.zone_edges.base_zone_edges_strat import (
    BaseZoneEdgesStrat,
)
from icarus_simulator.strategies.zone_select.base_zone_select_strat import (
    BaseZoneSelectStrat,
)
from icarus_simulator.multiprocessor import Multiprocessor
from icarus_simulator.structure_definitions import (
    GridPos,
    Pname,
    BwData,
    PathData,
    EdgeData,
    AttackData,
    ZoneAttackData,
    PathEdgeData,
    ZoneAttackInfo,
)
from icarus_simulator.utils import get_ordered_idx, get_edges


class ZoneAttackPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        num_procs: int,
        num_batches: int,
        geo_constr_strat: BaseGeoConstraintStrat,
        zone_select_strat: BaseZoneSelectStrat,
        zone_build_strat: BaseZoneBuildStrat,
        zone_edges_strat: BaseZoneEdgesStrat,
        zone_bneck_strat: BaseZoneBneckStrat,
        atk_filter_strat: BasePathFilteringStrat,
        atk_feas_strat: BaseFeasStrat,
        atk_optim_strat: BaseOptimStrat,
        grid_in: Pname,
        paths_in: Pname,
        edges_in: Pname,
        bw_in: Pname,
        atk_in: Pname,
        zatk_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.num_procs = num_procs
        self.num_batches = num_batches
        self.geo_constr_strat: BaseGeoConstraintStrat = geo_constr_strat
        self.select_strat: BaseZoneSelectStrat = zone_select_strat
        self.build_strat: BaseZoneBuildStrat = zone_build_strat
        self.edges_strat: BaseZoneEdgesStrat = zone_edges_strat
        self.bneck_strat: BaseZoneBneckStrat = zone_bneck_strat
        self.filter_strat: BasePathFilteringStrat = atk_filter_strat
        self.feas_strat: BaseFeasStrat = atk_feas_strat
        self.optim_strat: BaseOptimStrat = atk_optim_strat
        self.ins: List[Pname] = [grid_in, paths_in, edges_in, bw_in, atk_in]
        self.outs: List[Pname] = [zatk_out]

    @property
    def input_properties(self) -> List[Pname]:
        return self.ins

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [
            self.geo_constr_strat,
            self.select_strat,
            self.build_strat,
            self.edges_strat,
            self.bneck_strat,
            self.filter_strat,
            self.feas_strat,
            self.optim_strat,
        ]

    @property
    def name(self) -> str:
        return "ZAtk"

    def _compute(
        self,
        grid_pos: GridPos,
        path_data: PathData,
        edge_data: EdgeData,
        bw_data: BwData,
        atk_data: AttackData,
    ) -> Tuple[AttackData]:
        allowed_sources = self.geo_constr_strat.compute(grid_pos)
        # Select the centres of the zones to be disconnected
        zone_pairs = self.select_strat.compute(grid_pos)
        # Start a multithreaded computation
        multi = ZoneAttackMultiproc(
            self.num_procs,
            self.num_batches,
            zone_pairs,
            process_params=(
                self.build_strat,
                self.edges_strat,
                self.bneck_strat,
                self.filter_strat,
                self.feas_strat,
                self.optim_strat,
                grid_pos,
                path_data,
                bw_data,
                edge_data,
                atk_data,
                allowed_sources,
            ),
            verbose=True,
        )
        ret_tuple = (multi.process_batches(),)  # It must be a tuple!
        return ret_tuple

    def _check_result(self, result: Tuple[AttackData]) -> None:
        return


class ZoneAttackMultiproc(Multiprocessor):
    def _single_sample_process(
        self, sample: Tuple[int, int], process_result: ZoneAttackData, params: Tuple
    ) -> None:
        build_strat: BaseZoneBuildStrat
        edges_strat: BaseZoneEdgesStrat
        bneck_strat: BaseZoneBneckStrat
        filter_strat: BasePathFilteringStrat
        feas_strat: BaseFeasStrat
        optim_strat: BaseOptimStrat
        grid_pos: GridPos
        path_data: PathData
        bw_data: BwData
        edge_data: EdgeData
        atk_data: AttackData
        (
            build_strat,
            edges_strat,
            bneck_strat,
            filter_strat,
            feas_strat,
            optim_strat,
            grid_pos,
            path_data,
            bw_data,
            edge_data,
            atk_data,
            allowed_sources,
        ) = params

        # Process the single sample
        zone1, zone2 = build_strat.compute(grid_pos, sample[0], sample[1])

        sample_res_idx = tuple(zone1), tuple(zone2)
        # Firstly, if the zones overlap we say the disconnection fails, as an isl-only disconnection is not possible
        if len(set(zone1).intersection(set(zone2))) > 0:
            # The zones are not included in the results, as the sample pair is bad
            return

        # Find the minimum distance and all (desirable by routing phase) paths between zones
        min_dist = min(
            great_circle(
                (grid_pos[idx1].lat, grid_pos[idx1].lon),
                (grid_pos[idx2].lat, grid_pos[idx2].lon),
            ).meters
            for idx1 in zone1
            for idx2 in zone2
        )
        cross_zone_paths = compute_zone_crossing_paths(zone1, zone2, path_data)

        # Find all edges in all desirable
        path_edges: PathEdgeData = {}
        covered_paths_potential = set()
        for d_idx, d in enumerate(cross_zone_paths):
            for ed in get_edges(d):
                # Filter out the edges not allowed by the edge strategy and the non-singularly-attackable
                if edges_strat.compute(ed) and atk_data[ed] is not None:
                    covered_paths_potential.add(d_idx)
                    if ed not in path_edges:
                        path_edges[ed] = set()
                    path_edges[ed].add(d_idx)

        # Check if a cut can be achieved with these edges only and exit early if not
        if len(path_edges) == 0 or len(covered_paths_potential) < len(cross_zone_paths):
            process_result[sample_res_idx] = None
            return

        # Compute the possible heuristically-determined bottlenecks and check which one is the best
        uplink_size = max(
            bw_data[ed].capacity for ed in bw_data if ed[0] == -1
        )  # Max in case of weird bw assignments
        possible_bnecks = bneck_strat.compute(
            bw_data, atk_data, path_edges, len(cross_zone_paths)
        )
        best_atk_flow_set, best_on_trg, best_detect, best_bneck = (
            None,
            9000000000,
            90000000000,
            None,
        )
        for bneck in possible_bnecks:
            direction_data = filter_strat.compute(
                bneck, edge_data, path_data, allowed_sources
            )

            # A4: feasibility check
            atk_flow_set, on_trg, detect = feas_strat.compute(
                bneck, path_data, bw_data, direction_data, uplink_size
            )
            if atk_flow_set is None:
                continue

            # A5: iterative optimisation
            # We firstly need the maximum increase value possible, that is maximum capacity of all uplinks
            atk_flow_set, on_trg, detect = optim_strat.compute(
                bneck, path_data, bw_data, direction_data, uplink_size, feas_strat
            )
            # Deterministic allocation, therefore cost = on_trg
            if detect < best_detect or (detect == best_detect and on_trg < best_on_trg):
                best_atk_flow_set = atk_flow_set
                best_on_trg = on_trg
                best_detect = detect
                best_bneck = bneck

        if best_atk_flow_set is None:
            process_result[sample_res_idx] = None
            return

        process_result[sample_res_idx] = ZoneAttackInfo(
            cost=best_on_trg,
            detectability=best_detect,
            flows_on_trg=best_on_trg,
            atkflowset=best_atk_flow_set,
            cross_zone_paths=cross_zone_paths,
            bottlenecks=best_bneck,
            distance=min_dist,
        )
        return


def compute_zone_crossing_paths(zone1: List[int], zone2: List[int], path_data):
    # Analyse all possible pairs that go across zones
    paths_across = []
    for src in zone1:
        for trg in zone2:
            ord_pair, ordered = get_ordered_idx((src, trg))
            path_part = [pd[0][1:-1] for pd in path_data[ord_pair]]
            for i in range(len(path_part)):
                p = path_part[i]
                if ordered:
                    path_part[i] = [-1] + p + [-1]
                else:
                    path_part[i] = [-1] + list(reversed(p)) + [-1]
            paths_across.extend(path_part)

    paths_across.sort()
    paths_across = [item for item, _ in itertools.groupby(paths_across)]
    return paths_across
