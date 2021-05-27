#  2020 Tommaso Ciussani and Giacomo Giuliari
from math import ceil
from typing import List, Optional, Tuple

from icarus_simulator.strategies.atk_detect_optimisation.base_optim_strat import (
    BaseOptimStrat,
)
from icarus_simulator.strategies.atk_feasibility_check.base_feas_strat import (
    BaseFeasStrat,
)
from icarus_simulator.structure_definitions import (
    Edge,
    PathData,
    DirectionData,
    BwData,
    AtkFlowSet,
)


class BinSearchOptimStrat(BaseOptimStrat):
    def __init__(self, rate: float, **kwargs):
        super().__init__()
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection
        assert 0.0 <= rate <= 1.0
        self.rate = rate

    @property
    def name(self) -> str:
        return "bin"

    @property
    def param_description(self) -> str:
        return f"{self.rate}"

    def compute(
        self,
        congest_edges: List[Edge],
        path_data: PathData,
        bw_data: BwData,
        direction_data: DirectionData,
        uplink_max_val: int,
        feas_strat: BaseFeasStrat,
    ) -> Tuple[Optional[AtkFlowSet], int, int]:

        # If the rate is 0, no optimisation is required
        if self.rate == 0.0:
            return feas_strat.compute(
                congest_edges, path_data, bw_data, direction_data, uplink_max_val
            )

        # Start a binary search algorithm to find the lowest increase constraint st the problem is feasible
        # Idea: left always infeasible, right always feasible, right is INCLUSIVE
        left, right = 0, uplink_max_val
        final_val = uplink_max_val
        while left != right - 1:
            half = left + int(ceil((right - left) / 2))
            temp_atk_flow_set, _, _ = feas_strat.compute(
                congest_edges, path_data, bw_data, direction_data, half
            )
            if temp_atk_flow_set is not None:  # If optimal
                final_val = half
                right = half
            else:  # If infeasible
                left = half

        # Based on the optimisation rate chosen, re-run for the correct value
        val_range = uplink_max_val - final_val
        val_incr = int(
            self.rate * val_range
        )  # Taking floor here ensures that ceil is taken in next line
        req_detect = uplink_max_val - val_incr
        return feas_strat.compute(
            congest_edges, path_data, bw_data, direction_data, req_detect
        )
