"""
Main financial model class
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np

from .assets import Asset
from .events import Event
from .flows import Expense, InOrOutPerYear, TaxableIncome


@dataclass
class FinancialModel:
    """
    Main class for financial model.
    """

    revenues: List[InOrOutPerYear]
    expenses: List[InOrOutPerYear]
    assets: List[Asset]
    duration: int

    events: Optional[List[Event]] = None
    debt: Optional[InOrOutPerYear] = None  # type: ignore
    stocks_allocation: float = 0.7
    bonds_allocation: float = 0.3
    cash_buffer: int = 50_000

    enable_logging: bool = False
    logger: Optional[logging.Logger] = None

    def __post_init__(self):
        self.events = self.events or []
        self.enable_logging and self._enable_logging()
        self.debt = self.debt or InOrOutPerYear(
            name="Debt", initial_value=0, start_year=self.start_year, duration=self.duration + 1
        )
        self._validate_asset_allocation()

    def _validate_asset_allocation(self) -> None:
        """
        Raise an error if the total allocation is not 1.
        """
        total_allocation = sum(asset.allocation or 0 for asset in self.assets)
        if not np.isclose(total_allocation, 1):
            raise ValueError(f"Total assets allocation is {total_allocation} but must sum to 1.")

    @property
    def start_year(self) -> int:
        """
        Get the earliest start year from all financial planning moneys.
        """
        return min(money.start_year for money in self.all_moneys)

    @property
    def all_moneys(self) -> List[InOrOutPerYear]:
        """
        Get all financial planning moneys.
        """
        return self.revenues + self.expenses + self.assets

    def _enable_logging(self):
        """
        Turn on logging. Once enabled, add messages with self._log().
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Check if the logger already has handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info(f"FinancialModel initialized. Start year: {self.start_year}")

    def _log(self, level: str, message: str) -> None:
        """
        Log a message.
        """
        if self.logger:
            getattr(self.logger, level)(message)

    def get_events(self, year: int) -> List[Event]:
        """
        Get events for a given year.
        """
        events = [event for event in self.events if event.year == year]
        self._log("debug", f"Events for year {year}: {events}")
        return events

    def apply_events(self, year: int) -> None:
        for event in self.get_events(year):
            self._log("info", f"Applying event in year {year}: {event}")
            event.apply()

    def balance_cash_flow(self, year: int) -> int:
        """
        Subtract total expenses and debt from total revenues, and return the cash flow.
        """
        year_revenues = sum(revenue[year] for revenue in self.revenues)
        year_expenses = sum(expense[year] for expense in self.expenses) + self.debt[year]
        cash_flow = year_revenues - year_expenses
        self._log(
            "info",
            f"Revenues: {year_revenues:_}, Expenses: {year_expenses:_}, "
            f"Cash flow for year {year}: {cash_flow:_}",
        )
        return cash_flow

    def invest_pre_tax(self, year: int, amount: int) -> int:
        """
        Invest into pre-tax assets.
        Subtract amount invested from TaxableIncome.
        Return amount invested, depending on pre-tax assets' caps.
        """
        if amount <= 0:
            return 0

        pretax_assets = [asset for asset in self.assets if asset.pretax]
        total_amount_invested = self._invest_in_assets(year, amount, pretax_assets)

        if total_amount_invested > 0:
            self._withdraw_from_taxable_income(year, total_amount_invested)

        return total_amount_invested

    def invest(self, year: int, amount: int) -> None:
        """
        Invest amount into assets with cap, then according to allocation.
        """
        # First, allocate to assets with cap
        capped_assets = [asset for asset in self.assets if asset.cap_value != float("inf")]
        amount_invested = self._invest_in_assets(year, amount, capped_assets)
        amount_remaining = amount - amount_invested

        # Then, allocate to assets with allocation
        allocated_assets = [asset for asset in self.assets if asset.allocation is not None]
        allocated_amounts = [amount_remaining * asset.allocation for asset in allocated_assets]
        self._invest_in_assets(year, amount_remaining, allocated_assets, allocated_amounts)

    def _invest_in_assets(
        self, year: int, amount: int, assets: List[Asset], amounts: Optional[List[int]] = None
    ) -> int:
        """
        Helper method to invest in a list of assets.
        Returns the total amount invested.
        """
        total_invested = 0
        for i, asset in enumerate(assets):
            to_invest = amounts[i] if amounts else amount
            amount_invested = asset.deposit(year, to_invest)
            total_invested += amount_invested
            self._log("info", f"Invested in year {year}: {amount_invested:_} in {asset.name}")
        return total_invested

    def _withdraw_from_taxable_income(self, year: int, amount: int) -> None:
        """
        Helper method to withdraw investments from pre-tax income.
        """
        to_withdraw = amount
        for revenue in self.revenues:
            if isinstance(revenue, TaxableIncome):
                withdrawn = revenue.withdraw(year, to_withdraw)
                to_withdraw -= withdrawn
                self._log("info", f"Withdrew {withdrawn:_} from {revenue.name} in year {year}")
                if to_withdraw <= 0:
                    break

    def distribute_cash_flow(self, year: int, cash_flow: int) -> None:
        """
        Distribute cash flow to assets or debt.
        """
        if cash_flow < 0:
            self._log("info", f"Negative cash flow in year {year}. Withdrawing funds.")
            self.withdraw_funds(year, -cash_flow, self.assets)
        else:
            self._log("info", f"Positive cash flow in year {year}. Investing surplus.")
            self.invest(year, cash_flow)

    def withdraw_funds(self, year: int, amount: int, asset_order: List[Asset]) -> None:
        """
        Recursively withdraw funds from assets in order.
        """
        if amount <= 0 or not asset_order:
            self._log("info", f"Adding {amount:_} to debt for next year.")
            self.debt.add_to_base_value(year + 1, amount)
            return
        current_asset = asset_order[0]
        withdrawn = current_asset.withdraw(year, amount)
        remaining = amount - withdrawn
        self._log("info", f"Withdrew {withdrawn:_} from {current_asset.name} in year {year}")

        return self.withdraw_funds(year, remaining, asset_order[1:])

    def grow_assets(self, year: int) -> None:
        for asset in self.assets:
            asset.grow(year)
        self._log("debug", f"Assets grown for year {year}")

    def add_inflation(self, year: int) -> None:
        """
        Add inflation to all expenses.
        """
        for expense in self.expenses:
            expense.grow(year)

    def tax_revenues(self, year: int) -> None:
        """
        Subtract state and federal taxes from year's revenues.
        """
        for revenue in self.revenues:
            if isinstance(revenue, TaxableIncome):
                taxed_amount = revenue.tax(year)
                self._log("info", f"Taxed {taxed_amount:_} from {revenue.name} in year {year}")

    def run(self, duration: Optional[int] = None) -> None:
        """
        Run the financial planning simulation.
        """
        self._log("info", "Starting financial planning simulation")
        for year in range(self.start_year, self.start_year + (duration or self.duration)):
            self._log("info", f"Processing year {year}")
            self.apply_events(year)
            # Figure out how much cash to invest pre-tax.
            # TODO: probably there is a more accurate way to do this.
            cash_flow = self.balance_cash_flow(year)
            self.invest_pre_tax(year, cash_flow)
            self.tax_revenues(year)
            # Recalculate cash flow after taxes.
            cash_flow = self.balance_cash_flow(year)
            self.distribute_cash_flow(year, cash_flow)
            self.grow_assets(year)
            self.add_inflation(year)
        self._log("info", "Financial planning simulation completed")

    def _plot_values(
        self, values: List[Union[InOrOutPerYear, Event]], ax: Optional[plt.Axes] = None
    ) -> plt.Axes:
        """
        Plot values from InOrOutPerYears or its subclasses over financial planning duration.
        """
        ax = ax or plt.gca()
        for value in values:
            value.plot(duration=self.duration, ax=ax)
        return ax

    def plot_assets(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot assets over financial planning duration.
        """
        return self._plot_values(self.assets, ax)

    def plot_cash_flow(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot the expenses, revenues and debt over financial planning duration.
        """
        return self._plot_values(self.expenses + self.revenues + [self.debt], ax)  # type: ignore

    def plot_events(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot events as vertical lines.
        """
        ax = ax or plt.gca()
        for event in self.events:
            event.plot(ax=ax)
        return ax

    def plot_all(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot all values over financial planning duration.
        """
        ax = self.plot_assets(ax)
        self.plot_cash_flow(ax)
        self.plot_events(ax)
        return ax

    def _get_money_by_name(
        self, name: str, money_list: List[InOrOutPerYear]
    ) -> Optional[InOrOutPerYear]:
        """
        Filter a list of InOrOutPerYears or its subclasses by name.
        """
        for money in money_list:
            if money.name == name:
                return money
        return None

    def get_asset(self, name: str) -> Optional[Asset]:
        """
        Get an asset by name.
        """
        return self._get_money_by_name(name, self.assets)

    def get_expense(self, name: str) -> Optional[Expense]:
        """
        Get an expense by name.
        """
        return self._get_money_by_name(name, self.expenses)

    def get_revenue(self, name: str) -> Optional[InOrOutPerYear]:
        """
        Get a revenue by name.
        """
        return self._get_money_by_name(name, self.revenues)
