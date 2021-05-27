#  2020 Tommaso Ciussani and Giacomo Giuliari

from scipy.constants import G


# Average great-circle radius in meters.
EARTH_RADIUS = 6371 * 1000
# Average duration of a day in seconds.
SEC_IN_DAY = 86400
# Earth mass
EARTH_MASS = 5.9722e24
# Atmosphere
ATMOSPHERE_HEIGHT = 100
# Standard Gravitational Parameter for earth
MU = G * EARTH_MASS
# Speed of light in m/s
LIGHTSPEED = 299792458
# Earth surface in km^2
EARTH_SURFACE = 510100000
