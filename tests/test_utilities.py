import pytest

from fisi.taxes import calculate_tax_liability, calculate_total_tax


class TestTaxes:
    def test_calculate_total_tax(self):
        assert calculate_total_tax(150_000, "MA") == pytest.approx(37_000, rel=0.01)
        assert calculate_total_tax(150_000, "CA") == pytest.approx(40_000, rel=0.01)

    def test_calculate_tax_liability(self):
        assert calculate_tax_liability(150_000, "MA") == pytest.approx(7_500, rel=0.01)
        assert calculate_tax_liability(150_000, "CA") == pytest.approx(10_000, rel=0.1)

    def test_calculate_tax_liability_for_federal_tax(self):
        assert calculate_tax_liability(150_000, None) == pytest.approx(30_000, rel=0.1)
