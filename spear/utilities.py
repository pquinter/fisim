from typing import Optional, Union

import numpy as np

from spear.constants import FEDERAL_TAX_RATES, STATE_TAX_RATES


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

    # Return scalar if input was scalar, otherwise return array
    return total_tax[0] if len(total_tax) == 1 else total_tax


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
    return np.round(total_tax).astype(int)
