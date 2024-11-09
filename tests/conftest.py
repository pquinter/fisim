import pytest

from fisi.assets import (
    Asset,
    PretaxAsset,
    PretaxPortfolio,
    TaxableAsset,
    TaxablePortfolio,
)
from fisi.events import Action, Event
from fisi.flows import Expense, InOrOutPerYear, TaxableIncome
from fisi.growth import GrowthType
from fisi.model import FinancialModel


@pytest.fixture
def sample_revenue():
    return InOrOutPerYear(name="Test Revenue", initial_value=1_000, duration=10, start_year=2024)


@pytest.fixture
def sample_taxable_income():
    return TaxableIncome(
        name="Test Taxable Income", initial_value=150_000, start_year=2024, state="MA"
    )


@pytest.fixture
def sample_expense():
    return Expense(
        name="Test Expense", initial_value=1_000, duration=10, inflation_rate=0.02, start_year=2024
    )


@pytest.fixture
def sample_mortgage():
    return Expense(
        name="Test Mortgage", initial_value=0, duration=100, inflation_rate=0.06, start_year=2024
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
def sample_stock_with_cap_deposit():
    return Asset(
        name="Test Stock with Capped Deposit",
        initial_value=1_000,
        start_year=2024,
        growth_rate=0.01,
        cap_deposit=1_000,
    )


@pytest.fixture
def sample_stock_with_growth_type():
    return Asset(
        name="Test Stock with Growth Type",
        initial_value=1_000,
        start_year=2024,
        growth_type=GrowthType.STOCKS,
    )


@pytest.fixture
def sample_taxable_stock():
    return TaxableAsset(
        name="Test Stock for Capital Gains",
        initial_value=200_000,
        start_year=2024,
        growth_rate=0.1,
        allocation=0.5,
    )


@pytest.fixture
def sample_pretax_asset_with_cap_deposit():
    return Asset(
        name="Test 401k",
        initial_value=1_000,
        start_year=2024,
        growth_rate=0.01,
        pretax=True,
        cap_deposit=500,
    )


@pytest.fixture
def sample_pretax_asset():
    return PretaxAsset(
        name="Test 401k",
        initial_value=200_000,
        start_year=2024,
        growth_rate=0.05,
        pretax=True,
        age=30,
        state="MA",
    )


@pytest.fixture
def sample_taxable_portfolio():
    return TaxablePortfolio(
        name="Test Taxable Portfolio",
        initial_value=1_000,
        start_year=2024,
        age=30,
        number_of_simulations=1_000,
    )


@pytest.fixture
def sample_pretax_portfolio():
    return PretaxPortfolio(
        name="Test Pretax Portfolio",
        initial_value=1_000,
        start_year=2024,
        age=30,
        state="MA",
        number_of_simulations=1_000,
    )


@pytest.fixture
def basic_model(sample_revenue, sample_expense, sample_stock, sample_bond, sample_cash):
    return FinancialModel(
        revenues=[sample_revenue],
        expenses=[sample_expense],
        assets=[sample_cash, sample_bond, sample_stock],
        duration=10,
        age=30,
    )


@pytest.fixture
def model_with_simulations(
    sample_revenue, sample_expense, sample_stock, sample_bond, sample_cash, sample_pretax_asset
):
    return FinancialModel(
        revenues=[sample_revenue],
        expenses=[sample_expense],
        assets=[sample_cash, sample_bond, sample_stock, sample_pretax_asset],
        duration=10,
        age=30,
        number_of_simulations=1_000,
    )


@pytest.fixture
def sample_action_update_taxable_income(sample_taxable_income):
    return Action(
        target=sample_taxable_income,
        action="update_base_values",
        params={"new_base_values": 0, "duration": 100},
    )


@pytest.fixture
def sample_action_change_cap_deposit(sample_pretax_asset_with_cap_deposit):
    return Action(
        target=sample_pretax_asset_with_cap_deposit,
        action="update_cap_deposit",
        params={"cap_deposit": 0},
    )


@pytest.fixture
def sample_action_withdraw_cash(sample_cash):
    return Action(target=sample_cash, action="withdraw", params={"amount": 505})


@pytest.fixture
def sample_event_stop_taxable_income(sample_action_update_taxable_income):
    return Event(name="Retirement", year=2030, actions=[sample_action_update_taxable_income])


@pytest.fixture
def sample_event_stop_investing_in_401k(sample_action_change_cap_deposit):
    return Event(
        name="Stop Investing in 401k", year=2026, actions=[sample_action_change_cap_deposit]
    )


@pytest.fixture
def sample_event_buy_house(sample_action_withdraw_cash):
    return Event(name="Buy House", year=2024, actions=[sample_action_withdraw_cash])


@pytest.fixture
def sample_event_buy_house_with_mortgage(sample_mortgage):
    return Event(
        name="Buy House",
        year=2030,
        actions=[
            Action(
                target=sample_mortgage,
                action="update_base_values",
                params={"new_base_values": 1_000, "duration": 10},
            )
        ],
    )


@pytest.fixture
def model_with_events(
    basic_model,
    sample_event_stop_investing_in_401k,
    sample_event_stop_taxable_income,
    sample_event_buy_house,
):
    model = basic_model
    model.events = [
        sample_event_stop_investing_in_401k,
        sample_event_stop_taxable_income,
        sample_event_buy_house,
    ]
    return model


@pytest.fixture
def model_with_portfolios(
    sample_revenue, sample_expense, sample_taxable_portfolio, sample_pretax_portfolio
):
    return FinancialModel(
        revenues=[sample_revenue],
        expenses=[sample_expense],
        assets=[sample_taxable_portfolio, sample_pretax_portfolio],
        duration=10,
        age=30,
    )
