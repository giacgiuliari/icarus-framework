#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
File containing utility functions
"""
import math
from typing import Tuple, List


def get_ordered_idx(idx: Tuple[int, int]):
    if idx[0] > idx[1]:
        return (idx[1], idx[0]), False
    return idx, True


def get_edges(list_elements, excl_start=0, excl_end=0):
    minus = 1 + excl_end
    for i in range(excl_start, len(list_elements) - minus):
        yield list_elements[i], list_elements[i + 1]


def similarity(path1, path2, len1, len2, network):
    p1_eds, p2_eds = set(get_edges(path1)), set(get_edges(path2))
    common_eds = p1_eds.intersection(p2_eds)
    numer = sum([get_edge_length(network, ed) for ed in common_eds])
    return numer / min(len1, len2)


def get_edge_length(network, ed, prop="length"):
    return network[ed[0]][ed[1]][prop]


def compute_intervals_uniform(length: int, cpus: int) -> List[Tuple[int, int]]:
    if length < cpus:
        cpus = length
    itvls = []
    prev_e = 0
    uniform_measure = int(math.ceil(length / cpus))
    for i in range(cpus - 1):
        s = prev_e
        if (length - s) / (cpus - i) <= uniform_measure - 1:
            e = s + uniform_measure - 1
        else:
            e = s + uniform_measure
        prev_e = e
        itvls.append((s, e))
    itvls.append((prev_e, length))
    return itvls
