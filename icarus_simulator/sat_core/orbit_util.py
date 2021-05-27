#  2020 Tommaso Ciussani and Giacomo Giuliari

from datetime import datetime, timedelta

import ephem
import numpy as np

from .planetary_const import *


def right_ascension_ascending_node(orbit_idx: int, num_orbits: int) -> ephem.Angle:
    """Compute the right ascension of the ascending node (raan).

    Args:
        orbit_idx: Index of the orbit for which the raan is computed.
        num_orbits: Number of orbits in the constellation.

    Returns:
        ephem.Angle: The raan in degrees.
    """
    if num_orbits < 1:
        raise ValueError
    raan = float(orbit_idx * 360 / num_orbits)
    raan = ephem.degrees(raan)
    return raan


def mean_anomaly(
    sat_idx_in_orbit: int, num_sat_per_orbit: int, orbit_shift: float = 0.0
) -> ephem.Angle:
    """Compute the mean anomaly for the current satellite.

    Args:
        sat_idx_in_orbit: Index of the satellite inside its orbit.
        num_sat_per_orbit: Total number of satellites in each orbit of the
            constellation.
        orbit_shift: Shift of the orbit from the equatorial plane. This
            can be used to create more complex walker-type constellations.

    Returns:
        ephem.Angle: The mean anomaly for the current satellite.
    """
    if num_sat_per_orbit < 1:
        raise ValueError
    ma = orbit_shift + sat_idx_in_orbit * 360 / num_sat_per_orbit
    ma = ephem.degrees(ma)
    return ma


def elevation_to_period(elevation: float) -> float:
    """Compute the period of an orbit in seconds.

    Returns:
        float: The orbital period of a satellite at the given elevation in
            seconds.
    """
    assert elevation > 0
    elevation = float(elevation)
    radius = elevation + EARTH_RADIUS
    period = 2 * np.pi * np.sqrt(np.power(radius, 3) / MU)
    return period


def elevation_to_mean_motion(elevation: float, unit: str = "revs") -> float:
    """Compute the mean motion of the satellite given its elevation.

    Args:
        elevation: The elevation of the satellite, in meters from sea level.
        unit: The unit in which to compute the mean motion. Can be either
            "radians", "degrees", or "revs" for revolutions.
    Returns:
        float: The mean motion of a satellite orbiting at the given elevation.
            The measure is `unit / day`.
    """
    # Get the period in days
    period = elevation_to_period(elevation) / SEC_IN_DAY
    if unit == "radians":
        return 2 * np.pi / period
    elif unit == "degrees":
        return 360 / period
    elif unit == "revs":
        return 1 / period
    else:
        raise ValueError("Specify a valid unit for mean motion")


def epoch_offset_to_date(
    epoch: str, hours: int = 0, minutes: int = 0, seconds: int = 0, millisecs: int = 0
) -> ephem.Date:
    """Compute the date obtained by adding an offset to epoch."""
    epoch_datetime = datetime.strptime(epoch, "%Y/%m/%d %H:%M:%S")
    delta = timedelta(
        hours=hours, minutes=minutes, seconds=seconds, milliseconds=millisecs
    )
    target = epoch_datetime + delta
    targetstr = target.strftime("%Y/%m/%d %H:%M:%S.%f")
    return targetstr
