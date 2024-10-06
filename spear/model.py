"""
Main financial model class
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np

from .assets import Asset
from .events import Event
from .flows import InOrOutPerYear


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
        return self.revenues + self.expenses + self.assets + self.events

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
        events = [event for event in self.events if event.start_year == year]
        self._log("debug", f"Events for year {year}: {events}")
        return events

    def apply_events(self, year: int) -> None:
        for event in self.get_events(year):
            self._log("info", f"Applying event in year {year}: {event}")
            for affected_io in event.affected_ios:
                start_year = event.start_year
                end_year = start_year + event.duration
                for y in range(start_year, end_year):
                    affected_io.mutate_multiplier(y, event.multiplier)

    def balance_cash_flow(self, year: int) -> int:
        """
        Subtract total expenses and debt from total revenues, and return the cash flow.
        """
        self.apply_events(year)
        year_revenues = sum(revenue[year] for revenue in self.revenues)
        year_expenses = sum(expense[year] for expense in self.expenses) + self.debt[year]
        cash_flow = year_revenues - year_expenses
        self._log(
            "info",
            f"Revenues: {year_revenues:_}, Expenses: {year_expenses:_}, "
            f"Cash flow for year {year}: {cash_flow:_}",
        )
        return cash_flow

    def invest(self, year: int, amount: int) -> None:
        """
        Invest amount into assets with cap, then according to allocation.
        """
        # First, allocate to assets with cap
        capped_assets = [asset for asset in self.assets if asset.cap_value != float("inf")]
        for asset in capped_assets:
            amount_invested = asset.deposit(year, amount)
            amount -= amount_invested
            self._log("info", f"Invested in year {year}: {amount_invested:_} in {asset.name}")

        # Then, allocate to assets with allocation
        allocated_assets = [asset for asset in self.assets if asset.allocation is not None]
        allocated_amounts = [amount * asset.allocation for asset in allocated_assets]
        for asset, allocated_amount in zip(allocated_assets, allocated_amounts):
            amount_invested = asset.deposit(year, allocated_amount)
            self._log("info", f"Invested in year {year}: {amount_invested:_} in {asset.name}")

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
            self._log("info", f"Adding debt for next year: {amount:_}")
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

    def run(self, duration: Optional[int] = None) -> None:
        """
        Run the financial planning simulation.
        """
        self._log("info", "Starting financial planning simulation")
        for year in range(self.start_year, self.start_year + (duration or self.duration)):
            self._log("info", f"Processing year {year}")
            cash_flow = self.balance_cash_flow(year)
            self.distribute_cash_flow(year, cash_flow)
            self.grow_assets(year)
        self._log("info", "Financial planning simulation completed")

    def _plot_values(self, values: List[InOrOutPerYear], ax: Optional[plt.Axes] = None) -> plt.Axes:
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

    def plot_all(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot all values over financial planning duration.
        """
        ax = self.plot_assets(ax)
        self.plot_cash_flow(ax)
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

    def get_flow(self, name: str) -> Optional[InOrOutPerYear]:
        """
        Get a flow by name.
        """
        return self._get_money_by_name(name, self.revenues + self.expenses)
