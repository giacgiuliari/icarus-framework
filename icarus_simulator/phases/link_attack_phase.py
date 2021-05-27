#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import List, Tuple

from icarus_simulator.phases.base_phase import BasePhase
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
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.multiprocessor import Multiprocessor
from icarus_simulator.structure_definitions import (
    GridPos,
    Pname,
    BwData,
    PathData,
    EdgeData,
    Edge,
    AttackInfo,
    AttackData,
)


class LinkAttackPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        num_procs: int,
        num_batches: int,
        geo_constr_strat: BaseGeoConstraintStrat,
        filter_strat: BasePathFilteringStrat,
        feas_strat: BaseFeasStrat,
        optim_strat: BaseOptimStrat,
        grid_in: Pname,
        paths_in: Pname,
        edges_in: Pname,
        bw_in: Pname,
        latk_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.num_procs = num_procs
        self.num_batches = num_batches
        self.geo_constr_strat: BaseGeoConstraintStrat = geo_constr_strat
        self.filter_strat: BasePathFilteringStrat = filter_strat
        self.feas_strat: BaseFeasStrat = feas_strat
        self.optim_strat: BaseOptimStrat = optim_strat
        self.ins: List[Pname] = [grid_in, paths_in, edges_in, bw_in]
        self.outs: List[Pname] = [latk_out]

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
            self.filter_strat,
            self.feas_strat,
            self.optim_strat,
        ]

    @property
    def name(self) -> str:
        return "LAtk"

    def _compute(
        self,
        grid_pos: GridPos,
        path_data: PathData,
        edge_data: EdgeData,
        bw_data: BwData,
    ) -> Tuple[AttackData]:
        # Elaborate a list of the edges to be attacked
        edges = list(bw_data.keys())
        allowed_sources = self.geo_constr_strat.compute(grid_pos)
        # Start a multithreaded computation
        multi = AttackMultiproc(
            self.num_procs,
            self.num_batches,
            edges,
            process_params=(
                self.filter_strat,
                self.feas_strat,
                self.optim_strat,
                path_data,
                edge_data,
                bw_data,
                allowed_sources,
            ),
        )
        ret_tuple = (multi.process_batches(),)  # It must be a tuple!
        return ret_tuple

    def _check_result(self, result: Tuple[AttackData]) -> None:
        return


class AttackMultiproc(Multiprocessor):
    def _single_sample_process(
        self, sample: Edge, process_result: AttackData, params: Tuple
    ) -> None:
        filter_strat: BasePathFilteringStrat
        feas_strat: BaseFeasStrat
        optim_strat: BaseOptimStrat
        (
            filter_strat,
            feas_strat,
            optim_strat,
            path_data,
            edge_data,
            bw_data,
            allowed_sources,
        ) = params
        # This method computes the attack phases.
        # A1 is comprised of all the previously done work until here.
        # A2 is instead irrelevant as there is no bneck choice.
        # A3: path filtering
        direction_data = filter_strat.compute(
            [sample], edge_data, path_data, allowed_sources
        )

        # A4: feasibility check
        uplink_size = max(
            bw_data[ed].capacity for ed in bw_data if ed[0] == -1
        )  # Max in case of weird bw assignments
        atk_flow_set, on_trg, detect = feas_strat.compute(
            [sample], path_data, bw_data, direction_data, uplink_size
        )
        if atk_flow_set is None:
            process_result[sample] = None
            return

        # A5: iterative optimisation
        # We firstly need the maximum increase value possible, that is maximum capacity of all uplinks
        atk_flow_set, on_trg, detect = optim_strat.compute(
            [sample], path_data, bw_data, direction_data, uplink_size, feas_strat
        )

        process_result[sample] = AttackInfo(
            cost=sum([el[1] for el in atk_flow_set]),
            detectability=detect,
            flows_on_trg=on_trg,
            atkflowset=atk_flow_set,
        )
