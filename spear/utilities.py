from typing import Optional

from spear.constants import FEDERAL_TAX_RATES, STATE_TAX_RATES


def calculate_tax_liability(income: int, state: Optional[str] = None) -> float:
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

    total_tax = 0.0
    previous_bracket_limit = 0.0

    for rate, bracket in sorted_brackets:
        applicable_income = min(income, bracket) - previous_bracket_limit
        if applicable_income > 0:
            total_tax += (rate / 100) * applicable_income
            previous_bracket_limit = bracket
        if income <= bracket:
            break

    return total_tax


def calculate_total_tax(income: int, state: str) -> int:
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
    int
        Total tax owed.
    """
    state_tax = calculate_tax_liability(income, state)
    federal_tax = calculate_tax_liability(income, state=None)
    return int(state_tax + federal_tax)
