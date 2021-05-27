#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import List, Tuple

from icarus_simulator.strategies.coverage.base_coverage_strat import BaseCoverageStrat
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.structure_definitions import SatPos, GridPos, Coverage, Pname


class CoveragePhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        cov_strat: BaseCoverageStrat,
        grid_in: Pname,
        sat_in: Pname,
        grid_out: Pname,
        cov_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.cov_strat: BaseCoverageStrat = cov_strat
        self.ins: List[Pname] = [grid_in, sat_in]
        self.outs: List[Pname] = [grid_out, cov_out]

    @property
    def input_properties(self) -> List[Pname]:
        return self.ins

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.cov_strat]

    @property
    def name(self) -> str:
        return "Cover"

    def _compute(self, grid_pos: GridPos, sat_pos: SatPos) -> Tuple[GridPos, Coverage]:
        # Compute the coverage
        coverage = self.cov_strat.compute(grid_pos, sat_pos)
        # Optimise coverage and grid by removing the uncovered points
        gplen = len(grid_pos)
        uncovered_gnds = [gnd for gnd in coverage if len(coverage[gnd].keys()) == 0]
        for gnd in uncovered_gnds:
            del coverage[gnd]
            del grid_pos[gnd]
        print(f"Earth grid size reduced from {gplen} to {len(grid_pos)}")
        return grid_pos, coverage

    def _check_result(self, result) -> None:  # No check
        return
