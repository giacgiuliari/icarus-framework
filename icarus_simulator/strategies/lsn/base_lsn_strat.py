#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
import networkx as nx

from abc import abstractmethod
from typing import Tuple, List

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import SatPos, IslInfo


class BaseLSNStrat(BaseStrat):
    @abstractmethod
    def compute(self) -> Tuple[SatPos, nx.Graph, List[IslInfo]]:
        raise NotImplementedError
