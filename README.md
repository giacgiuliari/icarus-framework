# The ICARUS Attack Simulator

This repository cointains the code for a new, extensible and customizable simulator for the ICARUS attack on satellite networks.  
More specifically, two libraries are provided:
* `icarus_simulator`: code for the ICARUS simulator;
* `sat_plotter`: a visualization utility for geographical and statistical plots.

## Usage instructions
The simulator is based on a few key classes.  

**`IcarusSimulator`:**  
Main interface of the library, it receives phases and executes them sequentially. It also manages the middle results, storing them in a key-value fashion, and the dependencies between phases. By passing different phases, the simulation algorithm can be fully adapted to the user's needs.

**`BasePhase`:**  
Phases are classes that manage the execution of a macrotask, and their execution always yields a milestone in the computation (e.g. the attack result for all ISLs in the network). They accept the keys for the inputs and outputs and get and save values directly into the simulator instance.  
Custom phases can be created by extending this class. The phase code is supposed to be a template, that gets its full behaviour through the use of strategies.

**`BaseStrategy`:**  
Strategies are classes that manage the execution of a microtask, following a specific signature.  They specify the behaviour when many alternatives would be possible, e.g. the chosen routing algorithm. They allow for a runtime decision of the detailed algorithm, allowing for easy prototyping and experimentation.  
Custom strategies can be created by extending this class.

The library already includes several predefined phases, used in the ICARUS attack, found in the directory `phases`.   
Predefined strategies can also be found in `strategies`, with a different subdirectory for each microtask.

Each base class features a detailed explanation. Please read the initial comment of `main.py` for more details and further instructions.


## Installation instructions

This project uses `pipenv` for dependency management.
To install the two libraries, checkout the project and navigate to the project directory, then run:
```bash
pipenv install .
```

After activating the virtual environment with ```pipenv shell```, run:
```bash
python setup.py install
```

If using the strategy `strategies/atk_feasibility_check/lp_feas_strat.py`, an installation of Gurobi is necessary, which requires additional steps. After registering for a free academic license, activate the license. To install, run the following command: 
```bash
pipenv install -i https://pypi.gurobi.com gurobipy
```
Refer to https://www.gurobi.com/documentation/9.1/quickstart_windows/cs_using_pip_to_install_gr.html for more info.

The two libraries are now available and can be imported as any other python packages. You can run the following as a first test:
```bash
python main.py
```


Important note:  
The simulations are very computation- and memory-heavy. Therefore, we recommend to run the simulator on a multicore cluster.


