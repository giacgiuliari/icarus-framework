#  2020 Tommaso Ciussani and Giacomo Giuliari

from typing import Dict, List

import numpy as np

from .orbit_shift_algo import OrbitShiftAlgo
from .orbit_util import elevation_to_mean_motion, epoch_offset_to_date
from .satellite import Satellite
from icarus_simulator.sat_core.coordinate_util import GeodeticPosition


class Constellation:
    """Class representation of a constellation.

    A constellation is a set of satellites on pre-defined orbits.
    """

    def __init__(
        self,
        num_sat_per_orbit: int,
        num_orbits: int,
        inclination: float,
        epoch: str,
        mean_motion: float = None,
        elevation: float = None,
        orbit_shift_algo: OrbitShiftAlgo = None,
        eccentricity: float = 1e-32,
        aug_perigee: float = 0.0,
    ) -> None:
        self.num_sat_per_orbit = num_sat_per_orbit
        self.num_orbits = num_orbits
        self.inclination = inclination
        self.epoch = epoch
        self.orbit_shift_algo = orbit_shift_algo
        self.eccentricity = eccentricity
        self.aug_perigee = aug_perigee
        # Check agreement between mean motion and elevation if specified
        if mean_motion is None and elevation is None:
            raise ValueError("Either mean_motion or elevation must be given.")
        if elevation is not None:
            self.elevation = elevation
            conv_mean_motion = elevation_to_mean_motion(elevation)
            if mean_motion is not None:
                assert np.isclose(mean_motion, conv_mean_motion)
            mean_motion = conv_mean_motion
        self.mean_motion = mean_motion
        # Satellite store
        self.satellites: Dict[int, Satellite] = {}

    def create_constellation(self):
        """Create the constellation, loading all the satellites.

        This has to be called once before calling other methods.
        """
        for orbit_idx in range(self.num_orbits):
            for in_orbit_idx in range(self.num_sat_per_orbit):
                cur_orbit_shift = self.orbit_shift_algo.get_shift(orbit_idx)
                cur_sat = Satellite(
                    sat_idx_in_orbit=in_orbit_idx,
                    orbit_idx=orbit_idx,
                    num_sat_per_orbit=self.num_sat_per_orbit,
                    num_orbits=self.num_orbits,
                    inclination=self.inclination,
                    epoch=self.epoch,
                    mean_motion=self.mean_motion,
                    orbit_shift=cur_orbit_shift,
                    eccentricity=self.eccentricity,
                    aug_perigee=self.aug_perigee,
                )
                self.satellites[cur_sat.sat_idx] = cur_sat

    def compute_positions_at_time(self, timestr: str) -> Dict[int, GeodeticPosition]:
        """
        Compute satellite positions at a specific time
        Args:
            timestr: Time for which to compute the position. Has to be a string
            formatted as with `%Y/%m/%d %H:%M:%S`.

        Returns:
            Dict[int, SatPosition]: A dictionary of satellite positions, keyed
                by satellite index.
        """
        positions = {}
        for idx, satellite in self.satellites.items():
            positions[idx] = satellite.position_at_time(timestr)
        return positions

    def compute_positions_at_epoch_offset(
        self, hours: int = 0, minutes: int = 0, seconds: int = 0, millisecs: int = 0
    ) -> Dict[int, GeodeticPosition]:
        """
        Compute satellite positions at a particular epoch offset
        Args:
            hours: Offset hours.
            minutes: Offset minutes.
            seconds: Offset seconds.
            millisecs: Offset milliseconds

        Returns: Dict[int, SatPosition]: A dictionary of satellite positions, keyed
                by satellite index.
        """

        target_date_str = epoch_offset_to_date(
            self.epoch, hours, minutes, seconds, millisecs
        )
        return self.compute_positions_at_time(target_date_str)

    def positions_tostring(self) -> List[str]:
        """
        List of strings with index and position information.
        List is sorted by satellite idx.
        """
        pos_str = []
        for idx in range(self.num_sat_per_orbit * self.num_orbits):
            pos_str.append(self.satellites[idx].sat_position_tostring())
        return pos_str


if __name__ == "__main__":
    raise RuntimeError
