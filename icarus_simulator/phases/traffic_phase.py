#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import List, Tuple

from icarus_simulator.phases.base_phase import BasePhase
from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.strategies.bw_selection.base_bw_select_strat import (
    BaseBwSelectStrat,
)
from icarus_simulator.strategies.bw_assignment.base_bw_assig_strat import (
    BaseBwAssignStrat,
)
from icarus_simulator.structure_definitions import (
    GridPos,
    Pname,
    BwData,
    PathData,
    EdgeData,
)


class TrafficPhase(BasePhase):
    def __init__(
        self,
        read_persist: bool,
        persist: bool,
        select_strat: BaseBwSelectStrat,
        assign_strat: BaseBwAssignStrat,
        grid_in: Pname,
        paths_in: Pname,
        edges_in: Pname,
        bw_out: Pname,
    ):
        super().__init__(read_persist, persist)
        self.select_strat: BaseBwSelectStrat = select_strat
        self.assign_strat: BaseBwAssignStrat = assign_strat
        self.ins: List[Pname] = [grid_in, paths_in, edges_in]
        self.outs: List[Pname] = [bw_out]

    @property
    def input_properties(self) -> List[Pname]:
        return self.ins

    @property
    def output_properties(self) -> List[Pname]:
        return self.outs

    @property
    def _strategies(self) -> List[BaseStrat]:
        return [self.select_strat, self.assign_strat]

    @property
    def name(self) -> str:
        return "Bw"

    def _compute(
        self, grid_pos: GridPos, path_data: PathData, edge_data: EdgeData
    ) -> Tuple[BwData]:
        # Let the selection strategy choose a list of paths to allocate in order
        # Each path in the list bears one single data quantum
        chosen_paths = self.select_strat.compute(grid_pos, path_data)

        # Assign the paths sequentially
        bw_data = self.assign_strat.compute(path_data, chosen_paths, edge_data)
        return (bw_data,)

    def _check_result(self, result: Tuple[BwData]) -> None:
        bw_data = result[0]
        for bd in bw_data.values():
            assert bd.idle_bw <= bd.capacity
        return
