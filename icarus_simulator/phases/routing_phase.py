#  2020 Tommaso Ciussani and Giacomo Giuliari

import networkx as nx
from typing import List, Tuple, Dict

from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.multiprocessor import Multiprocessor
from icarus_simulator.structure_definitions import (
    PathData,
    GridPos,
    Coverage,
    SdPair,
    Pname,
    LbSet,
)


class RoutingPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        num_procs: int,
        num_batches: int,
        rout_strat: BaseRoutingStrat,
        grid_in: Pname,
        nw_in: Pname,
        cov_in: Pname,
        paths_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.num_procs = num_procs
        self.num_batches = num_batches
        self.rout_strat: BaseRoutingStrat = rout_strat
        self.ins: List[Pname] = [grid_in, nw_in, cov_in]
        self.outs: List[Pname] = [paths_out]

    @property
    def input_properties(self) -> List[Pname]:
        return self.ins

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.rout_strat]

    @property
    def name(self) -> str:
        return "Routes"

    def _compute(
        self, grid: GridPos, network: nx.Graph, coverage: Coverage
    ) -> Tuple[PathData]:
        # Elaborate a list of the sdpairs to be computed
        grid_ids = list(grid.keys())
        pairs = []
        for src_key_id in range(len(grid_ids) - 1):
            in_grid = grid_ids[src_key_id]
            for dst_key_id in range(src_key_id + 1, len(grid_ids)):
                out_grid = grid_ids[dst_key_id]
                pairs.append((in_grid, out_grid))
        # Start a multithreaded computation
        multi = RoutingMultiproc(
            self.num_procs,
            self.num_batches,
            pairs,
            process_params=(grid, network, coverage, self.rout_strat),
        )
        ret_tuple = (multi.process_batches(),)  # It must be a tuple!
        return ret_tuple

    def _check_result(self, result: Tuple[PathData]) -> None:
        path_data = result[0]
        for sdpair in path_data:
            assert sdpair[0] < sdpair[1]
        return


class RoutingMultiproc(Multiprocessor):
    def _single_sample_process(
        self, sample: SdPair, process_result: Dict[SdPair, LbSet], params: Tuple
    ) -> None:
        grid: GridPos
        network: nx.Graph
        coverage: Coverage
        rout_strat: BaseRoutingStrat
        grid, network, coverage, rout_strat = params
        process_result[sample] = rout_strat.compute(sample, grid, network, coverage)
