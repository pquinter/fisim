"""
Event class for financial planning model
"""
import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt

from .flows import InOrOutPerYear


@dataclass
class Action:
    """
    Action to be taken by an Event

    Parameters
    ----------
    target : InOrOutPerYear
        The target object to apply the action to.
    action : str
        Name of the method to call on the target.
    params : Dict[str, Any]
        Parameters to pass to the target's method.
    """

    target: InOrOutPerYear
    action: str
    params: Dict[str, Any]

    def __post_init__(self):
        self.validate()

    def __str__(self) -> str:
        """Return the Action's target name."""
        return f"{self.target.__class__.__name__}.{self.action}"

    def _mock_call_action_with_params(self):
        """Mock calling the action with the provided parameters."""
        target_action = getattr(self.target, self.action)
        # Get the signature of the target action
        sig = inspect.signature(target_action)
        # Check if the provided parameters match the action;
        params_to_check = self.params.copy()
        if "year" in sig.parameters:
            # year comes from Event, so just mock it here if needed
            params_to_check["year"] = 2024
        sig.bind(**params_to_check)

    def validate(self):
        """
        Raise an error if the target does not have specified property or method,
        or if the parameters are invalid for the target's method.
        """
        try:
            self._mock_call_action_with_params()
        except AttributeError:
            raise ValueError(f"'{self.target.__class__.__name__}' has no action '{self.action}'")
        except TypeError as e:
            raise ValueError(
                f"Invalid parameters for action '{self.action}' "
                f"on '{self.target.__class__.__name__}': {str(e)}"
            )

    def apply(self):
        """Execute the target method with the provided parameters."""
        getattr(self.target, self.action)(**self.params)


@dataclass
class Event:
    """
    Base class for modeling one-time events.

    Parameters
    ----------
    name : str
        The name of the event.
    actions : List[Action]
        The actions to be taken by the event.
    year : int
        The year when the event occurs.

    Attributes
    ----------
    name : str
    year : int
    actions : List[Action]
    """

    name: str
    year: int
    actions: List[Action]

    def __post_init__(self):
        # Add year to all actions
        for action in self.actions:
            target_action = getattr(action.target, action.action)
            # Add year parameter if it method requires it
            if "year" in inspect.signature(target_action).parameters:
                action.params["year"] = self.year

    def __str__(self) -> str:
        """Return a string representation of the Event."""
        return (
            f"{self.name} (Year: {self.year}"
            + f", Actions: {', '.join(str(action) for action in self.actions)})"
        )

    def apply(self):
        """Apply the event's actions."""
        for action in self.actions:
            action.apply()

    def plot(self, ax: Optional[plt.Axes] = None, **kwargs) -> plt.Axes:
        """Plot event's year as a vertical line."""
        ax = ax or plt.gca()
        ax.axvline(x=self.year, linestyle="--", alpha=0.7, label=self.name, **kwargs)
        ax.legend()
        return ax
