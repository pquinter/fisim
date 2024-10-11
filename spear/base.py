"""
Base classes for financial planning model
"""
import datetime
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class InOrOutPerYear:
    """
    Base class for modeling cash flows.

    Parameters
    ----------
    base_value : List[int]
        Money per year. Positive for revenue, negative for expenses.
    multiplier : List[float]
        Rate per year. Must be zero or positive.

    Attributes
    ----------
    base_value : np.ndarray[int]
        Array of base values.
    multiplier : np.ndarray[float]
        Array of multipliers.
    value: np.ndarray[int]
        Array of actual values.
    name: str
        Name of the InOrOutPerYear.
    """

    name: str
    initial_value: int
    start_year: Optional[int] = None
    duration: int = 100
    multiplier: float = 1

    def __post_init__(self):
        self.base_value = np.full(self.duration, self.initial_value, dtype=int)
        self.multiplier = np.full(self.duration, self.multiplier, dtype=float)
        self.start_year = self.start_year or self._get_current_year()
        self._validate_positive_values(self.base_value, "Base value")
        self._validate_positive_values(self.multiplier, "Multiplier")

    @staticmethod
    def _validate_positive_values(values: np.ndarray, name: str):
        if np.any(values < 0):
            raise ValueError(f"{name} must be zero or positive.")

    def __str__(self) -> str:
        """
        Return a string representation of the InOrOutPerYear object.
        """
        return (
            f"{self.name} (Start Year: {self.start_year}, "
            f"Initial Value: {self.initial_value}, Duration: {self.duration})"
        )

    def _get_current_year(self) -> int:
        return datetime.datetime.now().year

    def _convert_year_to_index(self, year: int) -> int:
        return year - self.start_year

    def _get_value(self, year: int, array: np.ndarray) -> int:
        """
        Get the value for the specified year from array.
        Return 0 if year is outside array.
        """
        year_index = self._convert_year_to_index(year)
        try:
            return array[year_index]
        except IndexError:
            return 0

    def get_base_value(self, year: int) -> int:
        """
        Get the base value for the specified year.
        Return 0 if year is outside the duration of the object.
        """
        return self._get_value(year, self.base_value)

    def get_multiplier(self, year: int) -> float:
        """
        Get the multiplier for the specified year.
        Return 0 if year is outside the duration of the object.
        """
        return self._get_value(year, self.multiplier)

    def update_multiplier(self, year: int, multiplier: float):
        year_index = self._convert_year_to_index(year)
        self.multiplier[year_index] = multiplier

    def update_base_value(self, year: int, base_value: int, duration: Optional[int] = None):
        year_index = self._convert_year_to_index(year)
        self.base_value[year_index : year_index + (duration or 1)] = base_value

    def add_to_base_value(self, year: int, base_value: int, duration: Optional[int] = None):
        year_index = self._convert_year_to_index(year)
        self.base_value[year_index : year_index + (duration or 1)] += base_value

    def _plot(
        self,
        duration: Optional[int] = None,
        ax: Optional[plt.Axes] = None,
        array: np.ndarray = None,
        **kwargs,
    ) -> plt.Axes:
        """
        Plot base value or multiplier over time.
        """
        ax = ax or plt.gca()
        ax.plot(
            range(self.start_year, self.start_year + (duration or self.duration)),
            array[: duration or self.duration],
            label=self.name,
            **kwargs,
        )
        ax.set(
            xlabel="Year",
            ylabel="Value",
            xticks=range(self.start_year, self.start_year + (duration or self.duration)),
        )
        ax.tick_params(axis="x", rotation=60)
        ax.legend()
        ax.grid(True, alpha=0.3)
        return ax

    def plot(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot base values over time.
        """
        ax = self._plot(duration, ax, self.base_value, **kwargs)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f"{x/1e3:.0f}K" if x < 1e6 else f"{x/1e6:.1f}M")
        )
        return ax

    def plot_multipliers(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot multipliers over time.
        """
        ax = self._plot(duration, ax, self.multiplier, **kwargs)
        return ax

    def __getitem__(self, year: int) -> int:
        year_index = self._convert_year_to_index(year)
        return self.base_value[year_index]

    def grow(self, year: int) -> None:
        """
        Multiply the base value of specified year, and assign result to base value of next year.
        Can be used to model e.g. inflation or stock growth.
        """
        year_index = self._convert_year_to_index(year)
        if year_index + 1 < self.duration:
            self.base_value[year_index + 1] = (
                self.base_value[year_index] * self.multiplier[year_index]
            )
