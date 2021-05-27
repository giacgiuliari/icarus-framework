#  2020 Tommaso Ciussani and Giacomo Giuliari


"""
This file contains the type definitions and conversions between coordinate schemes.
All length values in m
"""
import numpy as np
from typing import Tuple
from typing_extensions import TypedDict

from icarus_simulator.sat_core.planetary_const import EARTH_RADIUS


class GeodeticPosition(TypedDict):
    lat: float
    lon: float
    elev: float  # Elevation wrt Earth surface, NOT Earth center!


class CartesianPosition(TypedDict):
    x: float
    y: float
    z: float


CartCoords = Tuple[float, float, float]


def geo2cart(geo_coord: GeodeticPosition) -> CartCoords:
    """
    Converts a {lat, long, elevation} point to cartesian (x, y, z).
    Args:
        geo_coord: SatPosition. Coordinates of the point in geodesic format.

    Returns:
        Tuple[float, float, float]: Tuple of cartesian coordinates.
    """
    theta = np.deg2rad(geo_coord["lon"])
    phi = np.deg2rad(90 - geo_coord["lat"])
    r = geo_coord["elev"] + EARTH_RADIUS
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)
    cart = (x, y, z)
    rad = np.sqrt(np.sum(np.square(cart)))

    assert rad >= EARTH_RADIUS - 1000  # Allow for approximation error
    return cart
