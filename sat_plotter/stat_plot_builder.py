#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
This Builder object builds a statistical plot step by step. The order in which methods are called influences the plot.
The class is self-explanatory, method names add what they promise on the graph.
This class uses the amazing defaults from Amazingplots by Giacomo Giuliari for colour and dash.
Refer to and edit the file amazingplots.mpstyle for changes in the default style.
"""
import os
import itertools
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import cm
from typing import List, Optional

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "amazingplots.mpstyle")
plt.style.use(filename)


class StatPlotBuilder:
    viridis = cm.get_cmap("Spectral_r", 12)  # Spectral_r

    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.thick = 5
        self.bins = 1000
        self.fig.set_size_inches(14, 5)
        plt.xticks(fontsize=25)
        plt.yticks(fontsize=25)

    # Save the plot to file, jpeg not allowed as extension
    def save_to_file(self, fname: str) -> "StatPlotBuilder":
        plt.savefig(fname, dpi=300)
        return self

    # Show plot
    def show(self) -> "StatPlotBuilder":
        plt.show()
        return self

    # Set the axis labels
    def labels(self, x_label: str, y_label: str) -> "StatPlotBuilder":
        plt.xlabel(x_label, fontsize=32)
        plt.ylabel(y_label, fontsize=32)
        return self

    # Add the legend
    def legend(self) -> "StatPlotBuilder":
        plt.legend(loc="lower right")
        return self

    # Set the line width
    def set_thickness(self, thickness: int) -> "StatPlotBuilder":
        self.thick = thickness
        return self

    # Set the bin number for the cdf/pdf
    def set_bins(self, bins: int) -> "StatPlotBuilder":
        self.bins = bins
        return self

    # Set the scaling to zero
    def set_zero_y(self) -> "StatPlotBuilder":
        self.bins = self.ax.set_ylim(ymin=0)
        return self

    # Set y logarithmic scale
    def set_log_y(self) -> "StatPlotBuilder":
        plt.yscale("log")
        return self

    # Set the size
    def set_size(self, width: int, height: int) -> "StatPlotBuilder":
        self.fig.set_size_inches(width, height)
        return self

    # Add a CDF from data
    def cdf(
        self, data: List, label: str, weights: Optional[List] = None
    ) -> "StatPlotBuilder":
        # Weights None implies weights ignored
        _, _, patches = self.ax.hist(
            data,
            cumulative=True,
            density=True,
            bins=self.bins,
            histtype="step",
            label=label,
            linewidth=self.thick,
            joinstyle="round",
            capstyle="round",
            weights=weights,
        )
        patches[0].set_xy(patches[0].get_xy()[:-1])  # Avoids vertical line at the end
        return self

    # Add a PDF from data
    def pdf(
        self, data: List, label: str, weights: Optional[List] = None
    ) -> "StatPlotBuilder":
        _, _, patches = self.ax.hist(
            data,
            bins=self.bins,
            histtype="step",
            label=label,
            weights=weights,
            linewidth=self.thick,
            joinstyle="round",
            capstyle="round",
        )
        patches[0].set_xy(patches[0].get_xy()[:-1])
        return self

    # Histogram
    def hist(self, data: List, label: str) -> "StatPlotBuilder":
        self.ax.hist(data, bins=self.bins, label=label)
        return self

    # Line plot xy
    def line_xy(self, x: List, y: List, label: str) -> "StatPlotBuilder":
        self.ax.plot("x", "y", data={"x": x, "y": y}, label=label)
        return self

    # Point plot xy
    def point_xy(self, x: List, y: List, label: str) -> "StatPlotBuilder":
        self.ax.scatter(
            "x", "y", s="s", data={"x": x, "y": y, "s": [20] * len(x)}, label=label
        )
        return self

    # Plot a binned median line based on an xy dataset
    def binned_line_xy(self, x: List, y: List, label: str):
        min_x = min(x)
        quant_intvl = (max(x) - min_x) / self.bins
        quant_x = [
            (quant_intvl * round(d / quant_intvl), orig_idx)
            for orig_idx, d in enumerate(x)
        ]
        quant_x.sort(key=lambda k: k[0])
        temp, quant_y = [], []
        for item, group in itertools.groupby(quant_x, key=lambda k: k[0]):
            temp.append(item)
            bin_costs = []
            for g in group:
                bin_costs.append(y[g[1]])
            perc_cost = np.percentile(bin_costs, [50])
            quant_y.append(perc_cost[0])
        quant_x = temp
        self.line_xy(quant_x, quant_y, f"Median {label}")
        return self
