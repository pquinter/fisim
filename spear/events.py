"""
Event class for financial planning model
"""
import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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

    def validate(self):
        """
        Raise an error if the target does not have specified property or method,
        or if the parameters are invalid for the target's method.
        """
        try:
            target_action = getattr(self.target, self.action)
            # Get the signature of the target action
            sig = inspect.signature(target_action)
            # Check if the provided parameters match the action
            sig.bind(**self.params)
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
    start_year : int, optional
        The year when the event occurs.

    Attributes
    ----------
    name : str
    start_year : int
    actions : List[Action]
    """

    name: str
    actions: List[Action]
    start_year: Optional[int] = None

    def __post_init__(self):
        self.start_year = self.start_year or self.get_earliest_action_year()

    def get_earliest_action_year(self) -> int:
        """Get the earliest year from the event's actions."""
        all_years = [action.params.get("year", float("inf")) for action in self.actions]
        if min(all_years) == float("inf"):
            raise ValueError("`start_year` must be provided if no actions specify a year.")
        return min(all_years)

    def apply(self):
        """Apply the event's actions."""
        for action in self.actions:
            action.apply()
