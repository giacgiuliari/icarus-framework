#  2020 Tommaso Ciussani and Giacomo Giuliari


from typing import Tuple

import numpy as np
from scipy.spatial.distance import euclidean

from .coordinate_util import GeodeticPosition, geo2cart
from .planetary_const import *


def compute_link_length(sat1: GeodeticPosition, sat2: GeodeticPosition) -> float:
    """
    Compute the length of an Inter-Satellite Link
    Args:
        sat1: Position of the first satellite
        sat2:Position of the second satellite
    Returns:
        Euclidean distance between the points
    """
    cart1 = geo2cart(sat1)
    cart2 = geo2cart(sat2)
    return euclidean(cart1, cart2)


def get_sat_by_offset(
    sat_idx_in_orbit: int,
    orbit_idx: int,
    sat_idx_offset: int,
    orbit_offset: int,
    num_sat_per_orbit: int,
    num_orbits: int,
    max_shift: float = 0,
) -> Tuple[int, int, int]:
    """Compute the indexes of the neighbor satellite given by the offset.

    Args:
        sat_idx_in_orbit: Index of the satellite inside its orbit.
        orbit_idx: Index of the orbit of the satelliite.
        sat_idx_offset: In-orbit offset of the index of the neighboring
            satellite from `sat_idx_in_orbit`.
        orbit_offset: Orbit index offset of the neighboring satellite from the
            orbit of the current satellite `orbit_idx`.
        num_sat_per_orbit: Total number of satellites in each orbit of the
                constellation.
        num_orbits: Number of orbits in the constellation.
        max_shift: Maximum shift introduced by OrbitShiftAlgo or other means.
            This is needed to fix the problems with the shift at the seam.

    Returns:
        Tuple[int, int, int]: The indices of the neighboring satellite obtained
            that is offset from the current. The indices are
            `sat_idx, sat_idx_in_orbit, orbit_idx`
    """
    assert not (sat_idx_offset == 0 and orbit_offset == 0)
    walker_shift_in_orbit = 0
    if orbit_idx == (num_orbits - 1) and orbit_offset > 0:
        # This satellite is west of the seam
        inter_sat = 360 / num_sat_per_orbit
        walker_shift_in_orbit = np.ceil(max_shift / inter_sat)
    # Get the index of the satellite in the orbit, eventually making up for the walker shift
    neigh_idx_in_orbit = (
        sat_idx_in_orbit + sat_idx_offset + walker_shift_in_orbit
    ) % num_sat_per_orbit
    # Get the orbit index
    neigh_orbit_idx = (orbit_idx + orbit_offset) % num_orbits
    neigh_idx = in_orbit_idx_to_sat_idx(
        neigh_idx_in_orbit, neigh_orbit_idx, num_sat_per_orbit
    )
    neigh_idx = int(neigh_idx)
    return neigh_idx, neigh_idx_in_orbit, neigh_orbit_idx


def sat_idx_to_in_orbit_idx(sat_idx: int, num_sat_per_orbit: int) -> Tuple[int, int]:
    """
    Compute the satellite index in orbit and orbit index.
    Starting from the satellite index in the constellation.
    Args:
        sat_idx: Index of the satellite in the constellation.
        num_sat_per_orbit: Total number of satellites in each orbit of the
            constellation.
    Returns:
        (int, int): Index of the satellite inside its orbit, index of the
            satellite's orbit.
    """
    if num_sat_per_orbit < 1:
        raise ValueError
    sat_idx_in_orbit = sat_idx % num_sat_per_orbit
    orbit_idx = sat_idx // num_sat_per_orbit
    return sat_idx_in_orbit, orbit_idx


def in_orbit_idx_to_sat_idx(
    sat_idx_in_orbit: int, orbit_idx: int, num_sat_per_orbit: int
) -> int:
    """Compute the satellite index in the constellation.
     Starting from from the satellite index in the orbit and orbit index.
    Args:
        sat_idx_in_orbit: Index of the satellite inside its orbit.
        orbit_idx: Index of the satellite's orbit.
        num_sat_per_orbit: Total number of satellites in each orbit of the
            constellation.
    Returns:
        int: Index of the satellite in the constellation.
    """
    if sat_idx_in_orbit >= num_sat_per_orbit:
        raise ValueError(
            "Satellite index in orbit cannot be greater than "
            "the number of satellites per orbit"
        )
    base_idx = orbit_idx * num_sat_per_orbit
    sat_idx = base_idx + sat_idx_in_orbit
    return sat_idx


def max_ground_sat_dist(h: float, min_angle: float) -> float:
    """
    Compute the maximum sat-ground distance given a minimum angle.
        Uses the law of sines.
        In the computation:
            alpha: angle at the GST, pointing SAT and CENTER.
            beta: angle at the SAT, pointing GST and CENTER.
            gamma: angle at GENTER, pointing at GST and SAT.
            (sides are relative).
    Args:
        h: Elevation of the satellite in meters.
        min_angle: Minimum elevation angle at the GST, from the horizon and
            pointing to the satellite.
    Returns: float: the maximum distance GST-SAT.
    """
    alpha = np.deg2rad(min_angle + 90)
    a = h + EARTH_RADIUS
    b = EARTH_RADIUS
    sin_beta = np.sin(alpha) / a * b
    beta = np.arcsin(sin_beta)
    gamma = np.pi - alpha - beta
    c = a * np.sin(gamma) / np.sin(alpha)
    # arc = EARTH_RADIUS * gamma
    return c
