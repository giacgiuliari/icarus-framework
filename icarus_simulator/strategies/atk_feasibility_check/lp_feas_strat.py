#  2020 Tommaso Ciussani and Giacomo Giuliari
import numpy as np
from math import ceil
from typing import List, Optional, Tuple

from icarus_simulator.strategies.atk_feasibility_check.base_feas_strat import (
    BaseFeasStrat,
)
from icarus_simulator.structure_definitions import (
    Edge,
    PathData,
    DirectionData,
    BwData,
    AtkFlowSet,
    PathEdgeData,
)
from icarus_simulator.utils import get_edges


class LPFeasStrat(BaseFeasStrat):
    def __init__(self, **kwargs):
        super().__init__()
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "lp"

    @property
    def param_description(self) -> None:
        return None

    # Important note: this only works for single-target attacks!
    def compute(
        self,
        congest_edges: List[Edge],
        path_data: PathData,
        bw_data: BwData,
        direction_data: DirectionData,
        max_uplink_increase: int,
    ) -> Tuple[Optional[AtkFlowSet], int, int]:

        directions = list(direction_data.keys())

        if len(directions) == 0:
            return None, -1, -1

        # Go through the edges and find out their coverage and their max bw
        # IMPORTANT: take the sum of variables as total bw, and as objective, to avoid having pass-through directions
        # counted two times
        direction_edges: PathEdgeData = {}
        tot_needed = 0
        for idx, p in enumerate(directions):
            for ed in get_edges(p):
                if ed not in direction_edges and ed not in congest_edges:
                    direction_edges[ed] = set()
                elif ed not in direction_edges and ed in congest_edges:
                    tot_needed += bw_data[ed].get_remaining_bw()
                    direction_edges[ed] = set()
                direction_edges[ed].add(idx)

        # Formulate the linear program
        # The variables are the bw in flows assigned to each direction, the constraints are the bw limitations of edges
        # In each row of the constraint matrix, the index to the corresponding path will be set to 1

        # Matrix for leq inequalities
        # Num of columns is number of directions, so len(directions)
        # Num of rows is complicated:
        #  - each path gets a constraint for bw >= 0                           len(directions)
        #  - each edge gets a constraint for bw <= cap                         len(direction_edges)
        #  - each congest edge gets an additional constr to make equality      len(congest_edges)
        # We need to track where each uplink edge is in the matrix in order to update the constraints
        num_rows = len(direction_edges) + len(congest_edges)
        numpy_g = np.zeros((num_rows, len(directions)))
        numpy_h = np.zeros(num_rows)
        numpy_c = np.ones(len(directions))

        curr_row = 0
        # All edges need the less-than constraint
        for e in direction_edges:
            if e[0] == -1:
                numpy_h[curr_row] = min(
                    bw_data[e].get_remaining_bw(), max_uplink_increase
                )
            else:
                numpy_h[curr_row] = bw_data[e].get_remaining_bw()
            for j in direction_edges[e]:
                numpy_g[curr_row, j] = 1.0
            curr_row += 1

        # Congest edges also need the greater-than constraint -> invert sign!
        for e in congest_edges:
            if e[0] == -1:
                numpy_h[curr_row] = -min(
                    bw_data[e].get_remaining_bw(), max_uplink_increase
                )
            else:
                numpy_h[curr_row] = -bw_data[e].get_remaining_bw()
            for j in direction_edges[e]:
                numpy_g[curr_row, j] = -1.0
            curr_row += 1

        # Prepare Gurobi problem -> we import gurobi here as not everybody may habve it installed!
        import gurobipy as gp
        from gurobipy import GRB

        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        m = gp.Model("attack", env=env)
        x = m.addMVar(shape=len(directions), lb=0.0, name="x")
        m.setObjective(numpy_c @ x, GRB.MINIMIZE)  # @ is matrix product!
        # noinspection PyArgumentList
        m.addConstr(numpy_g @ x <= numpy_h, name="c")
        m.optimize()

        if m.status != GRB.OPTIMAL:  # LP not feasible, attack not possible!
            return None, -1, -1

        # Gather info about the amount of flow each direction sends
        lp_vars, directions_bw, edges_bw = m.getVars(), {}, {}
        for i in range(len(directions)):
            # Get the value of the variable
            val = int(lp_vars[i].x)
            if val > 0:
                directions_bw[directions[i]] = val
                for ed in get_edges(directions[i]):
                    if ed not in edges_bw:
                        edges_bw[ed] = 0
                    edges_bw[ed] += val

        # Find a conformant atkflowset, distribute each direction equally among the originating pairs
        atk_flow_set = set()
        for dire, bw in directions_bw.items():
            tot_pairs = len(direction_data[dire])
            flows_per_pair = max(
                5, int(ceil(bw / tot_pairs))
            )  # Enforce a min of 5 per pair for attack efficiency
            for pair in direction_data[dire]:
                if bw == 0:
                    break
                flows = min(flows_per_pair, bw)
                atk_flow_set.add((pair, flows))
                bw -= flows

        return (
            atk_flow_set,
            tot_needed,
            max(edges_bw[ed] for ed in edges_bw if ed[0] == -1),
        )
