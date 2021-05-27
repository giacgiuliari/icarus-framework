#  2020 Tommaso Ciussani and Giacomo Giuliari
import os

from netCDF4 import Dataset
from scipy.spatial.ckdtree import cKDTree
import numpy as np

from icarus_simulator.sat_core.coordinate_util import geo2cart
from icarus_simulator.strategies.grid_weight.base_weight_strat import BaseWeightStrat
from icarus_simulator.structure_definitions import GridPos

dirname = os.path.dirname(__file__)
strategies_dirname = os.path.split(dirname)[0]
library_dirname = os.path.split(strategies_dirname)[0]
data_dirname = os.path.join(library_dirname, "data")
GDP_FILE: str = os.path.join(data_dirname, "GDP_PPP_1990_2015_5arcmin_v2.nc")


class GDPWeightStrat(BaseWeightStrat):
    def __init__(self, dataset_file: str = None, **kwargs):
        super().__init__()
        if dataset_file is None:
            self.dataset = GDP_FILE
        else:
            self.dataset = dataset_file
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "gdp"

    @property
    def param_description(self) -> None:
        return None

    def compute(self, grid_pos: GridPos) -> GridPos:
        # Add the default weight for this unweighted grid
        # Load the GDP data
        gdp_matrix = load_dataset(self.dataset)
        lat_size, lon_size = gdp_matrix.shape
        gdp_cart = []
        gdp_values = []
        idx = 0
        gdp_grid = {}
        for lat_id in range(0, lat_size):
            for lon_id in range(0, lon_size):
                value = gdp_matrix[lat_id, lon_id]
                if value > 0:
                    lat = get_lat(lat_id)
                    lon = get_lon(lon_id)
                    gdp_cart.append(geo2cart({"elev": 0, "lon": lon, "lat": lat}))
                    gdp_grid[idx] = {"lat": lat, "lon": lon, "value": value}
                    gdp_values.append(value)
                    idx += 1

        # Generate the homogeneous grid
        grid_cart = np.zeros((len(grid_pos), 3))
        for i in grid_pos:
            grid_cart[i] = geo2cart(
                {"elev": 0, "lon": grid_pos[i].lon, "lat": grid_pos[i].lat}
            )
            grid_pos[i].weight = 0.0

        # Put the homogeneous grid into a KD-tree and query all the points, summing values to the closest grid point
        kd = cKDTree(grid_cart)
        for gdp_idx in range(len(gdp_cart)):
            _, closest_grid_idx = kd.query(gdp_cart[gdp_idx], k=1)
            grid_pos[closest_grid_idx].weight += gdp_values[gdp_idx]

        # Remove the zero-weight points
        grid_pos = {idx: point for idx, point in grid_pos.items() if point.weight > 0.0}
        # for idx, point in grid_s.items():
        #    grid_s[idx].weight = math.log10(point.weight)
        max_single_gdp = max(grid_pos.values(), key=lambda ka: ka.weight).weight
        for gp in grid_pos:
            grid_pos[gp].weight = grid_pos[gp].weight / max_single_gdp
        return grid_pos


# Downsample an ndarray to a new shape by summing
def downsample_ndarray(ndarray: np.ndarray, new_shape: np.shape) -> np.ndarray:
    compression_pairs = [(d, c // d) for d, c in zip(new_shape, ndarray.shape)]
    flattened = [li for p in compression_pairs for li in p]
    ndarray = ndarray.reshape(flattened)
    for i in range(len(new_shape)):
        ndarray = ndarray.sum(-1 * (i + 1))
    return ndarray


# Load the GDP distribution data.
def load_dataset(dataset_fname) -> np.ndarray:
    # Resolution is 5 arcmin -> 12 points per degree
    # lat: full globe, 0 is 90°; lon: full globe, 0 is -180
    # Unit: 2011 USD, Index for 2015 is 25
    # GDP_PPP indexed by (year_id, latitude_id, longitude_id)
    nc = Dataset(dataset_fname, "r")
    matrix = nc["GDP_PPP"][25, :, :]
    # matrix = nc["Population Count, v4.11 (2000, 2005, 2010, 2015, 2020): 2.5 arc-minutes"][4, :, :]
    matrix = matrix.filled(0.0)
    # Return indexed by lat, long
    return downsample_ndarray(matrix, (180, 360))


# Get latitude from index in gdp matrix
def get_lat(idx: int):
    return 90 - idx - 0.5


# Get longitude from index in gdp matrix
def get_lon(idx: int):
    return -180 + idx + 0.5
