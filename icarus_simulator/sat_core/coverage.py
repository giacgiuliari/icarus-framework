#  2020 Tommaso Ciussani and Giacomo Giuliari


from typing import Dict, Tuple
import pandas as pd
import networkx as nx
import numpy as np
from sklearn.neighbors import KDTree

from .coordinate_util import GeodeticPosition, geo2cart
from .isl_util import max_ground_sat_dist, compute_link_length

WUP_CITIES = "data/WUP2018-F22-Cities_Over_300K_Annual.csv"


def in_reach(
    pos1: GeodeticPosition, pos2: GeodeticPosition, max_dist: float
) -> Tuple[bool, float]:
    """
    Check if two objects are within reach.
    Args:
        pos1: The first position
        pos2: The second position
        max_dist: The maximum distance considered for being in reach
    Returns:
        bool: positions are in reach wrt each other, float: distance
    """
    dist = compute_link_length(pos1, pos2)
    is_in_reach = dist < max_dist
    return is_in_reach, dist


def load_big_cities(filename: str = WUP_CITIES) -> Dict[int, GeodeticPosition]:
    """Load the biggest cities from the WUP dataset."""
    df = pd.read_csv(filename)
    df = df.rename(
        columns={
            "Latitude": "lat",
            "Longitude": "lon",
            "Urban Agglomeration": "name",
            "2020": "population",
        }
    )
    df = df[["lat", "lon", "name", "population"]]
    dfdict = df.to_dict("records")
    cities = {}
    idx = 0
    for value in dfdict:
        if value["lat"] < 57:
            value["elev"] = 0
            cities[idx] = value
            idx += 1
    return cities


def add_cities_to_graph(G: nx.Graph, coverage: Dict[int, Dict[int, float]]):
    """
    Adds the GSLs to a satellite network graph.
    City indices are prepended with `c `. E.g., city 24 is node 'c 24' in the graph.
    """
    for city in coverage:
        for dst_sat in coverage[city]:
            G.add_edge(f"c {city}", dst_sat, length=coverage[city][dst_sat])
    return G


def positions_satellite_coverage(
    grid_pos: Dict[int, GeodeticPosition],
    sat_pos: Dict[int, GeodeticPosition],
    min_elev_angle: int,
) -> Dict[int, Dict[int, float]]:
    """
    Check the satellite coverage for positions on Earth.
    Coverage is defined as all the satellites that are reachable with a
    line-of-sight path of length smaller than `max_dist`.
    Args:
    pos: Dict of indexed Positions. Positions of the points in the ground grid
    sat_pos: Dict of indexed Satpositions. Positions of the satellites
    elevation: Elevation of the satellites
    min_elev_angle: Minimum elevation angle of the satellites

    Returns: All the distances {ground_idx:{sat_idx: dist}}
    """
    all_dist = {idx: {} for idx in grid_pos}
    # The dictionary format we use conflicts with this algorithm's format -> index map
    # Put grid points into a KD-tree
    index, id_map, grid_cart = 0, {}, np.zeros((len(grid_pos), 3))
    for grid_id in grid_pos:
        id_map[index] = grid_id  # map indices to sat indices
        grid_cart[index] = geo2cart(grid_pos[grid_id])
        index += 1
    kd = KDTree(grid_cart)

    # Query all the satellites using the max_dist
    for sat_idx, sat in sat_pos.items():
        max_dist = max_ground_sat_dist(sat["elev"], min_elev_angle)
        covered_grid_ids, distances = kd.query_radius(
            [geo2cart(sat)], r=max_dist, count_only=False, return_distance=True
        )
        covered_grid_ids = covered_grid_ids[0]
        distances = distances[0]
        # Convert all the indices back
        for i in range(len(distances)):
            grid_idx = id_map[covered_grid_ids[i]]
            all_dist[grid_idx][sat_idx] = distances[i]
    return all_dist
