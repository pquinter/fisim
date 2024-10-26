"""
Base classes for financial planning model
"""
import datetime
from dataclasses import dataclass
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class InOrOutPerYear:
    """
    Base class for modeling cash flows.

    Attributes
    ----------

    name: str
        Name of the InOrOutPerYear.
    base_values : np.ndarray[int]
        Array of base values.
    multipliers : np.ndarray[float]
        Array of multipliers.
    """

    name: str
    initial_value: int
    start_year: Optional[int] = None
    duration: int = 100
    multiplier: float = 1
    number_of_simulations: int = 1

    def __post_init__(self):
        self.prepare_simulations(self.number_of_simulations)
        self.start_year = self.start_year or self._get_current_year()
        self._validate_positive_values(self.base_values, "Base value")
        self._validate_positive_values(self.multipliers, "Multiplier")

    @staticmethod
    def _validate_positive_values(values: np.ndarray, name: str):
        if np.any(values < 0):
            raise ValueError(f"{name} must be zero or positive.")

    def __str__(self) -> str:
        return (
            f"{self.name} (Start Year: {self.start_year}, "
            f"Initial Value: {self.initial_value}, Duration: {self.duration})"
        )

    def _get_current_year(self) -> int:
        return datetime.datetime.now().year

    def _convert_year_to_index(self, year: int) -> int:
        return year - self.start_year

    def _get_values(self, year: int, array: np.ndarray) -> np.ndarray:
        """
        Get the values for the specified year from array.
        Return zeros if year is outside the array.
        """
        year_index = self._convert_year_to_index(year)
        try:
            return array[:, year_index]
        except IndexError:
            return np.zeros(self.number_of_simulations)

    def get_base_values(self, year: int) -> np.ndarray:
        """
        Get the base values for the specified year.
        Return zeros if year is outside the duration of the object.
        """
        return self._get_values(year, self.base_values)

    def get_multipliers(self, year: int) -> np.ndarray:
        """
        Get the multipliers for the specified year.
        Return zeros if year is outside the duration of the object.
        """
        return self._get_values(year, self.multipliers)

    def _update_values(
        self,
        year: int,
        new_values: Union[float, np.ndarray],
        array: np.ndarray,
        duration: Optional[int] = None,
    ):
        year_index = self._convert_year_to_index(year)
        if isinstance(new_values, np.ndarray):
            new_values = new_values.reshape(-1, 1)
        array[:, year_index : year_index + (duration or 1)] = new_values

    def update_multipliers(self, year: int, new_multipliers: Union[float, np.ndarray]):
        self._update_values(year, new_multipliers, self.multipliers)

    def update_base_values(
        self,
        year: int,
        new_base_values: Union[int, np.ndarray],
        duration: Optional[int] = None,
    ):
        self._update_values(year, new_base_values, self.base_values, duration)

    def add_to_base_values(
        self,
        year: int,
        to_add: Union[int, np.ndarray],
        duration: Optional[int] = None,
    ):
        self.update_base_values(year, self.get_base_values(year) + to_add, duration)

    def withdraw(self, year: int, amount: np.ndarray) -> np.ndarray:
        """
        Withdraw amount from the object for a given year.
        Return amount withdrawn, depending on available funds.
        """
        available = self.get_base_values(year)
        amount_withdrawn = np.minimum(amount, available)
        self.update_base_values(year, available - amount_withdrawn)
        return amount_withdrawn

    def _plot(
        self,
        duration: Optional[int] = None,
        ax: Optional[plt.Axes] = None,
        array: np.ndarray = None,
        label: Optional[str] = None,
        **kwargs,
    ) -> plt.Axes:
        """
        Plot base value or multiplier over time.
        """
        ax = ax or plt.gca()

        plot_duration = duration or self.duration
        years = range(self.start_year, self.start_year + plot_duration)

        # Calculate statistics
        median_values = np.median(array[:, :plot_duration], axis=0)
        lower_bound = np.percentile(array[:, :plot_duration], 5, axis=0)
        upper_bound = np.percentile(array[:, :plot_duration], 95, axis=0)

        # Plot median value
        ax.plot(years, median_values, label=label or self.name, **kwargs)

        # Plot confidence interval
        ax.fill_between(years, lower_bound, upper_bound, alpha=0.2)

        ax.set(
            xlabel="Year",
            ylabel="Value",
            xticks=range(self.start_year, self.start_year + (duration or self.duration)),
        )
        ax.tick_params(axis="x", rotation=60)
        ax.legend()
        ax.grid(True, alpha=0.3)
        # Assume that the values are in dollars if they are greater than 1e3
        # And format y-axis labels to use thousands (k) or millions (M) notation
        if np.any(array >= 1e3):
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f"${x/1e6:.1f}M" if x >= 1e6 else f"${x/1e3:.0f}K")
            )
        return ax

    def plot(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot base values over time for all simulations.
        """
        ax = ax or plt.gca()
        self._plot(duration, ax, self.base_values, **kwargs)
        return ax

    def plot_multipliers(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot multipliers over time.
        """
        ax = self._plot(duration, ax, self.multipliers, **kwargs)
        return ax

    def __getitem__(self, year: int) -> np.ndarray:
        return self.get_base_values(year)

    def grow(self, year: int) -> np.ndarray:
        """
        Multiply the base value of specified year, and assign result to base value of next year.
        Can be used to model e.g. inflation or stock growth.
        """
        current_values = self.get_base_values(year)
        next_values = current_values * self.get_multipliers(year)
        growth = next_values - current_values
        self.update_base_values(year + 1, next_values)
        return growth

    def prepare_simulations(self, number_of_simulations: int):
        """
        Expand base_values and multipliers to hold multiple simulations.
        """
        self.number_of_simulations = number_of_simulations
        self.base_values = np.full(
            (self.number_of_simulations, self.duration), self.initial_value, dtype=np.int64
        )
        self.multipliers = np.full(
            (self.number_of_simulations, self.duration), self.multiplier, dtype=np.float64
        )
