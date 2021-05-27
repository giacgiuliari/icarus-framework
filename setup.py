#  2020 Tommaso Ciussani and Giacomo Giuliari
import setuptools

setuptools.setup(
    name="icarus_simulator",
    version="0.0.1",
    author="Tommaso Ciussani",
    author_email="tommasoc@student.ethz.ch",
    description="Simulator for the Icarus attack",
    packages=["icarus_simulator"],
    python_requires=">=3.6",
)

setuptools.setup(
    name="sat_plotter",
    version="0.0.1",
    author="Tommaso Ciussani",
    author_email="tommasoc@student.ethz.ch",
    description="Plot builders for satellite networks",
    packages=["sat_plotter"],
    python_requires=">=3.6",
)
