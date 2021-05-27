#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import Tuple, List

from icarus_simulator.strategies.grid.base_grid_strat import BaseGridStrat
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.strategies.grid_weight.base_weight_strat import BaseWeightStrat
from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.structure_definitions import GridPos, Pname


class GridPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        grid_strat: BaseGridStrat,
        weight_strat: BaseWeightStrat,
        grid_out: Pname,
        size_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.grid_strat: BaseGridStrat = grid_strat
        self.weight_strat: BaseWeightStrat = weight_strat
        self.outs: List[Pname] = [grid_out, size_out]

    @property
    def input_properties(self) -> List[Pname]:
        return []

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.grid_strat, self.weight_strat]

    @property
    def name(self) -> str:
        return "Grid"

    def _compute(self) -> Tuple[GridPos, int]:
        grid_pos = self.grid_strat.compute()
        full_len = len(grid_pos)
        grid_pos = self.weight_strat.compute(grid_pos)
        return grid_pos, full_len

    def _check_result(self, result: Tuple[GridPos, int]) -> None:
        gp, full_length = result
        for idx in [0, 1]:
            if idx in gp:
                gp[full_length + idx] = gp[idx]
                del gp[idx]

        for idx in gp:
            assert idx > 1
        return
