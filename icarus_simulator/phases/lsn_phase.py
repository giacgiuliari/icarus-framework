#  2020 Tommaso Ciussani and Giacomo Giuliari

import networkx as nx
from typing import Tuple, List

from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.strategies.lsn.base_lsn_strat import BaseLSNStrat
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import SatPos, Pname, IslInfo


class LSNPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        lsn_strat: BaseLSNStrat,
        lsn_out: Pname,
        nw_out: Pname,
        isls_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.lsn_strat = lsn_strat
        self.outs: List[Pname] = [lsn_out, nw_out, isls_out]

    @property
    def input_properties(self) -> List[Pname]:
        return []

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.lsn_strat]

    @property
    def name(self) -> str:
        return "LSN"

    def _compute(self) -> Tuple[SatPos, nx.Graph, List[IslInfo]]:
        # Call the strategy to generate the network
        sat_pos, nw, isls = self.lsn_strat.compute()
        return sat_pos, nw, isls

    def _check_result(self, result) -> None:  # No checks to be performed
        return
