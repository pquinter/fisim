import pytest

from spear.assets import Asset
from spear.flows import Expense, InOrOutPerYear
from spear.model import FinancialModel


@pytest.fixture
def sample_revenue():
    return InOrOutPerYear(name="Test Revenue", initial_value=1_000, duration=10, start_year=2024)


@pytest.fixture
def sample_expense():
    return Expense(
        name="Test Expense", initial_value=1_000, duration=10, inflation_rate=0.02, start_year=2024
    )


@pytest.fixture
def sample_cash():
    return Asset(
        name="Test Cash",
        initial_value=1_000,
        start_year=2024,
        cap_value=1_500,
        growth_rate=0.01,
    )


@pytest.fixture
def sample_stock():
    return Asset(
        name="Test Stock",
        initial_value=1_000,
        start_year=2024,
        growth_rate=0.05,
        allocation=0.5,
    )


@pytest.fixture
def sample_bond():
    return Asset(
        name="Test Bond",
        initial_value=1_000,
        start_year=2024,
        growth_rate=0.05,
        allocation=0.5,
    )


@pytest.fixture
def basic_model(sample_revenue, sample_expense, sample_stock, sample_bond, sample_cash):
    return FinancialModel(
        revenues=[sample_revenue],
        expenses=[sample_expense],
        assets=[sample_cash, sample_bond, sample_stock],
        duration=10,
    )
