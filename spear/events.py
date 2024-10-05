"""
Event class for financial planning model
"""
from typing import List
from .flows import InOrOutPerYear


class Event:
    """
    Base class for modeling one-time events.

    Parameters
    ----------
    start_year : int
        The year when the event occurs.
    duration : int
        The duration of the event in years.
    affected_ios : List[InOrOutPerYear]
        List of InOrOutPerYear objects affected by this event.
    multiplier : float
        The multiplier to apply to the affected InOrOutPerYear objects.

    Attributes
    ----------
    start_year : int
        The year of the event.
    duration : int
        The duration of the event.
    affected_ios : List[InOrOutPerYear]
        The affected InOrOutPerYear objects.
    multiplier : float
        The multiplier to apply.
    """

    def __init__(
        self, start_year: int, duration: int, affected_ios: List[InOrOutPerYear], multiplier: float
    ):
        self.start_year = start_year
        self.duration = duration
        self.affected_ios = affected_ios
        self.multiplier = multiplier

    def __repr__(self):
        return f"Event(start_year={self.start_year}, duration={self.duration}, affected_ios={self.affected_ios}, multiplier={self.multiplier})"
