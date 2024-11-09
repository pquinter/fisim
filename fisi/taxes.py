from typing import Optional, Union

import numpy as np

from fisi.constants import (
    FEDERAL_TAX_RATES,
    LONG_TERM_CAPITAL_GAINS_TAX_BRACKETS,
    STATE_TAX_RATES,
    EarlyWithdrawal,
)


def calculate_tax_liability(
    incomes: Union[int, np.ndarray], state: Optional[str] = None
) -> Union[float, np.ndarray]:
    """
    Calculate the total tax liability for the given income.
    Applies progressive tax rates based on the defined brackets.

    Parameters
    ----------
    income : int
        The taxable income.
    state : str, optional, default to None
        State to calculate tax for. If None, calculate federal tax.

    Returns
    -------
    float
        Total tax owed.
    """
    tax_brackets = STATE_TAX_RATES[state] if state else FEDERAL_TAX_RATES
    sorted_brackets = sorted(tax_brackets.items(), key=lambda item: item[1])

    incomes = np.atleast_1d(np.asarray(incomes))
    total_tax = np.zeros_like(incomes, dtype=float)

    previous_bracket = 0
    for rate, bracket in sorted_brackets:
        # Calculate the taxable amount for the current bracket
        applicable_income = np.clip(incomes - previous_bracket, 0, bracket - previous_bracket)
        # Calculate the tax for the applicable income and add it to the total tax
        total_tax += (rate / 100) * applicable_income
        # Update the previous bracket limit
        previous_bracket = bracket

    return total_tax


def calculate_total_tax(incomes: Union[int, np.ndarray], state: str) -> Union[int, np.ndarray]:
    """
    Calculate the total federal and state tax liability for the given income.

    Parameters
    ----------
    income : int
        The taxable income.
    state : str
        State to calculate tax for.

    Returns
    -------
    Union[int, np.ndarray]
        Total tax owed.
    """
    state_tax = calculate_tax_liability(incomes, state)
    federal_tax = calculate_tax_liability(incomes, state=None)
    total_tax = state_tax + federal_tax
    return total_tax


def calculate_capital_gain_tax_rate(taxable_income: np.ndarray) -> np.ndarray:
    """
    Calculate the long-term capital gains tax rate based on taxable income.

    Parameters
    ----------
    taxable_income : np.ndarray
        The expected taxable income including capital gains.

    Returns
    -------
    np.ndarray
        The applicable long-term capital gains tax rate for each simulation.
    """
    tax_rates = np.zeros_like(taxable_income)
    higher_threshold = 100_000_000
    for threshold, rate in reversed(LONG_TERM_CAPITAL_GAINS_TAX_BRACKETS):
        tax_rates = np.where(
            np.logical_and(taxable_income >= threshold, taxable_income < higher_threshold),
            rate,
            tax_rates,
        )
        higher_threshold = threshold
    return tax_rates


def calculate_pretax_withdrawal_tax_rate(incomes: np.ndarray, state: str, age: int) -> np.ndarray:
    """
    Calculate the early withdrawal tax rate for the given age.

    Parameters
    ----------
    age : int
        The age of the investor.

    Returns
    -------
    float
        The early withdrawal tax rate for the given age.
    """
    total_taxes = calculate_total_tax(incomes, state)
    # Prevent divide by zero
    tax_rate = np.divide(total_taxes, incomes, out=np.zeros_like(total_taxes), where=incomes != 0)
    if age < EarlyWithdrawal.AGE.value:
        tax_rate += EarlyWithdrawal.PENALTY.value
    return tax_rate
