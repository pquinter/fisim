"""
Asset class for financial planning model
"""
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from .flows import InOrOutPerYear


class Asset(InOrOutPerYear):
    """
    Class for modeling assets, inheriting from InOrOutPerYear.

    Parameters
    ----------
    initial_value : int
        Initial value of the asset.
    start_year : int
        The starting year for the asset.
    growth_rate : float
        Annual growth rate of the asset.
    allocation : Optional[float] = None
        Allocation of the asset in the portfolio.
        The sum of allocations across Assets passed to a FinancialModel must equal 1.
    cap_value : Optional[int] = None
        If asset reaches this value, no more deposits are allowed.
    pretax : bool = False
        Whether the asset is pretax (i.e., tax-deferred).
    cap_deposit: Optional[int] = None
        Maximum yearly amount to deposit into the asset.

    Attributes
    ----------
    base_value : np.ndarray[int]
        Array of base values.
    multiplier : np.ndarray[float]
        Array of multipliers.
    value: np.ndarray[int]
        Array of actual values.
    """

    def __init__(
        self,
        growth_rate: float,
        allocation: Optional[float] = None,
        cap_value: Optional[int] = None,
        pretax: bool = False,
        cap_deposit: Optional[int] = None,
        monte_carlo: bool = False,
        seed: Optional[int] = None,
        scale: float = 0.05,
        **kwargs,
    ):
        self.growth_rate = growth_rate
        kwargs["multiplier"] = 1 + self.growth_rate
        super().__init__(**kwargs)
        # Assets are not recurrent
        self.base_value[1:] = 0
        self.cap_value = cap_value or float("inf")
        self.cap_deposit = cap_deposit or float("inf")
        self.allocation = allocation
        self.pretax = pretax
        self.seed = seed
        self.scale = scale
        if monte_carlo:
            self._sample_growth_rates()

    def _sample_growth_rates(self):
        rng = np.random.default_rng(seed=self.seed)
        self.multiplier = rng.normal(loc=self.growth_rate, scale=self.scale, size=self.duration)
        self.multiplier += 1

    def withdraw(self, year: int, amount: int) -> int:
        """
        Withdraw an amount from the asset for a given year.
        Returns the amount actually withdrawn, based on available funds.
        """
        year_index = self._convert_year_to_index(year)
        available = self.base_value[year_index]
        withdrawn = min(amount, available)
        self.base_value[year_index] -= withdrawn
        return withdrawn

    def deposit(self, year: int, amount: int) -> int:
        """
        Deposit an optionally capped amount into the asset for a given year.
        Returns the amount actually deposited.
        """
        year_index = self._convert_year_to_index(year)
        space_left = max(0, self.cap_value - self.base_value[year_index])
        deposit = min(amount, space_left, self.cap_deposit)
        self.base_value[year_index] += deposit
        return deposit

    def update_cap_deposit(self, cap_deposit: int):
        self.cap_deposit = cap_deposit

    def plot_growth_rates(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot growth rates over time.
        """
        growth_rates = self.multiplier - 1
        ax = self._plot(duration, ax, growth_rates, **kwargs)
        return ax
