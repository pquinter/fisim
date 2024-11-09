import pytest

from fisi.flows import TaxableIncome
from fisi.taxes import calculate_total_tax


class TestExpense:
    def test_expense_gets_inflated(self, sample_expense):
        for year in range(2024, 2027):
            sample_expense.grow(year)

        assert sample_expense.get_base_values(2024) == 1_000
        assert sample_expense.get_base_values(2025) == 1_020
        assert abs(sample_expense.get_base_values(2026) - int(1_000 * (1.02**2))) <= 1
        assert abs(sample_expense.get_base_values(2027) - int(1_000 * (1.02**3))) <= 1


class TestTaxableIncome:
    def test_tax_income_for_year(self, sample_taxable_income):
        sample_taxable_income.tax(2024)
        assert sample_taxable_income[2024] == 150_000 - calculate_total_tax(
            150_000, sample_taxable_income.state
        )

    @pytest.mark.parametrize("invalid_state", ["InvalidState", "XX", "WOW"])
    def test_invalid_state(self, invalid_state):
        with pytest.raises(ValueError, match=f"Unsupported state: {invalid_state}"):
            TaxableIncome(
                name="Test Taxable Income",
                initial_value=150_000,
                start_year=2024,
                state=invalid_state,
            )
