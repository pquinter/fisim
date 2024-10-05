"""
Asset class for financial planning model
"""
from typing import Optional
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
    duration : int
        Number of years to model.

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
        **kwargs,
    ):
        multiplier = 1 + growth_rate
        kwargs["multiplier"] = multiplier
        super().__init__(**kwargs)
        # Assets are not recurrent
        self.base_value[1:] = 0
        self.cap_value = cap_value or float("inf")
        self.allocation = allocation

    def grow(self, year: int) -> None:
        """
        Grow the asset for a given year.
        """
        year_index = self._convert_year_to_index(year)
        if year_index + 1 < self.duration:
            self.base_value[year_index + 1] = (
                self.base_value[year_index] * self.multiplier[year_index]
            )

    def withdraw(self, year: int, amount: int) -> int:
        """
        Withdraw an amount from the asset for a given year.
        Returns the amount actually withdrawn.
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
        deposit = min(amount, space_left)
        self.base_value[year_index] += deposit
        return deposit