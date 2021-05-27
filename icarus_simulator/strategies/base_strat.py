#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
This class defines the abstraction for a strategy, passed to a phase to define a specific computation step.
This class is open for custom extension, in order to create different execution strategies for specific steps.

The methods name() and param_description() are used by the phase to manage naming.
The compute() method, contains the computation logic, and must be specified according to the task.

For extension examples, see the subdirectories. Every subdirectory contains strategies for a different task, and must
have a level 2 base class specifying the constructor and compute arguments and returns for the task. All __init__()
overrides must call the superclass init and must specify **kwargs in the parameters, to enable the configuration
mechanism (see configuration.py in the main directory).
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseStrat(ABC):
    def __init__(self, **kwargs):
        pass

    # Methods to override
    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def param_description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def compute(self, *args) -> Any:
        raise NotImplementedError

    # No override
    @property
    def description(self) -> str:
        conf_desc = "-"
        if self.param_description is not None:
            conf_desc = f"-{self.param_description}-"
        return f"{self.name}{conf_desc}"
