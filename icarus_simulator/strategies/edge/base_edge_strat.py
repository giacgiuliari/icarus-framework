#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
from abc import abstractmethod
from typing import Dict

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import Edge, TempEdgeInfo, Path, PathId


class BaseEdgeStrat(BaseStrat):
    @abstractmethod  # Side effects on temp_edge_data are produced
    def compute(
        self, temp_edge_data: Dict[Edge, TempEdgeInfo], path: Path, path_id: PathId
    ) -> None:
        raise NotImplementedError
