#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
This Builder object builds a geographic plot step by step. The order in which methods are called influences the plot.
The class is self-explanatory, method names add what they promise on the globe map.
"""
import numpy as np
import plotly.graph_objects as go

from matplotlib import cm
from typing import Dict, List

from icarus_simulator.structure_definitions import (
    GeoPoint,
    IslInfo,
    SatPos,
    GridPos,
    Path,
    Edge,
)


class GeoPlotBuilder:
    viridis = cm.get_cmap("Spectral_r", 12)  # Spectral_r

    LOW = 0
    MED = 1
    HI = 2

    def __init__(self):
        self.fig = go.Figure()
        self.transparency = True
        self.l_thick = [2, 6, 9]
        self.p_thick = [6, 12, 16]
        self.is_2d = True

    # Set if the less important links should have lower transparency
    def set_transparency(self, transparency: bool) -> "GeoPlotBuilder":
        self.transparency = transparency
        return self

    # Set the line thickness
    def set_line_thickness(self, low: int, med: int, high: int) -> "GeoPlotBuilder":
        self.l_thick = [low, med, high]
        return self

    def set_point_thickness(self, low: int, med: int, high: int) -> "GeoPlotBuilder":
        self.p_thick = [low, med, high]
        return self

    # Set if the less important links should have lower transparency
    def set_2d(self, is_2d: bool) -> "GeoPlotBuilder":
        self.is_2d = is_2d
        return self

    # Save the plot to file
    def save_to_file(self, fname: str) -> "GeoPlotBuilder":
        self._update_layout()
        self.fig.write_image(fname, width=3000, height=1800, scale=2.0)
        return self

    # Show plot on browser
    def show(self) -> "GeoPlotBuilder":
        self._update_layout()
        self.fig.show()
        return self

    # Ensure the map is plotted on an empty graph
    def empty(self) -> "GeoPlotBuilder":
        self.points(
            {0: GeoPoint(0.0, 0.0, 0.0)},
            color="rgba(0,0,0,0.0)",
            size_id=self.LOW,
            word_hover="",
        )
        return self

    # Plot the whole constellation in the background
    def constellation(self, sat_pos: SatPos, isls: List[IslInfo]) -> "GeoPlotBuilder":
        for isl in isls:
            self.path(
                [sat_pos[isl.sat1], sat_pos[isl.sat2]],
                "rgba(200, 200, 200, 0.5)",
                self.LOW,
            )
        self.points(sat_pos, "rgba(200, 200, 200, 0.5)", self.LOW, "SAT")
        return self

    # Plots a heatmap on the isls
    def isl_heatmap(
        self, sat_pos: SatPos, isl_values: Dict[Edge, float], max_isl: float = None
    ) -> "GeoPlotBuilder":
        # Print highest at the top
        isl_values = list(sorted(isl_values.items(), key=lambda k: k[1]))
        if max_isl is None and len(isl_values) > 0:
            max_isl = isl_values[-1][1]
        for edge, val in isl_values:
            self.path(
                [sat_pos[idx] for idx in edge],
                self.get_color(float(val), float(max_isl), self.transparency),
                self.MED,
                "solid",
                f"{float(val):,.4f}",
            )
        return self

    # Plots a heatmap of both points and isls
    def point_heatmap(
        self,
        point_pos: Dict[int, GeoPoint],
        point_values: Dict[int, float],
        max_point: float = None,
    ) -> "GeoPlotBuilder":
        point_values = list(sorted(point_values.items(), key=lambda k: k[1]))
        if max_point is None and len(point_values) > 0:
            max_point = point_values[-1][1]
        for idx, val in point_values:
            self.points(
                {idx: point_pos[idx]},
                self.get_color(float(val), float(max_point), self.transparency),
                self.MED,
                "",
            )
        return self

    # Plot a list of paths
    def path_list(
        self,
        sat_pos: SatPos,
        grid_pos: GridPos,
        paths: List[Path],
        color: str,
        size_id: int,
        dash: str = "solid",
    ) -> "GeoPlotBuilder":
        udls, sat_paths, gnds, ext_sats = [], [], {}, {}
        for path in paths:
            # Check if start has an uplink
            if path[0] < 0:
                st = 1
                ext_sats[path[1]] = sat_pos[path[1]]
                if path[0] != -1:
                    gnds[-path[0]] = grid_pos[-path[0]]
                    udls.append([grid_pos[-path[0]], sat_pos[path[1]]])
            else:
                st = 0
                ext_sats[path[0]] = sat_pos[path[0]]
            # Check if the end has a downlink
            if path[-1] < 0:
                end = len(path) - 1
                ext_sats[path[-2]] = sat_pos[path[-2]]
                if path[-1] != -1:
                    gnds[-path[-1]] = grid_pos[-path[-1]]
                    udls.append([grid_pos[-path[-1]], sat_pos[path[-2]]])
            else:
                end = len(path)
                ext_sats[path[-1]] = sat_pos[path[-1]]
            sat_paths.append([sat_pos[idx] for idx in path[st:end]])

        # Print the gnd points and uplinks first
        low_sz = max(0, size_id - 1)
        self.points(gnds, color, low_sz, "GND")
        for udl in udls:
            self.path(udl, color, low_sz, dash)
        # Print the satellite portion
        self.points(ext_sats, color, size_id, "SAT")
        for sp in sat_paths:
            self.path(sp, color, size_id, dash)
        return self

    # Plot basics
    def points(
        self, point_dict: Dict[int, GeoPoint], color: str, size_id: int, word_hover: str
    ) -> "GeoPlotBuilder":
        lats, lons, texts = [], [], []
        for idx, point in point_dict.items():
            lats.append(point.lat)
            lons.append(point.lon)
            texts.append(f"{word_hover}{idx} - {point.lat}, {point.lon}")
        self.fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                hoverinfo="text",
                text=texts,
                mode="markers",
                marker=dict(size=self.p_thick[size_id], color=color),
            )
        )
        return self

    def path(
        self,
        path_points: List[GeoPoint],
        color: str,
        size_id: int,
        dash: str = "solid",
        hover: str = "",
    ) -> "GeoPlotBuilder":
        # [‘solid’, ‘dot’, ‘dash’, ‘longdash’, ‘dashdot’, ‘longdashdot’]
        lats, lons = [], []
        for cur in path_points:
            lats.append(cur.lat)
            lons.append(cur.lon)
        self.fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                hoverinfo="text",
                text=hover,
                mode="lines",
                line=dict(width=self.l_thick[size_id], color=color, dash=dash),
            )
        )
        return self

    def arrow(
        self,
        src_point: GeoPoint,
        trg_point: GeoPoint,
        color: str,
        size_id: int,
        hover_info: str,
    ) -> "GeoPlotBuilder":
        # Draw the line
        lats, lons = [src_point.lat, trg_point.lat], [src_point.lon, trg_point.lon]
        self.fig.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                hoverinfo="text",
                text=hover_info,
                mode="lines",
                line=dict(width=self.l_thick[size_id], color=color),
            )
        )
        # Draw an arrow with some plotly magic
        arrow_len = 3  # the arrow length
        arrow_width = 0.2  # 2*arrow_width is the width of the arrow base as triangle
        src = np.array([src_point.lon, src_point.lat])
        trg = np.array([trg_point.lon, trg_point.lat])
        v = trg - src
        w = v / np.linalg.norm(v)
        u = np.array([-v[1], v[0]])  # u orthogonal on w
        p = trg - arrow_len * w
        s = p - arrow_width * u
        t = p + arrow_width * u
        self.fig.add_trace(
            go.Scattergeo(
                lon=[s[0], t[0], trg[0], s[0]],
                lat=[s[1], t[1], trg[1], s[1]],
                mode="lines",
                fill="toself",
                fillcolor=color,
                line_color=color,
            )
        )
        return self

    def _update_layout(self):
        self.fig.update_layout(
            showlegend=False,
            autosize=True,
            geo=dict(
                resolution=50,
                showcountries=False,
                countrywidth=0.5,
                showland=False,
                showocean=False,
                oceancolor="rgba(245,245,253, 0.0)",
                landcolor="rgba(232,232,232, 0.0)",
                countrycolor="rgb(200, 200, 200)",
                projection=dict(
                    type="equirectangular" if self.is_2d else "orthographic"
                ),
                lonaxis=dict(
                    showgrid=False, gridcolor="rgb(102, 102, 102)", gridwidth=0.5
                ),
                lataxis=dict(
                    showgrid=False, gridcolor="rgb(102, 102, 102)", gridwidth=0.5
                ),
            ),
        )

    # Method used internally to get colours from the colormap based on a value
    @classmethod
    def get_color(cls, value: float, max_val: float, transp_adjust=True) -> str:
        if max_val > 0.0:
            ratio = value / max_val
        else:
            ratio = 0.0
        color = cls.viridis(ratio)
        # Adjust transparency to improve aesthetics, if required
        if transp_adjust:
            transp = 1.02785 + (0.15 - 1.02785) / (1 + (ratio / 0.2377001) ** 2.379258)
            if transp < 0.15:
                transp = 0.15
        else:
            transp = 1.0

        return f"rgba({color[0]:.4f}, {color[1]:.4f}, {color[2]:.4f}, {transp:.4f})"
