import pytest

from spear.assets import Asset
from spear.flows import InOrOutPerYear
from spear.model import FinancialModel


@pytest.fixture
def sample_flow():
    return InOrOutPerYear(
        name="Test Flow", initial_value=1_000, duration=10, multiplier=1.05, start_year=2024
    )


@pytest.fixture
def sample_capped_asset():
    return Asset(
        name="Test Capped Asset",
        initial_value=1_000,
        start_year=2024,
        duration=10,
        cap_value=1_500,
        growth_rate=0.05,
    )


@pytest.fixture
def sample_stock():
    return Asset(
        name="Test Stock",
        initial_value=1_000,
        start_year=2024,
        duration=10,
        growth_rate=0.05,
        allocation=0.5,
    )


@pytest.fixture
def basic_model():
    revenues = [InOrOutPerYear("Salary", 100000, 2023, 10)]
    expenses = [InOrOutPerYear("Living Expenses", 70000, 2023, 10)]
    assets = [
        Asset("Stocks", 50000, 2023, 10, allocation=0.7),
        Asset("Bonds", 20000, 2023, 10, allocation=0.3),
    ]
    return FinancialModel(revenues, expenses, assets, duration=10)
