"""
Asset class for financial planning model
"""
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from .flows import InOrOutPerYear
from .growth import (
    GrowthType,
    get_rebalancing_stock_allocations,
    sample_from_historical_growth_rates,
)
from .taxes import calculate_capital_gain_tax_rate, calculate_pretax_withdrawal_tax_rate


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
    """

    def __init__(
        self,
        growth_rate: Optional[float] = None,
        allocation: Optional[float] = None,
        cap_value: Optional[int] = None,
        pretax: bool = False,
        cap_deposit: Optional[int] = None,
        seed: int = 42,
        scale: float = 0.05,
        growth_type: Optional[GrowthType] = None,
        **kwargs,
    ):
        self.growth_rate = growth_rate
        self.allocation = allocation
        self.cap_value = cap_value or float("inf")
        self.cap_deposit = cap_deposit or float("inf")
        self.pretax = pretax
        self.seed = seed
        self.scale = scale
        self.growth_type = growth_type
        kwargs["multiplier"] = 1 + (self.growth_rate or 0)
        super().__init__(**kwargs)
        # Assets are not recurrent
        self.base_values[:, 1:] = 0
        if self.growth_type is not None:
            self._sample_growth_rates()

    def _validate_and_set_parameter(
        self, parameter: str, value: Any, validate_kwargs: Dict[str, Any]
    ):
        """
        Raise an error if parameter is specified to an unallowed value in `validate_kwargs`,
        and set it to the given value otherwise.
        """
        if parameter in validate_kwargs and validate_kwargs[parameter] != value:
            raise TypeError(f"Do not specify `{parameter}`, it is automatically set to {value}")
        validate_kwargs[parameter] = value

    def _sample_growth_rates(self):
        self.multipliers = 1 + sample_from_historical_growth_rates(
            self.growth_type, self.number_of_simulations, self.duration, self.seed
        )

    def prepare_simulations(self, number_of_simulations: int):
        """
        Expand base_values and multipliers to hold multiple simulations,
        and sample growth rates for each.
        """
        super().prepare_simulations(number_of_simulations)
        if self.growth_type is not None:
            self._sample_growth_rates()

    def deposit(self, year: int, amount: np.ndarray) -> np.ndarray:
        """
        Deposit an optionally capped amount into the asset for a given year.
        Returns the amount actually deposited.
        """
        available = self.get_base_values(year)
        space_left = np.maximum(0, self.cap_value - available)
        deposit = np.minimum(amount, np.minimum(space_left, self.cap_deposit))
        self.update_base_values(year, available + deposit)
        return deposit

    def update_cap_deposit(self, cap_deposit: int):
        self.cap_deposit = cap_deposit

    def plot_growth_rates(
        self, duration: Optional[int] = None, ax: Optional[plt.Axes] = None, **kwargs
    ) -> plt.Axes:
        """
        Plot growth rates over time.
        """
        growth_rates = self.multipliers - 1
        ax = self._plot(duration, ax, growth_rates, **kwargs)
        return ax


class TaxableAsset(Asset):
    """
    Taxable assets are taxed upon withdrawal as long-term capital gains.
    """

    def prepare_simulations(self, number_of_simulations: int):
        """
        Expand base_values and multipliers to hold multiple simulations,
        sample growth rates for each, and initialize cumulative capital gains.
        """
        super().prepare_simulations(number_of_simulations)
        self.cumulative_capital_gains = np.full(
            (self.number_of_simulations, self.duration), 0, dtype=np.int64
        )

    def get_cumulative_capital_gains(self, year: int) -> np.ndarray:
        """
        Get the cumulative capital gains for a given year.
        """
        year_index = self._convert_year_to_index(year)
        return self.cumulative_capital_gains[:, year_index]

    def update_cumulative_capital_gains(self, year: int, gains: np.ndarray) -> None:
        """
        Update the cumulative capital gains for a given year.
        """
        year_index = self._convert_year_to_index(year)
        self.cumulative_capital_gains[:, year_index] = gains

    def grow(self, year: int) -> np.ndarray:
        """
        Multiply the base value of specified year, assign result to next year,
        and track long-term capital gains.
        """
        gains = super().grow(year)
        previous_cumulative_gains = self.get_cumulative_capital_gains(year)
        self.update_cumulative_capital_gains(year + 1, previous_cumulative_gains + gains)
        return gains

    def _calculate_gross_withdrawal(
        self,
        year: int,
        net_amount: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the gross withdrawal amount needed to achieve as much of the desired net amount
        as possible, after accounting for capital gains tax.

        Parameters
        ----------
        year : int
            The year for which to calculate the withdrawal.
        net_amount : np.ndarray
            The desired net amount after taxes.

        Returns
        -------
        np.ndarray
            The gross withdrawal amount needed.
        """
        available = self.get_base_values(year)
        cumulative_gains = self.get_cumulative_capital_gains(year)

        # Calculate the proportion of the withdrawal that is capital gains
        gain_ratio = np.divide(  # Avoid division by zero errors
            cumulative_gains,
            available,
            out=np.zeros_like(available, dtype=float),
            where=available != 0,
        )

        # Initial guess for gross withdrawal
        gross_withdrawn = net_amount / (1 - 0.15 * gain_ratio)  # Using 15% as initial guess
        gross_withdrawn = np.where(gross_withdrawn >= available, available, gross_withdrawn)

        # Iterate to find the correct gross amount
        for _ in range(5):  # Usually converges within a few iterations
            capital_gains = gross_withdrawn * gain_ratio
            total_taxable_income = capital_gains
            tax_rate = calculate_capital_gain_tax_rate(total_taxable_income)
            gross_withdrawn = np.where(
                gross_withdrawn >= available, available, net_amount / (1 - tax_rate * gain_ratio)
            )
        net_withdrawn = gross_withdrawn - capital_gains * tax_rate
        return gross_withdrawn, net_withdrawn, capital_gains

    def withdraw(
        self,
        year: int,
        amount: np.ndarray,
    ) -> np.ndarray:
        """
        Withdraw amount from the asset for a given year, accounting for capital gains tax.
        Return the net amount withdrawn after taxes, which can be subtracted
        from the requested amount to balance the cash flow.

        Parameters
        ----------
        year : int
            The year for which to calculate the withdrawal.
        amount : np.ndarray
            The desired net withdrawal amount.

        Returns
        -------
        np.ndarray
            The net amount withdrawn after taxes.
        """
        available = self.get_base_values(year)
        (
            gross_withdrawn,
            net_withdrawn,
            capital_gains,
        ) = self._calculate_gross_withdrawal(year, amount)
        self.update_cumulative_capital_gains(
            year, self.get_cumulative_capital_gains(year) - capital_gains
        )
        self.update_base_values(year, available - gross_withdrawn)
        return net_withdrawn


class TaxablePortfolio(Asset):
    """
    Taxable portfolio that simulates a mix of bonds and stocks, with a growth rate for each,
    and an allocation that rebalances according to:

        stocks_allocation = (120 - age) / 100
        bonds_allocation = 1 - stocks_allocation

    Instead of having separate assets for stocks and bonds, by having a single asset with a
    weighted average growth rate, we simulate the behavior of a taxable portfolio that
    rebalances its allocation between stocks and bonds every year.
    """

    def __init__(
        self,
        age: int,
        **kwargs,
    ):
        self.age = age
        # Set so that _sample_growth_rates is called
        self._validate_and_set_parameter("growth_type", GrowthType.PORTFOLIO, kwargs)
        super().__init__(**kwargs)

    @property
    def stock_allocations(self) -> np.ndarray:
        return get_rebalancing_stock_allocations(self.age, self.duration)

    @property
    def bond_allocations(self) -> np.ndarray:
        return 1 - self.stock_allocations

    def _sample_growth_rates(self):
        """
        Sample growth rates that simulate a mix of stocks and bonds,
        with the allocation between stocks and bonds changing over time.
        """
        stocks_growth = sample_from_historical_growth_rates(
            GrowthType.STOCKS, self.number_of_simulations, self.duration, self.seed
        )
        bonds_growth = sample_from_historical_growth_rates(
            GrowthType.BONDS, self.number_of_simulations, self.duration, self.seed
        )
        # Combine growth rates based on allocation
        self.multipliers = 1 + (
            self.stock_allocations * stocks_growth + self.bond_allocations * bonds_growth
        )

    def plot(
        self,
        duration: Optional[int] = None,
        ax: Optional[plt.Axes] = None,
        split: bool = False,
        **kwargs,
    ) -> plt.Axes:
        """
        Plot the portfolio over time.

        Parameters
        ----------
        duration : Optional[int]
            The duration to plot.
        ax : Optional[plt.Axes]
            The axes to plot on.
        split : bool
            Whether to plot stocks and bonds separately.

        Returns
        -------
        plt.Axes
            The axes with the plot.
        """
        ax = ax or plt.gca()
        if split:
            stocks = self.stock_allocations * self.base_values
            bonds = self.bond_allocations * self.base_values
            ax = self._plot(duration, ax, stocks, label=f"{self.name} (Stocks)", **kwargs)
            ax = self._plot(duration, ax, bonds, label=f"{self.name} (Bonds)", **kwargs)
        else:
            ax = self._plot(duration, ax, self.base_values, label=f"{self.name}", **kwargs)
        return ax


class PretaxAsset(Asset):
    """
    Pretax assets are subject to income tax, and may be subject to early withdrawal penalty.

    Parameters
    ----------
    In addition to the parameters for Asset, PretaxAsset takes:
    age : Optional[int] = None
        Age of the investor to determine whether early withdrawal penalty applies.
        Required when withdrawing from the asset.
    state : Optional[str] = None
        To calculate state income tax.
        Required when withdrawing from the asset.
    """

    def __init__(self, age: int, state: str, **kwargs):
        self.age = age
        self.state = state
        self._validate_and_set_parameter("pretax", True, kwargs)
        super().__init__(**kwargs)

    def _calculate_gross_withdrawal(
        self,
        year: int,
        net_amount: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate the gross withdrawal amount needed to achieve as much of the desired net amount
        as possible, after accounting for income tax and early withdrawal penalty.

        Parameters
        ----------
        year : int
            The year for which to calculate the withdrawal.
        net_amount : np.ndarray
            The desired net withdrawal amount.
        """
        available = self.get_base_values(year)
        tax_rate = calculate_pretax_withdrawal_tax_rate(net_amount, self.state, self.age)

        # Initial guess for gross withdrawal
        gross_withdrawn = net_amount / (1 - tax_rate)
        gross_withdrawn = np.where(gross_withdrawn >= available, available, gross_withdrawn)

        # Iterate to find the correct gross amount
        for _ in range(5):  # Usually converges within a few iterations
            tax_rate = calculate_pretax_withdrawal_tax_rate(gross_withdrawn, self.state, self.age)
            gross_withdrawn = np.where(
                gross_withdrawn >= available, available, net_amount / (1 - tax_rate)
            )
        net_withdrawn = gross_withdrawn - gross_withdrawn * tax_rate
        return gross_withdrawn, net_withdrawn

    def _validate_withdrawal_parameters(self) -> None:
        if self.age is None or self.state is None:
            raise ValueError("Age and state must be set before withdrawing from a pretax asset")

    def withdraw(
        self,
        year: int,
        amount: np.ndarray,
    ) -> np.ndarray:
        """
        Withdraw amount from the asset for a given year, accounting for income
        tax and early withdrawal penalty.
        Return the net amount withdrawn after taxes, which can be subtracted
        from the requested amount to balance the cash flow.

        Parameters
        ----------
        year : int
            The year for which to calculate the withdrawal.
        amount : np.ndarray
            The desired net withdrawal amount.

        Returns
        -------
        np.ndarray
            The net amount withdrawn after taxes.
        """
        self._validate_withdrawal_parameters()
        gross_withdrawn, net_withdrawn = self._calculate_gross_withdrawal(year, amount)
        available = self.get_base_values(year)
        self.update_base_values(year, available - gross_withdrawn)
        return net_withdrawn


class PretaxPortfolio(PretaxAsset):
    """
    Pretax portfolio that simulates a mix of bonds and stocks, with a set growth rate for each,
    and an allocation that rebalances according to:

        stocks_allocation = (120 - age) / 100
        bonds_allocation = 1 - stocks_allocation
    """

    def __init__(self, **kwargs):
        # Set so that _sample_growth_rates is called
        self._validate_and_set_parameter("growth_type", GrowthType.PORTFOLIO, kwargs)
        super().__init__(**kwargs)

    @property
    def stock_allocations(self) -> np.ndarray:
        return get_rebalancing_stock_allocations(self.age, self.duration)

    @property
    def bond_allocations(self) -> np.ndarray:
        return 1 - self.stock_allocations

    def _sample_growth_rates(self):
        """
        Sample growth rates that simulate a mix of stocks and bonds,
        with the allocation between stocks and bonds changing over time.
        """
        stocks_growth = sample_from_historical_growth_rates(
            GrowthType.STOCKS, self.number_of_simulations, self.duration, self.seed
        )
        bonds_growth = sample_from_historical_growth_rates(
            GrowthType.BONDS, self.number_of_simulations, self.duration, self.seed
        )
        # Combine growth rates based on allocation
        self.multipliers = 1 + (
            self.stock_allocations * stocks_growth + self.bond_allocations * bonds_growth
        )

    def plot(
        self,
        duration: Optional[int] = None,
        ax: Optional[plt.Axes] = None,
        split: bool = False,
        **kwargs,
    ) -> plt.Axes:
        """
        Plot the portfolio over time.

        Parameters
        ----------
        duration : Optional[int]
            The duration to plot.
        ax : Optional[plt.Axes]
            The axes to plot on.
        split : bool
            Whether to plot stocks and bonds separately.

        Returns
        -------
        plt.Axes
            The axes with the plot.
        """
        ax = ax or plt.gca()
        if split:
            stocks = self.stock_allocations * self.base_values
            bonds = self.bond_allocations * self.base_values
            ax = self._plot(duration, ax, stocks, label=f"{self.name} (Stocks)", **kwargs)
            ax = self._plot(duration, ax, bonds, label=f"{self.name} (Bonds)", **kwargs)
        else:
            ax = self._plot(duration, ax, self.base_values, label=f"{self.name}", **kwargs)
        return ax
