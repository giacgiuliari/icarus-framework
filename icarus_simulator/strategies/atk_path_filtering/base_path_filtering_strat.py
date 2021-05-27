#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import List

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import (
    PathData,
    Edge,
    EdgeData,
    DirectionData,
)


class BasePathFilteringStrat(BaseStrat):
    @abstractmethod
    def compute(
        self,
        edges: List[Edge],
        edge_data: EdgeData,
        path_data: PathData,
        allowed_sources: List[int],
    ) -> DirectionData:
        raise NotImplementedError
