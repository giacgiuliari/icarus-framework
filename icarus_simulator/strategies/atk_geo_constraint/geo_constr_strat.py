#  2020 Tommaso Ciussani and Giacomo Giuliari
import os
import json
import numpy as np

from typing import Set, List
from geopy.distance import great_circle
from scipy.spatial.ckdtree import cKDTree
from shapely.geometry import Polygon, shape, Point

from icarus_simulator.sat_core.coordinate_util import geo2cart
from icarus_simulator.strategies.atk_geo_constraint.base_geo_constraint_strat import (
    BaseGeoConstraintStrat,
)
from icarus_simulator.structure_definitions import GridPos

dirname = os.path.dirname(__file__)
strategies_dirname = os.path.split(dirname)[0]
library_dirname = os.path.split(strategies_dirname)[0]
data_dirname = os.path.join(library_dirname, "data")
COUNTRIES_FILE: str = os.path.join(data_dirname, "natural_earth_world_small.geo.json")


class GeoConstrStrat(BaseGeoConstraintStrat):
    def __init__(self, geo_names: List[str], **kwargs):
        super().__init__()
        self.geo_names = geo_names
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "geo"

    @property
    def param_description(self) -> str:
        return ",".join(self.geo_names)

    def compute(self, grid_pos: GridPos) -> Set[int]:
        allowed = set()
        geo_data = load_country_geojson()
        for s in self.geo_names:
            allowed.update(get_allowed_gridpoints(s, grid_pos, geo_data))
        return allowed


# noinspection PyTypeChecker
def get_allowed_gridpoints(geo_location: str, grid_pos: GridPos, geo_data) -> Set[int]:
    # Get a list of all possible source points
    if geo_location in geo_data["countries"]:
        indices = [geo_data["countries"][geo_location]]
    elif geo_location in geo_data["subregions"]:
        indices = geo_data["subregions"][geo_location]
    elif geo_location in geo_data["continents"]:
        indices = geo_data["continents"][geo_location]
    else:
        raise ValueError("Invalid geographic constraint")

    geometries = [geo_data["geometries"][index] for index in indices]
    allowed_points = set()
    # Create a unique shape, union of all shapes in the region, and take the points include within
    shp = Polygon()
    for idx, geo in enumerate(geometries):
        shp = shp.union(shape(geo))
    for idx, pos in grid_pos.items():
        if Point(pos.lat, pos.lon).within(shp):
            allowed_points.add(idx)

    # Extract the border points
    x, y = [], []
    if shp.geom_type == "MultiPolygon":
        for idx, shap in enumerate(shp.geoms):
            if True:
                x1, y1 = shap.exterior.xy
                x.extend(x1)
                y.extend(y1)
    else:
        x1, y1 = shp.exterior.xy
        x.extend(x1)
        y.extend(y1)
    # plotter.plot_points({idx: GeodeticPosInfo({"lat": x[idx], "lon": y[idx], "elev": 0.0})
    #                       for idx in range(len(x))}, "GRID", "TEST", "aa", "asas",)

    grid_cart = np.zeros((len(grid_pos), 3))
    grid_map = {}
    i = 0
    for idx, pos in grid_pos.items():
        grid_map[i] = idx
        grid_cart[i] = geo2cart({"elev": 0, "lon": pos.lon, "lat": pos.lat})
        i += 1

    # Put the homogeneous grid into a KD-tree and query the border points to include also point slightly in the sea
    kd = cKDTree(grid_cart)
    for idx in range(len(x)):
        _, closest_grid_idx = kd.query(
            geo2cart({"elev": 0, "lon": y[idx], "lat": x[idx]}), k=1
        )
        grid_id = grid_map[closest_grid_idx]
        if (
            great_circle(
                (grid_pos[grid_id].lat, grid_pos[grid_id].lon), (x[idx], y[idx])
            ).meters
            < 300000
        ):
            # 300000 -> number elaborated to keep the out-of-coast values without including wrong points
            allowed_points.add(grid_map[closest_grid_idx])
    return allowed_points


# noinspection PyTypeChecker
def load_country_geojson():
    new_data = {"geometries": [], "countries": {}, "continents": {}, "subregions": {}}
    with open(COUNTRIES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    new_data["geometries"] = [""] * len(data["features"])

    for idx, feature in enumerate(data["features"]):
        props = feature["properties"]
        code = props["iso_a3"]
        if code == "-99":
            continue
        continent = props["continent"]
        subregion = props["region_wb"]
        subregion2 = props["subregion"]
        if continent not in new_data["continents"]:
            new_data["continents"][continent] = []
        if subregion not in new_data["subregions"]:
            new_data["subregions"][subregion] = []
        if subregion2 not in new_data["subregions"]:
            new_data["subregions"][subregion2] = []
        new_data["continents"][continent].append(idx)
        new_data["subregions"][subregion].append(idx)
        new_data["subregions"][subregion2].append(idx)
        new_data["countries"][code] = idx
        new_data["geometries"][idx] = feature["geometry"]
        geom = new_data["geometries"][idx]
        if geom["type"] == "MultiPolygon":
            for l1 in range(len(geom["coordinates"])):
                for l2 in range(len(geom["coordinates"][l1])):
                    for l3 in range(len(geom["coordinates"][l1][l2])):
                        geom["coordinates"][l1][l2][l3] = geom["coordinates"][l1][l2][
                            l3
                        ][::-1]
        elif geom["type"] == "Polygon":
            for l1 in range(len(geom["coordinates"])):
                for l2 in range(len(geom["coordinates"][l1])):
                    geom["coordinates"][l1][l2] = geom["coordinates"][l1][l2][::-1]
    print(f"Available subregions: {list(new_data['subregions'].keys())}")
    return new_data
