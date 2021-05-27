#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple

from icarus_simulator.structure_definitions import (
    PathData,
    Edge,
    DirectionData,
    BwData,
    AtkFlowSet,
)
from icarus_simulator.strategies.atk_feasibility_check.base_feas_strat import (
    BaseFeasStrat,
)
from icarus_simulator.strategies.base_strat import BaseStrat


class BaseOptimStrat(BaseStrat):
    @abstractmethod
    def compute(
        self,
        congest_edges: List[Edge],
        path_data: PathData,
        bw_data: BwData,
        direction_data: DirectionData,
        uplink_max_val: int,
        feas_strat: BaseFeasStrat,
    ) -> Tuple[Optional[AtkFlowSet], int, int]:
        raise NotImplementedError
