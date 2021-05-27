#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import List

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import PathData, EdgeData, BwData, PathId


class BaseBwAssignStrat(BaseStrat):
    @abstractmethod
    def compute(
        self, path_data: PathData, path_list: List[PathId], edge_data: EdgeData
    ) -> BwData:
        raise NotImplementedError
