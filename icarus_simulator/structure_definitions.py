#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Definitions for aliases and custom data structures used in the predefined phases and strategies of the library.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Set, Optional

from .sat_core.coordinate_util import GeodeticPosition

Length = float
Pname = str
PropertyDict = Dict[Pname, Any]
DependencyDict = Dict[Pname, Set[str]]


# Satellite and Earth positions
@dataclass
class GeoPoint:
    # Extension of the geodetic position class defined in sat_core library
    lat: float
    lon: float
    elev: float

    @staticmethod
    def from_geo_pos(pos: GeodeticPosition) -> "GeoPoint":
        return GeoPoint(pos["lat"], pos["lon"], pos["elev"])

    def to_geo_pos(self) -> GeodeticPosition:
        return {"lat": self.lat, "lon": self.lon, "elev": self.elev}


@dataclass
class GridPoint(GeoPoint):
    weight: float = 0.0
    surface: float = 0.0


@dataclass
class IslInfo:
    sat1: int
    sat2: int
    length: float


# List definitions associate each position to an index
SatPos = Dict[int, GeoPoint]
GridPos = Dict[int, GridPoint]

# Coverage -> first id is the gnd index, second is the satellite, float is the distance gnd-sat
Coverage = Dict[int, Dict[int, Length]]

# Routing
SdPair = Tuple[int, int]
Path = List[int]
TuplePath = Tuple[int, ...]
PathInfo = Tuple[Path, Length]
LbSet = List[PathInfo]
PathData = Dict[SdPair, LbSet]  # The sdpair structure is always ordered numerically
PathId = Tuple[int, int, int]

# Edges
Edge = Tuple[int, int]  # An edge is a pair of sat indices, or gnd-sat indices
# The set contains the indices of cross zone paths covered by the edge
PathEdgeData = Dict[Edge, Set[int]]


@dataclass
class TempEdgeInfo:
    paths_through: List[PathId]
    centrality: float
    source_gridpoints: Set[int]


@dataclass
class EdgeInfo:
    paths_through: List[PathId]
    centrality: float = 0.0
    cov_centr: float = 0.0


EdgeData = Dict[Edge, EdgeInfo]  # The Edge here must be ordered numerically


# Traffic matrix
@dataclass
class BwInfo:
    idle_bw: int = 0
    capacity: int = 0

    def get_remaining_bw(self) -> int:
        return self.capacity - self.idle_bw


BwData = Dict[Edge, BwInfo]


# SSingle-target attacks
@dataclass
class PairInfo:
    directions: Set[TuplePath] = field(default_factory=set)
    prob: float = 0.0
    tot: int = 0


DirectionData = Dict[TuplePath, List[SdPair]]
PairData = Dict[SdPair, PairInfo]
AtkFlowSet = Set[Tuple[SdPair, int]]


@dataclass
class AttackInfo:
    cost: int
    detectability: int
    flows_on_trg: int
    atkflowset: AtkFlowSet


AttackData = Dict[Edge, Optional[AttackInfo]]

Zone = List[int]
TupleZone = Tuple[int, ...]


@dataclass
class ZoneAttackInfo(AttackInfo):
    cross_zone_paths: List[Path]
    bottlenecks: List[Edge]
    distance: float


ZoneAttackData = Dict[Tuple[TupleZone, TupleZone], Optional[ZoneAttackInfo]]
