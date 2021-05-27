#  2020 Tommaso Ciussani and Giacomo Giuliari

"""
This file introduces the special mechanism of the configuration file.
The dictionary CONFIG includes entries with all the strategies used in the current simulation definition.
Each entry contains the parameters passed, by name, to the strategy constructors, in a list format.
If you wish to run multiple simulations, you can add the needed parameters to the corresponding list, and the script
will automatically create new instances of the configuration by extending the last elements of all other lists.
For example, setting CONFIG['lsn']['orbits'] = [72, 50] will run two identical simulations, except for this parameter.
If you change a strategy class across simulations, just put the union of all parameters needed. At runtime, unneeded
parameters will be automatically discarded by the different strategy classes.

Running simulations with this method is NOT mandatory, phases can be configured manually every time.
"""
from typing import List, Dict
from icarus_simulator.strategies import *

CONFIG = {
    "lsn": {
        "strat": [ManhLSNStrat],
        "inclination": [53],
        "sats_per_orbit": [22],
        "orbits": [72],
        "f": [11],
        "elevation": [550000],
        "hrs": [0],
        "mins": [2],
        "secs": [17],  # list(range(0, 130))
        "millis": [0],
        "epoch": ["2020/01/01 00:00:00"],
    },
    "grid": {"strat": [GeodesicGridStrat], "repeats": [22]},
    "gweight": {"strat": [GDPWeightStrat], "dataset_file": [None]},
    "cover": {"strat": [AngleCovStrat], "min_elev_angle": [40]},
    "rout": {
        "strat": [SSPRoutStrat],
        "desirability_stretch": [2.3],
        "k": [5],
        "esx_theta": [0.5],
    },
    "edges": {"strat": [BidirEdgeStrat]},
    "bw_sel": {"strat": [SampledBwSelectStrat], "sampled_quanta": [250000]},
    "bw_asg": {
        "strat": [BidirBwAssignStrat],
        "isl_bw": [2000],
        "udl_bw": [400],
        "utilisation": [0.9],
    },
    "atk_constr": {
        "strat": [NoConstrStrat],
        "geo_names": [["USA", "RUS"]],
        "grid_points": [[1549, 1530]],
    },
    "atk_filt": {"strat": [DirectionalFilteringStrat]},
    "atk_feas": {
        "strat": [LPFeasStrat],
    },
    "atk_optim": {"strat": [BinSearchOptimStrat], "rate": [1.0]},
    "zone_select": {"strat": [RandZoneStrat], "samples": [5000]},
    "zone_build": {"strat": [KclosestZoneStrat], "size": [6]},
    "zone_edges": {
        "strat": [ISLZoneStrat],
    },
    "zone_bneck": {
        "strat": [DetectBneckStrat],
    },
}


# Here follow methods used for the parsing.
def parse_config(config_lists) -> List[Dict]:
    """ Parse the configuration """
    # Parse the base elements
    # Get a list of all the lists and determine the longest
    full_config = []
    keys = config_lists.keys()
    base_list = []
    for key in keys:
        base_list.extend(list(config_lists[key].values()))
    num_runs = len(max(base_list, key=lambda k: len(k)))

    # Extend all the lists
    for key in keys:
        for inner_key, val in config_lists[key].items():
            val.extend([val[-1]] * (num_runs - (len(val))))

    # Turn lists in dict of dicts
    for idx in range(num_runs):
        run = {}
        for key in keys:
            run[key] = [
                dict(zip(config_lists[key], t))
                for t in zip(*config_lists[key].values())
            ][idx]
        full_config.append(run)
    return full_config


def get_strat(strat_id: str, conf: Dict):
    return conf[strat_id]["strat"](**conf[strat_id])
