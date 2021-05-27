#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import Tuple, List

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import GridPos


class BaseZoneBuildStrat(BaseStrat):
    @abstractmethod
    def compute(
        self, grid_pos: GridPos, center1: int, center2: int
    ) -> Tuple[List[int], List[int]]:
        raise NotImplementedError
