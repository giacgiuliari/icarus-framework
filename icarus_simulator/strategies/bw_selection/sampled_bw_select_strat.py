#  2020 Tommaso Ciussani and Giacomo Giuliari
import random
from typing import List

from icarus_simulator.strategies.bw_selection.base_bw_select_strat import (
    BaseBwSelectStrat,
)
from icarus_simulator.structure_definitions import GridPos, PathData, PathId
from icarus_simulator.utils import get_ordered_idx


# Computes a sampled traffic matrix. IMPORTANT: this strategy assumes that all paths are symmetrical, and path_data
# only stores the ordered pairs for space and performance reasons.
class SampledBwSelectStrat(BaseBwSelectStrat):
    def __init__(self, sampled_quanta: int, **kwargs):
        super().__init__()
        self.sampled_quanta = sampled_quanta
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "samp"

    @property
    def param_description(self) -> str:
        return f"{self.sampled_quanta}"

    def compute(self, grid_pos: GridPos, path_data: PathData) -> List[PathId]:
        random.seed("ETHZ")
        # Sample communication pairs
        samples = random.choices(
            list(grid_pos.keys()),
            [val.weight for val in grid_pos.values()],
            k=self.sampled_quanta * 2,
        )
        # If the pair exists, sample a suitable path
        path_ids = []
        for i in range(0, self.sampled_quanta * 2, 2):
            ord_sample = get_ordered_idx((samples[i], samples[i + 1]))[0]
            # If the sample is not in the paths, or there is no path between the pair, the sample is dropped
            if ord_sample not in path_data or len(path_data[ord_sample]) == 0:
                continue
            lbset_size = len(path_data[ord_sample])
            id_in_lbset = random.randrange(0, lbset_size)
            path_ids.append((ord_sample[0], ord_sample[1], id_in_lbset))
        return path_ids
