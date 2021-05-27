#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import List, Optional, Tuple

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import (
    PathData,
    Edge,
    DirectionData,
    BwData,
    AtkFlowSet,
)


class BaseFeasStrat(BaseStrat):
    @abstractmethod
    def compute(
        self,
        congest_edges: List[Edge],
        path_data: PathData,
        bw_data: BwData,
        direction_data: DirectionData,
        max_uplink_increase: int,
    ) -> Tuple[Optional[AtkFlowSet], int, int]:
        raise NotImplementedError
