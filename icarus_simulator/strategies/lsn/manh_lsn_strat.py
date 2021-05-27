#  2020 Tommaso Ciussani and Giacomo Giuliari

import networkx as nx

from typing import Tuple, List

from icarus_simulator.sat_core import WalkerConstellationNetwork
from icarus_simulator.strategies.lsn.base_lsn_strat import BaseLSNStrat
from icarus_simulator.structure_definitions import SatPos, GeoPoint, IslInfo


class ManhLSNStrat(BaseLSNStrat):
    def __init__(
        self,
        inclination: int,
        sats_per_orbit: int,
        orbits: int,
        f: int,
        elevation: int,
        hrs: int,
        mins: int,
        secs: int,
        millis: int,
        epoch: str,
        **kwargs,
    ):
        super().__init__()
        self.inclination = inclination
        self.sats_per_orbit = sats_per_orbit
        self.orbits = orbits
        self.f = f
        self.elevation = elevation
        self.hrs = hrs
        self.mins = mins
        self.secs = secs
        self.millis = millis
        self.epoch = epoch
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "reg"

    @property
    def param_description(self) -> str:
        return (
            f"{self.inclination}°{self.sats_per_orbit}x{self.orbits}f{self.f}"
            f"e{int(self.elevation//1000)}km"
            f"{str(self.hrs).zfill(2)}h{str(self.mins).zfill(2)}m{str(self.secs).zfill(2)}s"
            f"{str(self.millis).zfill(4)}ms"
            f"{str(self.epoch).replace(' ' , '').replace(':', '').replace('/', '')}"
        )

    def compute(self) -> Tuple[SatPos, nx.Graph, List[IslInfo]]:
        walker = WalkerConstellationNetwork(
            self.sats_per_orbit,
            self.orbits,
            self.inclination,
            self.epoch,
            self.f,
            elevation=self.elevation,
        )
        walker.compute_network_at_epoch_offset(self.hrs, self.mins, self.secs)
        sat_pos = {
            key: GeoPoint.from_geo_pos(val)
            for key, val in walker.cnet.get_sats().items()
        }
        nw = walker.cnet.network
        isls = walker.cnet.get_isls()
        isls = [IslInfo(isl["sat1"], isl["sat2"], isl["length"]) for isl in isls]
        return sat_pos, nw, isls
