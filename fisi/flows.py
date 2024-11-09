"""
Cash flow classes for financial planning model
"""


import numpy as np

from fisi.base import InOrOutPerYear
from fisi.constants import STATE_TAX_RATES
from fisi.taxes import calculate_total_tax


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

    def tax(self, year: int) -> np.ndarray:
        """
        Subtract state and federal taxes from year's income.
        Return amount taxed.
        """
        income = self.get_base_values(year)
        tax_amount = calculate_total_tax(income, self.state)
        self.update_base_values(year, income - tax_amount)
        return tax_amount
