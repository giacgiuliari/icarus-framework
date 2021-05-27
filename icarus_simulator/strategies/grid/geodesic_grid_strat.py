#  2020 Tommaso Ciussani and Giacomo Giuliari
import math

from anti_lib import Vec

from icarus_simulator.strategies.grid.base_grid_strat import BaseGridStrat
from icarus_simulator.sat_core.planetary_const import EARTH_SURFACE
from icarus_simulator.structure_definitions import GridPos, GridPoint


class GeodesicGridStrat(BaseGridStrat):
    def __init__(self, repeats: int, **kwargs):
        super().__init__()
        self.repeats = repeats
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "geo"

    @property
    def param_description(self) -> str:
        return f"{self.repeats}"

    def compute(self) -> GridPos:
        verts, edges, faces = [], {}, []
        get_poly(verts, edges, faces)

        # a and b have same meanings as in geodesic notation
        # with the hardcoded 1, 0, 1: the grid will generate an icosahedron of class 1 with no divisions
        # when a=0 or b=0, the one that is nonzero will determine the number of divisions per face
        # The parameter repeats sets the multiple of the chosen pattern. if a=6 and repeats=2, each edge will be divided
        # into 12 parts. Setting a value of 1 and 6 to repeats and a or to a and repeats yields the same result.
        a, b, reps = 1, 0, 1
        repeats = self.repeats * reps
        triangulation_number = (
            a ** 2 + a * b + b ** 2
        )  # Total number of triangles in a face w/o repeats
        freq = repeats * triangulation_number

        single_face_grid = make_face_grid(freq, a, b)
        points = verts
        for face in faces:
            points[len(points) : len(points)] = grid_to_points(
                single_face_grid, freq, False, [verts[face[i]] for i in range(3)], face
            )
        points = [p.unit().v for p in points]  # Project onto sphere
        grid = {
            idx: GridPoint.from_geo_pos(cart2geo(p)) for idx, p in enumerate(points)
        }
        sur = EARTH_SURFACE / len(grid)
        for idx in grid:
            grid[idx].surface = sur
        return grid


def cart2geo(point):
    # radius is fixed here to the Earth's radius
    x = point[0]
    y = point[1]
    z = point[2]

    latitude = math.asin(z)
    longitude = math.atan2(y, x)
    return {"lat": math.degrees(latitude), "lon": math.degrees(longitude), "elev": 0.0}


def get_ico_coords():
    """Return icosahedron coordinate values"""
    phi = (math.sqrt(5) + 1) / 2
    rad = math.sqrt(phi + 2)
    return 1 / rad, phi / rad


def get_icosahedron(verts, faces):
    """Return an icosahedron"""
    x, z = get_ico_coords()
    verts.extend(
        [
            Vec(-x, 0.0, z),
            Vec(x, 0.0, z),
            Vec(-x, 0.0, -z),
            Vec(x, 0.0, -z),
            Vec(0.0, z, x),
            Vec(0.0, z, -x),
            Vec(0.0, -z, x),
            Vec(0.0, -z, -x),
            Vec(z, x, 0.0),
            Vec(-z, x, 0.0),
            Vec(z, -x, 0.0),
            Vec(-z, -x, 0.0),
        ]
    )

    faces.extend(
        [
            (0, 4, 1),
            (0, 9, 4),
            (9, 5, 4),
            (4, 5, 8),
            (4, 8, 1),
            (8, 10, 1),
            (8, 3, 10),
            (5, 3, 8),
            (5, 2, 3),
            (2, 7, 3),
            (7, 10, 3),
            (7, 6, 10),
            (7, 11, 6),
            (11, 0, 6),
            (0, 1, 6),
            (6, 1, 10),
            (9, 0, 11),
            (9, 11, 2),
            (9, 2, 5),
            (7, 2, 11),
        ]
    )


def get_poly(verts, edges, faces):
    """Return the base polyhedron"""
    get_icosahedron(verts, faces)
    for face in faces:
        for i in range(0, len(face)):
            i2 = i + 1
            if i2 == len(face):
                i2 = 0
            if face[i] < face[i2]:
                edges[(face[i], face[i2])] = 0
            else:
                edges[(face[i2], face[i])] = 0
    return 1


def grid_to_points(grid, freq, div_by_len, face_verts, face):
    """Convert grid coordinates to Cartesian coordinates"""
    points = []
    v = []
    for vtx in range(3):
        v.append([Vec(0.0, 0.0, 0.0)])
        edge_vec = face_verts[(vtx + 1) % 3] - face_verts[vtx]
        if div_by_len:
            for i in range(1, freq + 1):
                v[vtx].append(edge_vec * float(i) / freq)
        else:
            ang = 2 * math.asin(edge_vec.mag() / 2.0)
            unit_edge_vec = edge_vec.unit()
            for i in range(1, freq + 1):
                len_var = math.sin(i * ang / freq) / math.sin(
                    math.pi / 2 + ang / 2 - i * ang / freq
                )
                v[vtx].append(unit_edge_vec * len_var)

    for (i, j) in grid.values():

        if (i == 0) + (j == 0) + (i + j == freq) == 2:  # skip vertex
            continue
        # skip edges in one direction
        if (
            (i == 0 and face[2] > face[0])
            or (j == 0 and face[0] > face[1])
            or (i + j == freq and face[1] > face[2])
        ):
            continue

        n = [i, j, freq - i - j]
        v_delta = (
            v[0][n[0]] + v[(0 - 1) % 3][freq - n[(0 + 1) % 3]] - v[(0 - 1) % 3][freq]
        )
        pt = face_verts[0] + v_delta
        if not div_by_len:
            for k in [1, 2]:
                v_delta = (
                    v[k][n[k]]
                    + v[(k - 1) % 3][freq - n[(k + 1) % 3]]
                    - v[(k - 1) % 3][freq]
                )
                pt = pt + face_verts[k] + v_delta
            pt = pt / 3
        points.append(pt)

    return points


def make_face_grid(freq, m, n):
    """Make the geodesic pattern grid"""
    grid = {}
    rng = (2 * freq) // (m + n)
    for i in range(rng):
        for j in range(rng):
            x = i * (-n) + j * (m + n)
            y = i * (m + n) + j * (-m)

            if x >= 0 and y >= 0 and x + y <= freq:
                grid[(i, j)] = (x, y)

    return grid
