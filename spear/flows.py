"""
Base classes for financial planning model
"""
import datetime
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from spear.constants import STATE_TAX_RATES
from spear.utilities import calculate_total_tax


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

    def get_base_value(self, year: int) -> int:
        year_index = self._convert_year_to_index(year)
        return self.base_value[year_index]

    def get_multiplier(self, year: int) -> float:
        year_index = self._convert_year_to_index(year)
        return self.multiplier[year_index]

    def mutate_multiplier(self, year: int, multiplier: float):
        year_index = self._convert_year_to_index(year)
        self.multiplier[year_index] = multiplier

    def mutate_base_value(self, year: int, base_value: int):
        year_index = self._convert_year_to_index(year)
        self.base_value[year_index] = base_value

    def add_to_base_value(self, year: int, base_value: int):
        year_index = self._convert_year_to_index(year)
        self.base_value[year_index] += base_value

    def plot(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        ax = ax or plt.gca()
        ax.plot(
            range(self.start_year, self.start_year + (duration or self.duration)),
            self.base_value[: duration or self.duration],
            label=self.name,
            **kwargs,
        )
        ax.set(
            xlabel="Year",
            ylabel="Value",
            xticks=range(self.start_year, self.start_year + (duration or self.duration)),
        )
        ax.tick_params(axis="x", rotation=60)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f"{x/1e3:.0f}K" if x < 1e6 else f"{x/1e6:.1f}M")
        )
        ax.legend()
        ax.grid(True, alpha=0.3)
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


class Expense(InOrOutPerYear):
    """
    Expense per year with inflation.
    """

    def __init__(self, inflation_rate: float, **kwargs):
        multiplier = 1 + inflation_rate
        kwargs["multiplier"] = multiplier
        super().__init__(**kwargs)


class TaxableIncome(InOrOutPerYear):
    """
    Income per year with tax rate.
    """

    def __init__(self, state: str, **kwargs):
        self.state = state
        self._validate_state()
        super().__init__(**kwargs)

    def _validate_state(self):
        if self.state not in STATE_TAX_RATES:
            raise ValueError(f"Unsupported state: {self.state}")

    def tax_income(self, year: int) -> None:
        year_index = self._convert_year_to_index(year)
        self.base_value[year_index] -= calculate_total_tax(self.base_value[year_index], self.state)

    def withdraw(self, year: int, amount: int, pre_tax: bool = False) -> int:
        year_index = self._convert_year_to_index(year)
        if pre_tax:
            self.base_value[year_index] -= amount
        else:
            total_tax = calculate_total_tax(self.base_value[year_index], self.state)
            # First tax the amount, then withdraw
            self.base_value[year_index] -= total_tax
            self.base_value[year_index] -= amount
        return amount
