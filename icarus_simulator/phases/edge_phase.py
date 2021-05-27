#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import List, Tuple, Dict

import networkx as nx

from icarus_simulator.strategies.edge.base_edge_strat import BaseEdgeStrat
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.multiprocessor import Multiprocessor
from icarus_simulator.structure_definitions import (
    PathData,
    GridPos,
    Pname,
    EdgeData,
    EdgeInfo,
    SatPos,
    Path,
    PathId,
    Edge,
    TempEdgeInfo,
)


class EdgePhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        num_procs: int,
        num_batches: int,
        ed_strat: BaseEdgeStrat,
        paths_in: Pname,
        nw_in: Pname,
        sats_in: Pname,
        grid_in: Pname,
        edges_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.num_procs = num_procs
        self.num_batches = num_batches
        self.ed_strat: BaseEdgeStrat = ed_strat
        self.ins: List[Pname] = [paths_in, nw_in, sats_in, grid_in]
        self.outs: List[Pname] = [edges_out]

    @property
    def input_properties(self) -> List[Pname]:
        return self.ins

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.ed_strat]

    @property
    def name(self) -> str:
        return "Edges"

    def _compute(
        self, path_data: PathData, network: nx.Graph, sat_pos: SatPos, grid_pos: GridPos
    ) -> Tuple[EdgeData]:
        # Isolate all paths to be computed
        all_paths = [
            (pd[0], (pair[0], pair[1], list_id))
            for pair, pd_list in path_data.items()
            for list_id, pd in enumerate(pd_list)
        ]

        # Start a multithreaded computation
        multi = EdgeMultiproc(
            self.num_procs, self.num_batches, all_paths, process_params=(self.ed_strat,)
        )
        edge_infos: Dict[Edge, TempEdgeInfo] = multi.process_batches()

        # Transform to EdgeInfo and add the missing edges
        all_edges = list(network.edges())
        all_edges.extend([(ed[1], ed[0]) for ed in all_edges])
        all_edges.extend([(-1, sat) for sat in sat_pos])
        all_edges.extend([(sat, -1) for sat in sat_pos])
        edge_data = {}
        for ed in all_edges:
            if ed in edge_infos:
                tup = edge_infos[ed]
                edge_data[ed] = EdgeInfo(
                    tup.paths_through,
                    tup.centrality / len(all_paths),
                    sum(grid_pos[gnd].surface for gnd in tup.source_gridpoints),
                )
            else:  # Edge is never touched by the data, add default
                edge_data[ed] = EdgeInfo([], 0.0, 0.0)

        result_tup = (edge_data,)  # Must be a tuple!
        return result_tup

    def _check_result(self, result: Tuple[EdgeData]) -> None:
        return


class EdgeMultiproc(Multiprocessor):
    def _single_sample_process(
        self,
        sample: Tuple[Path, PathId],
        process_result: Dict[Edge, TempEdgeInfo],
        params: Tuple,
    ) -> None:
        path, path_id = sample
        ed_strat: BaseEdgeStrat = params[0]
        ed_strat.compute(process_result, path, path_id)

    @staticmethod
    def _assemble(final_result: Dict, part_result: Dict) -> Dict:
        for val in part_result.values():
            for ed, tup in val.items():
                if ed in final_result:
                    final_result[ed].paths_through.extend(tup.paths_through)
                    final_result[ed].centrality += tup.centrality
                    final_result[ed].source_gridpoints.update(tup.source_gridpoints)
                else:
                    final_result[ed] = tup
        return final_result
