#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Base strategy class for a specific task.
This class is open for custom extension, in order to create different execution strategies for this task.
See BaseStrategy for more details.
"""
import networkx as nx

from abc import abstractmethod

from icarus_simulator.strategies.base_strat import BaseStrat
from icarus_simulator.structure_definitions import GridPos, SdPair, Coverage, LbSet


class BaseRoutingStrat(BaseStrat):
    @abstractmethod
    def compute(
        self, pair: SdPair, grid: GridPos, network: nx.Graph, coverage: Coverage
    ) -> LbSet:
        raise NotImplementedError
