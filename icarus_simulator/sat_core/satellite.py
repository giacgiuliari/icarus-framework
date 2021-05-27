#  2020 Tommaso Ciussani and Giacomo Giuliari


import ephem
import math

from icarus_simulator.sat_core.coordinate_util import GeodeticPosition

from .isl_util import in_orbit_idx_to_sat_idx
from .orbit_util import (
    right_ascension_ascending_node as raan,
    mean_anomaly,
    epoch_offset_to_date,
)


class Satellite:
    """Wrapper for `pyephem`'s `EarthSatellite`."""

    def __init__(
        self,
        sat_idx_in_orbit: int,
        orbit_idx: int,
        num_sat_per_orbit: int,
        num_orbits: int,
        inclination: float,
        epoch: str,
        mean_motion: float,
        orbit_shift: float = 0.0,
        eccentricity: float = 1e-32,
        aug_perigee: float = 0.0,
    ) -> None:
        """
        Args:
            sat_idx_in_orbit: Index of the satellite inside its orbit.
            orbit_idx: Index of the orbit of the satelliite.
            num_sat_per_orbit: Total number of satellites in each orbit of the
                constellation.
            num_orbits: Number of orbits in the constellation.
            inclination: Inclination of the orbits.
            epoch: Starting epoch. Has to be a string formatted as
                with `%Y/%m/%d %H:%M:%S`.
            mean_motion: The mean motion of the satellite. This can be
                computed as a function of the satellite's elevation.
            orbit_shift: Shift of the orbit from the equatorial plane. This
                can be used to create more complex walker-type constellations.
                Defaults to 0.
            eccentricity: Eccentricity of the orbit.
                Defaults to 0.001 (circular orbit).
            aug_perigee: Augmentation of the perigree. Defualts to 0.0
                (circular orbit).
        """

        self.sat_idx_in_orbit = sat_idx_in_orbit
        self.orbit_idx = orbit_idx
        self.num_sat_per_orbit = num_sat_per_orbit
        self.num_orbits = num_orbits
        self.inclination = ephem.degrees(inclination)
        self.epoch = epoch
        self.mean_motion = mean_motion
        self.eccentricity = eccentricity
        self.aug_perigee = aug_perigee
        # Compute the derived parameters
        # TODO: maybe move the computation of these parameters outside the
        #   Satellite class to make it more general.
        self.sat_idx = in_orbit_idx_to_sat_idx(
            self.sat_idx_in_orbit, self.orbit_idx, self.num_sat_per_orbit
        )
        self.raan = raan(self.orbit_idx, num_orbits)
        self.mean_anomaly = mean_anomaly(
            self.sat_idx_in_orbit, num_sat_per_orbit, orbit_shift
        )
        # Create the satellite object
        self.sat = ephem.EarthSatellite()
        self.sat._epoch = self.epoch
        self.sat._e = self.eccentricity
        self.sat._raan = self.raan
        self.sat._M = self.mean_anomaly
        self.sat._inc = self.inclination
        self.sat._ap = self.aug_perigee
        self.sat._n = mean_motion

    def position_at_time(self, timestr: str) -> GeodeticPosition:
        """
        Compute the position of the satellite at a certain time.
        Args:
            timestr: Time for which to compute the position
        Returns:
            SatPosition: The {lat, long, elevation} of the satellite at the
                required time.
        """
        self.sat.compute(timestr)
        return self.get_lat_long_elev()

    def position_at_epoch_offset(
        self, hours: int = 0, minutes: int = 0, seconds: int = 0, millisecs: int = 0
    ) -> GeodeticPosition:
        """
        Compute the position of the satellite given an offset from epoch.
        Args:
            hours: Offset hours.
            minutes: Offset minutes.
            seconds: Offset seconds.
            millisecs: Offset milliseconds
        Returns:
            SatPosition: The {lat, long, elevation} of the satellite at the
                required time.
        """
        target_date_str = epoch_offset_to_date(
            self.epoch, hours, minutes, seconds, millisecs
        )
        return self.position_at_time(target_date_str)

    def get_lat_long_elev(self) -> GeodeticPosition:
        """
        Get the lat, long and elev for the satellite.
        Returns:
            Position of the satellite
        The values are for the last position computed with `position_at_time` or
        `position_at_epoch_offset`.
        """
        lat = math.degrees(self.sat.sublat)
        long = math.degrees(self.sat.sublong)
        elev = self.sat.elevation
        return {"lat": lat, "lon": long, "elev": elev}

    def sat_position_tostring(self) -> str:
        """Get a string with index and position information."""
        lat, long, elev = self.get_lat_long_elev()
        return (
            f"{self.sat_idx} {self.orbit_idx} {self.sat_idx_in_orbit} "
            f"{lat} {long} {elev}"
        )


if __name__ == "__main__":
    raise RuntimeError()
