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
    BwData,
    AttackData,
    PathEdgeData,
    Edge,
)


class BaseZoneBneckStrat(BaseStrat):
    @abstractmethod
    def compute(
        self,
        bw_data: BwData,
        atk_data: AttackData,
        path_edges: PathEdgeData,
        tot_cross_zone_paths: int,
    ) -> List[List[Edge]]:
        raise NotImplementedError
