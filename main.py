#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Example usage of the icarus_simulator and sat_plotter libraries.
This file makes use of the configuration mechanism, described in configuration.py.

For general information on the library usage, refer to readme.md and to the following files:
    - icarus_simulator/icarus_simulator.py,
    - icarus_simulator/phases/base_phase.py,
    - icarus_simulator/strategies/base_strategy.py,
    - icarus_simulator/structure_definitions,
    - icarus_simulator/multiprocessor.py

This file first exemplifies the creation of the computation phases and the simulation execution, then extracts data
from the IcarusSimulator object and creates useful plots.
After adjusting the class constants, execute the file to create the plots and the result dumps.
Due to the computational burden, it is advised to always run this library on a heavy-multicore machine.
"""
from statistics import mean

from icarus_simulator.icarus_simulator import IcarusSimulator
from icarus_simulator.default_properties import *
from icarus_simulator.phases import *
from sat_plotter import GeoPlotBuilder
from sat_plotter.stat_plot_builder import StatPlotBuilder

from configuration import CONFIG, parse_config, get_strat

# Change these parameters to match your machine
CORE_NUMBER = 30
RESULTS_DIR = "result_dumps"


def main():

    # Optional feature: parse the configuration file
    full_conf = parse_config(CONFIG)

    for conf_id, conf in enumerate(full_conf):
        # Repeat the simulation process for all configurations in the config file
        print(
            "---------------------------------------------------------------------------------"
        )
        print(f"Configuration number {conf_id}")  # 0-based

        # SIMULATION: phase definition and final computation
        lsn_ph = LSNPhase(
            True,
            True,
            lsn_strat=get_strat("lsn", conf),
            lsn_out=SAT_POS,
            nw_out=SAT_NW,
            isls_out=SAT_ISLS,
        )

        grid_ph = GridPhase(
            True,
            True,
            grid_strat=get_strat("grid", conf),
            weight_strat=get_strat("gweight", conf),
            grid_out=FULL_GRID_POS,
            size_out=GRID_FULL_SZ,
        )

        cov_ph = CoveragePhase(
            True,
            True,
            cov_strat=get_strat("cover", conf),
            sat_in=SAT_POS,
            grid_in=FULL_GRID_POS,
            cov_out=COVERAGE,
            grid_out=GRID_POS,
        )

        rout_ph = RoutingPhase(
            True,
            True,
            CORE_NUMBER,
            2,
            rout_strat=get_strat("rout", conf),
            grid_in=GRID_POS,
            cov_in=COVERAGE,
            nw_in=SAT_NW,
            paths_out=PATH_DATA,
        )

        edge_ph = EdgePhase(
            True,
            True,
            CORE_NUMBER,
            1,
            ed_strat=get_strat("edges", conf),
            paths_in=PATH_DATA,
            nw_in=SAT_NW,
            sats_in=SAT_POS,
            grid_in=GRID_POS,
            edges_out=EDGE_DATA,
        )

        # FULL_GRID_POS is passed for consistency with other experiments, where the coverage grid filtering is different
        bw_ph = TrafficPhase(
            True,
            True,
            select_strat=get_strat("bw_sel", conf),
            assign_strat=get_strat("bw_asg", conf),
            grid_in=FULL_GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_out=BW_DATA,
        )

        latk_ph = LinkAttackPhase(
            True,
            True,
            CORE_NUMBER,
            3,
            geo_constr_strat=get_strat("atk_constr", conf),
            filter_strat=get_strat("atk_filt", conf),
            feas_strat=get_strat("atk_feas", conf),
            optim_strat=get_strat("atk_optim", conf),
            grid_in=GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_in=BW_DATA,
            latk_out=ATK_DATA,
        )

        zatk_ph = ZoneAttackPhase(
            True,
            True,
            CORE_NUMBER,
            4,
            geo_constr_strat=get_strat("atk_constr", conf),
            zone_select_strat=get_strat("zone_select", conf),
            zone_build_strat=get_strat("zone_build", conf),
            zone_edges_strat=get_strat("zone_edges", conf),
            zone_bneck_strat=get_strat("zone_bneck", conf),
            atk_filter_strat=get_strat("atk_filt", conf),
            atk_feas_strat=get_strat("atk_feas", conf),
            atk_optim_strat=get_strat("atk_optim", conf),
            grid_in=GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_in=BW_DATA,
            atk_in=ATK_DATA,
            zatk_out=ZONE_ATK_DATA,
        )

        sim = IcarusSimulator(
            [lsn_ph, grid_ph, cov_ph, rout_ph, edge_ph, bw_ph, latk_ph, zatk_ph],
            RESULTS_DIR,
        )
        sim.compute_simulation()
        print("Computation finished")

        # EXAMPLE PLOTS
        # GEOGRAPHICAL PLOTS
        sat_pos, isls, grid_pos = (
            sim.get_property(SAT_POS),
            sim.get_property(SAT_ISLS),
            sim.get_property(GRID_POS),
        )
        edge_data, bw_data = sim.get_property(EDGE_DATA), sim.get_property(BW_DATA)
        path_data, atk_data = sim.get_property(PATH_DATA), sim.get_property(ATK_DATA)
        zatk_data = sim.get_property(ZONE_ATK_DATA)

        # As a first example, we plot the network as a background for other plots.
        # Note: for this plot, only outputs from lsn_ph are required, so Simulator([lsn_ph], BASEDIR) would work too
        # show() shows an interactive plot, save_to_file() plots to file
        GeoPlotBuilder().constellation(sat_pos, isls).show().save_to_file(
            "01_const_bckg.png"
        )

        # Plot the grid with weights. The points are automatically bigger.
        pt_vals = {idx: val.weight for idx, val in grid_pos.items()}
        GeoPlotBuilder().set_transparency(False).point_heatmap(
            grid_pos, pt_vals
        ).save_to_file("02_grid.png")

        # Plot the satellites, in 3d. There are three sizes (LOW, MED, HI), complex plots use them
        GeoPlotBuilder().set_point_thickness(6, 15, 19).set_2d(False).constellation(
            sat_pos, isls
        ).points(sat_pos, "red", GeoPlotBuilder.HI, "SAT").save_to_file("03_sats.png")

        # Plot the ISL centrality heatmap
        isl_vals = {
            e: mean([edge_data[e].centrality, edge_data[(e[1], e[0])].centrality])
            for e in edge_data
            if -1 not in e and e[0] < e[1]
        }
        GeoPlotBuilder().isl_heatmap(sat_pos, isl_vals).save_to_file(
            "04_centrality.png"
        )

        # Plot the coverage centrality, everything is re-set to the defaults
        isl_vals = {
            e: mean([edge_data[e].cov_centr, edge_data[(e[1], e[0])].cov_centr])
            for e in edge_data
            if -1 not in e and e[0] < e[1]
        }
        GeoPlotBuilder().set_transparency(True).set_line_thickness(
            3, 6, 9
        ).set_point_thickness(6, 12, 16).set_2d(False).isl_heatmap(
            sat_pos, isl_vals
        ).save_to_file(
            "05_coverage_centrality.png"
        )

        # Plot the bandwidth
        isl_vals = {
            e: mean([bw_data[e].idle_bw, bw_data[(e[1], e[0])].idle_bw])
            for e in bw_data
            if -1 not in e and e[0] < e[1]
        }
        pt_vals = {
            e[1]: mean([bw_data[e].idle_bw, bw_data[(e[1], e[0])].idle_bw])
            for e in bw_data
            if e[0] == -1
        }
        GeoPlotBuilder().isl_heatmap(sat_pos, isl_vals).point_heatmap(
            sat_pos, pt_vals
        ).save_to_file("06_bandwidth.png")

        # Plot attackable links
        ordered_keys = [e for e in atk_data if -1 not in e and e[0] < e[1]]
        set_ord = set(e for e in ordered_keys if atk_data[e] is not None)
        set_rev = set(e for e in ordered_keys if atk_data[(e[1], e[0])] is not None)
        no_way = set(ordered_keys).difference(set_ord).difference(set_rev)
        both_ways = set_ord.intersection(set_rev)
        one_way = set_ord.union(set_rev).difference(both_ways)
        GeoPlotBuilder().path_list(
            sat_pos,
            grid_pos,
            list(both_ways),
            "rgba(144,230,138,0.8)",
            GeoPlotBuilder.MED,
        ).path_list(
            sat_pos, grid_pos, list(one_way), "rgba(243,166,12,0.8)", GeoPlotBuilder.MED
        ).path_list(
            sat_pos, grid_pos, list(no_way), "rgba(243,12,43,0.8)", GeoPlotBuilder.MED
        ).save_to_file(
            "07_atk_isls.png"
        )

        # Complex plot: plot the most complicated attack
        b_ed = min(
            [ed for ed in atk_data if atk_data[ed] is not None and -1 not in ed],
            key=lambda k: atk_data[k].detectability,
        )
        allowed_sources = get_strat("atk_constr", conf).compute(grid_pos)
        direction_data = get_strat("atk_filt", conf).compute(
            [b_ed], edge_data, path_data, allowed_sources
        )
        pair_direction = {}
        for dire, pairs in direction_data.items():
            for pair in pairs:
                pair_direction[pair] = [-pair[0]] + list(dire[1:])  # Insert also uplink
        paths = [pair_direction[pair_tup[0]] for pair_tup in atk_data[b_ed].atkflowset]
        GeoPlotBuilder().path_list(
            sat_pos, grid_pos, paths, "rgba(0,0,255,0.8)", GeoPlotBuilder.MED
        ).arrow(
            sat_pos[b_ed[0]],
            sat_pos[b_ed[1]],
            "rgba(255,0,0,1.0)",
            GeoPlotBuilder.HI,
            "TRG",
        ).save_to_file(
            "08_atk_viz.png"
        )

        # Complex plot: plot a zone attack setup
        b_zones = min(
            [zs for zs in zatk_data if zatk_data[zs] is not None],
            key=lambda k: len(zatk_data[k].bottlenecks)
            / len(zatk_data[k].cross_zone_paths),
        )
        zatk = zatk_data[b_zones]
        zone1, zone2 = b_zones
        cross = [p[1:-1] for p in zatk.cross_zone_paths]
        GeoPlotBuilder().path_list(
            sat_pos, grid_pos, cross, "rgba(0,0,255,0.8)", GeoPlotBuilder.MED
        ).points(
            {p_id: grid_pos[p_id] for p_id in zone1}, "green", GeoPlotBuilder.MED, "Z1"
        ).points(
            {p_id: grid_pos[p_id] for p_id in zone2}, "red", GeoPlotBuilder.MED, "Z1"
        ).path_list(
            sat_pos, grid_pos, zatk.bottlenecks, "orange", GeoPlotBuilder.HI
        ).save_to_file(
            "09_zone_atk.png"
        )

        # STATISTICAL PLOTS
        # CDF of attack cost on ISL, defaults
        costs = [
            val.cost / conf["bw_asg"]["isl_bw"]
            for ed, val in atk_data.items()
            if val is not None and -1 not in ed
        ]
        StatPlotBuilder().cdf(costs, "Example").labels(
            "ISL cost", "CDF"
        ).set_zero_y().save_to_file("10_cost_cdf.png")

        # PDF of attack detectability on ISL
        detects = [
            val.detectability / conf["bw_asg"]["udl_bw"]
            for ed, val in atk_data.items()
            if val is not None and -1 not in ed
        ]
        StatPlotBuilder().set_bins(30).set_size(14, 5).set_thickness(5).pdf(
            detects, "Example"
        ).labels("ISL detectability", "PDF").set_zero_y().save_to_file(
            "11_detectability_pdf.png"
        )

        # Binned linear plot of detectability over cost
        StatPlotBuilder().set_bins(10).binned_line_xy(costs, detects, "Example").labels(
            "ISL cost", "ISL detectability"
        ).set_zero_y().save_to_file("12_detect_cost.png")

        # CDFs of zone attack cost and distance, defaults
        costs = [
            val.cost / conf["bw_asg"]["isl_bw"]
            for val in zatk_data.values()
            if val is not None
        ]
        detects = [
            val.detectability / conf["bw_asg"]["udl_bw"]
            for val in zatk_data.values()
            if val is not None
        ]
        StatPlotBuilder().cdf(costs, "Cost CDF").cdf(
            detects, "Detectability CDF"
        ).labels("", "CDF").set_zero_y().legend().save_to_file(
            "13_zone_cost_detect_cdf.png"
        )

        # Scatter plot of zone attack cost over distance
        distances = [
            val.distance / 1000 for val in zatk_data.values() if val is not None
        ]
        StatPlotBuilder().point_xy(x=distances, y=costs, label="Zone attacks").labels(
            "Distance[km]", "Cost"
        ).save_to_file("14_zone_scatter_cost_distance.png")

        # Binned linear plot of zone attack detectability over cost
        StatPlotBuilder().set_bins(10).point_xy(
            x=costs, y=detects, label="Example"
        ).labels("Attack cost", "Attack detectability").set_zero_y().save_to_file(
            "15_zone_detect_cost.png"
        )


# Execute on main
if __name__ == "__main__":
    main()
