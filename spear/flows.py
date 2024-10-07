"""
Cash flow classes for financial planning model
"""

from spear.base import InOrOutPerYear
from spear.constants import STATE_TAX_RATES
from spear.utilities import calculate_total_tax


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

    def tax(self, year: int) -> int:
        """
        Subtract state and federal taxes from year's income.
        Return amount taxed.
        """
        year_index = self._convert_year_to_index(year)
        tax_amount = calculate_total_tax(self.base_value[year_index], self.state)
        self.base_value[year_index] -= tax_amount
        return tax_amount

    def withdraw(self, year: int, amount: int) -> int:
        """
        Withdraw amount from income.
        Return amount withdrawn, depending on available funds.
        """
        year_index = self._convert_year_to_index(year)
        available_amount = self.base_value[year_index]
        amount_withdrawn = min(available_amount, amount)
        self.base_value[year_index] -= amount_withdrawn
        return amount_withdrawn
