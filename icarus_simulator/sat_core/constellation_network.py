#  2020 Tommaso Ciussani and Giacomo Giuliari


from typing import List, Tuple, Dict
from typing_extensions import TypedDict
import networkx as nx

from .constellation import Constellation
from .isl_util import sat_idx_to_in_orbit_idx, compute_link_length, get_sat_by_offset
from .orbit_shift_algo import WalkerShift
from .coordinate_util import GeodeticPosition


class Isl(TypedDict):
    sat1: int
    sat2: int
    length: float


class ConstellationNetwork:
    """The network made by interconnecting satellites with a "motif"."""

    def __init__(
        self,
        sat_pos: Dict[int, GeodeticPosition],
        num_sat_per_orbit: int,
        num_orbits: int,
        max_shift: float = 0,
    ):
        self.sat_pos = sat_pos
        self.num_sat_per_orbit = num_sat_per_orbit
        self.num_orbits = num_orbits
        self.network: nx.Graph = nx.Graph()
        self.max_shift = max_shift

    def generate_network(self, motif):
        """
        Args:
            motif: The description of a motif. A list of tuples. Each tuple
                contains two indices, representing the offset from the current
                satellite.
        """
        for sat_idx in self.sat_pos:
            sat_idx_in_orbit, orbit_idx = sat_idx_to_in_orbit_idx(
                sat_idx, self.num_sat_per_orbit
            )
            for sat_off, orbit_off in motif:
                neigh_idx, _, _ = get_sat_by_offset(
                    sat_idx_in_orbit,
                    orbit_idx,
                    sat_off,
                    orbit_off,
                    self.num_sat_per_orbit,
                    self.num_orbits,
                    self.max_shift,
                )
                length = compute_link_length(
                    self.sat_pos[sat_idx], self.sat_pos[neigh_idx]
                )
                self.network.add_edge(sat_idx, neigh_idx, length=length)

    def get_sats(self):
        return self.sat_pos.copy()

    def get_isls(self) -> List[Isl]:
        isls = []
        for start, end in self.network.edges():
            length = self.network[start][end]["length"]
            isl = {"sat1": start, "sat2": end, "length": length}
            isls.append(isl)
        return isls

    def isls_tostring(self) -> List[str]:
        """List of strings information on the ISLa.

        List is sorted by satellite idx.
        """
        pos_str = []
        for start, end in self.network.edges():
            # slat, slong, selev = self.sat_pos[start]
            # elat, elong, eelev = self.sat_pos[end]
            length = self.network[start][end]["length"]
            cur = f"{start} {end} {length}"
            pos_str.append(cur)
        return pos_str


class WalkerConstellationNetwork:
    """Helper class that combine Constellation and ConstellationNetwork.

    Helps create a constellation network with Walker topology fast.
    """

    def __init__(
        self,
        num_sat_per_orbit: int,
        num_orbits: int,
        inclination: float,
        epoch: str,
        f_param: int,
        mean_motion: float = None,
        elevation: float = None,
        motif: List[Tuple[int, int]] = ((0, 1), (1, 0)),
    ) -> None:
        self.shiftalgo = WalkerShift(
            inclination, num_sat_per_orbit, num_orbits, f_param
        )
        max_shift = self.shiftalgo.get_shift(num_orbits - 1)
        self.const = Constellation(
            num_sat_per_orbit,
            num_orbits,
            inclination,
            epoch,
            mean_motion=mean_motion,
            elevation=elevation,
            orbit_shift_algo=self.shiftalgo,
        )
        self.const.create_constellation()
        sat_pos = self.const.compute_positions_at_epoch_offset()
        # Create the network
        self.cnet = ConstellationNetwork(
            sat_pos, num_sat_per_orbit, num_orbits, max_shift=max_shift
        )
        self.cnet.generate_network(motif)
        self.f_param = f_param
        self.motif = motif
        self.num_sat_per_orbit = num_sat_per_orbit
        self.num_orbits = num_orbits
        self.max_shift = max_shift

    def compute_network_at_epoch_offset(
        self, hours=0, minutes=0, seconds=0, millisecs=0
    ):
        # TODO: Improve this integration
        sat_pos = self.const.compute_positions_at_epoch_offset(
            hours, minutes, seconds, millisecs
        )
        self.cnet = ConstellationNetwork(
            sat_pos, self.num_sat_per_orbit, self.num_orbits, max_shift=self.max_shift
        )
        self.cnet.generate_network(self.motif)
