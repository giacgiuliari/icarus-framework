#  2020 Tommaso Ciussani and Giacomo Giuliari

from abc import abstractmethod


class OrbitShiftAlgo:
    """Base class to create orbit shift algorithms."""

    def __init__(self):
        pass

    @abstractmethod
    def get_shift(self, orbit_idx):
        """Method to compute the orbit shift based on orbit index.

        Args:
            orbit_idx: the index of the orbit for which to compute the shift.

        Returns:
            float: The decimal representation of the degrees to shift.
        """
        raise NotImplementedError


class SimpleShift(OrbitShiftAlgo):
    """Shift each odd orbit by half the inter-satellite angular distance.

    This shift is a simplified version of a Walker shift.
    Credits: satnetwork.github.io
    """

    def __init__(self, num_sat_per_orbit):
        super().__init__()
        self.num_sat_per_orbit = num_sat_per_orbit

    def get_shift(self, orbit_idx: int) -> float:
        """Method to compute the orbit shift based on orbit index.

        Args:
            orbit_idx: the index of the orbit for which to compute the shift.

        Returns:
            float: The decimal representation of the degrees to shift.
        """
        if orbit_idx % 2 == 1:
            return 360 / (self.num_sat_per_orbit * 2)
        return 0


class NoShift(OrbitShiftAlgo):
    """Do not shift."""

    def __init__(self):
        super().__init__()

    def get_shift(self, orbit_idx: int) -> float:
        """Method to compute the orbit shift based on orbit index.

        Args:
            orbit_idx: the index of the orbit for which to compute the shift.

        Returns:
            float: The decimal representation of the degrees to shift.
        """
        return 0


class WalkerShift(OrbitShiftAlgo):
    """Compute the shift according to the Walker constellation design.

    See:
        https://en.wikipedia.org/wiki/Satellite_constellation
    """

    def __init__(self, inclination, num_sat_per_orbit, num_orbits, f_param):
        super().__init__()
        assert 0 <= f_param < num_orbits
        self.inclination = inclination
        self.num_sat_per_orbit = num_sat_per_orbit
        self.num_orbits = num_orbits
        self.f_param = f_param
        # Compute the walker shift between adjacent planes
        t = num_sat_per_orbit * num_orbits
        self.plane_shift = f_param * 360 / t

    def get_shift(self, orbit_idx):
        # return (orbit_idx * self.plane_shift) % (360 / self.num_sat_per_orbit)
        return orbit_idx * self.plane_shift
