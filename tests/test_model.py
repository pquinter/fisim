import pytest

from spear.model import FinancialModel
from spear.utilities import calculate_total_tax


class TestFinancialModelBasics:
    def test_invalid_asset_allocation_raises_error(self, sample_stock, sample_bond):
        with pytest.raises(ValueError, match="Total assets allocation is 1.1 but must sum to 1."):
            sample_stock.allocation = 0.8
            sample_bond.allocation = 0.3
            FinancialModel(
                revenues=[], expenses=[], assets=[sample_stock, sample_bond], duration=10
            )

    def test_valid_asset_allocation_does_not_raise_error(self, sample_stock, sample_bond):
        FinancialModel(revenues=[], expenses=[], assets=[sample_stock, sample_bond], duration=10)

    def test_model_with_logging(
        self, sample_cash, sample_stock, sample_bond, sample_revenue, sample_expense
    ):
        FinancialModel(
            revenues=[sample_revenue],
            expenses=[sample_expense],
            assets=[sample_cash, sample_stock, sample_bond],
            duration=10,
            enable_logging=True,
        )

    def test_get_money_by_name(
        self, basic_model, sample_cash, sample_stock, sample_bond, sample_expense, sample_revenue
    ):
        assert basic_model.get_asset("Test Cash") == sample_cash
        assert basic_model.get_asset("Test Bond") == sample_bond
        assert basic_model.get_asset("Test Stock") == sample_stock
        assert basic_model.get_expense("Test Expense") == sample_expense
        assert basic_model.get_revenue("Test Revenue") == sample_revenue


class TestRunOperations:
    @pytest.fixture(autouse=True)
    def setup(self, basic_model):
        self.basic_model = basic_model
        self.initial_cash_value = self.basic_model.get_asset("Test Cash").get_base_value(2024)
        self.initial_bond_value = self.basic_model.get_asset("Test Bond").get_base_value(2024)
        self.initial_stock_value = self.basic_model.get_asset("Test Stock").get_base_value(2024)

    def test_balance_cash_flow(self):
        """No cash flow in 2024 because revenues equal expenses."""
        assert self.basic_model.balance_cash_flow(2024) == 0

    def test_balance_positive_cash_flow(self, sample_revenue):
        """Add a revenue that creates 1_000 positive cash flow in 2024."""
        self.basic_model.revenues.append(sample_revenue)
        assert self.basic_model.balance_cash_flow(2024) == 1_000

    def test_balance_negative_cash_flow(self, sample_expense):
        """Add an expense that creates 1_000 negative cash flow in 2024."""
        self.basic_model.expenses.append(sample_expense)
        assert self.basic_model.balance_cash_flow(2024) == -1_000

    def test_withdraw_funds_from_cash(self):
        """Withdraw enough funds to impact cash only."""
        to_withdraw = 1_000
        self.basic_model.withdraw_funds(2024, to_withdraw, self.basic_model.assets)
        assert (
            self.basic_model.get_asset("Test Cash").get_base_value(2024)
            == self.initial_cash_value - to_withdraw
        )
        # Stocks and bonds are unchanged
        assert (
            self.basic_model.get_asset("Test Bond").get_base_value(2024) == self.initial_bond_value
        )
        assert (
            self.basic_model.get_asset("Test Stock").get_base_value(2024)
            == self.initial_stock_value
        )

    def test_withdraw_funds_from_bond(self):
        """Withdraw enough funds to impact both cash and bonds, but not stock."""
        to_withdraw = 1_500
        self.basic_model.withdraw_funds(2024, to_withdraw, self.basic_model.assets)
        # Cash is depleted
        assert self.basic_model.get_asset("Test Cash").get_base_value(2024) == 0
        # Bonds are depleted by the amount withdrawn minus the initial cash value
        assert self.basic_model.get_asset("Test Bond").get_base_value(
            2024
        ) == self.initial_bond_value - (to_withdraw - self.initial_cash_value)
        # Stocks are unchanged
        assert (
            self.basic_model.get_asset("Test Stock").get_base_value(2024)
            == self.initial_stock_value
        )

    def test_withdraw_funds_from_stock(self):
        """Withdraw enough funds to impact all assets."""
        to_withdraw = 2_500
        self.basic_model.withdraw_funds(2024, to_withdraw, self.basic_model.assets)
        # Cash is depleted
        assert self.basic_model.get_asset("Test Cash").get_base_value(2024) == 0
        # Bonds are depleted
        assert self.basic_model.get_asset("Test Bond").get_base_value(2024) == 0
        # Stocks are depleted by the amount withdrawn minus the initial cash and bond values
        assert self.basic_model.get_asset("Test Stock").get_base_value(
            2024
        ) == self.initial_stock_value - (
            to_withdraw - self.initial_cash_value - self.initial_bond_value
        )

    def test_withdraw_funds_adds_debt_when_no_assets_can_absorb_negative_cash_flow(self):
        """Withdraw enough funds from assets to leave a deficit, which is added as debt."""
        to_withdraw = 4_000
        self.basic_model.withdraw_funds(2024, to_withdraw, self.basic_model.assets)
        # Debt is added for the deficit
        assert self.basic_model.debt.get_base_value(2025) == 1_000
        # Withdrawing again should just debt
        self.basic_model.withdraw_funds(2024, to_withdraw, self.basic_model.assets)
        assert self.basic_model.debt.get_base_value(2025) == 5_000

    def test_invest_in_capped_cash(self):
        """Invest money only sufficient to impact capped assets."""
        to_invest = 500
        self.basic_model.invest(2024, to_invest)
        # Cash increases
        assert (
            self.basic_model.get_asset("Test Cash").get_base_value(2024)
            == self.initial_cash_value + to_invest
        )
        # But bonds and stocks are unchanged
        assert (
            self.basic_model.get_asset("Test Bond").get_base_value(2024) == self.initial_bond_value
        )
        assert (
            self.basic_model.get_asset("Test Stock").get_base_value(2024)
            == self.initial_stock_value
        )

    def test_invest_in_bonds_and_stocks(self):
        """Invest sufficient money to fill cash cap and allocate remaining to bonds and stocks."""
        # Should leave 2_000 to invest
        to_invest = 2_500
        self.basic_model.invest(2024, to_invest)
        # Cash increases
        assert self.basic_model.get_asset("Test Cash").get_base_value(2024) == 1_500
        # Bonds and stocks increase according to allocation, 1_000 each
        assert self.basic_model.get_asset("Test Bond").get_base_value(2024) == 2_000
        assert self.basic_model.get_asset("Test Stock").get_base_value(2024) == 2_000

    def test_invest_in_pretax_asset(
        self, sample_pretax_asset_with_cap_deposit, sample_taxable_income
    ):
        """Invest investing in 401k, from pretax income, with a cap on deposit amount."""
        initial_taxable_income = sample_taxable_income.get_base_value(2024)
        self.basic_model.revenues.append(sample_taxable_income)
        self.basic_model.assets.append(sample_pretax_asset_with_cap_deposit)
        to_invest = 2_500
        invested = self.basic_model.invest_pre_tax(2024, to_invest)
        # 401k increases by cap deposit amount, not full amount
        assert self.basic_model.get_asset("Test 401k").get_base_value(2024) == 1_500
        # Only taxable income is reduced by 401k deposit
        assert sample_taxable_income.get_base_value(2024) == initial_taxable_income - invested
        # Cash and assets are unchanged
        assert (
            self.basic_model.get_asset("Test Cash").get_base_value(2024) == self.initial_cash_value
        )
        assert (
            self.basic_model.get_asset("Test Bond").get_base_value(2024) == self.initial_bond_value
        )
        assert (
            self.basic_model.get_asset("Test Stock").get_base_value(2024)
            == self.initial_stock_value
        )

    def test_tax_revenues(self, sample_taxable_income):
        """Taxable income should be taxed."""
        self.basic_model.revenues.append(sample_taxable_income)
        self.basic_model.tax_revenues(2024)
        assert sample_taxable_income.get_base_value(2024) == 150_000 - calculate_total_tax(
            150_000, sample_taxable_income.state
        )


class TestRun:
    def test_run_with_no_errors(self, basic_model):
        basic_model.run()

    def test_run_with_logging(
        self, sample_cash, sample_stock, sample_bond, sample_revenue, sample_expense
    ):
        FinancialModel(
            revenues=[sample_revenue],
            expenses=[sample_expense],
            assets=[sample_cash, sample_stock, sample_bond],
            duration=10,
            enable_logging=True,
        ).run()

    def test_order_of_operations(self, basic_model):
        """Cash should first be balanced, then distributed, then assets grown."""
        # Mock the methods to track their call order
        call_order = []

        def mock_balance_cash_flow(y):
            call_order.append("balance")
            return 1000  # Return a dummy cash flow value

        basic_model.balance_cash_flow = mock_balance_cash_flow
        basic_model.invest_pre_tax = lambda y, a: call_order.append("invest_pre_tax")
        basic_model.tax_revenues = lambda y: call_order.append("tax_revenues")
        basic_model.distribute_cash_flow = lambda y, f: call_order.append("distribute")
        basic_model.grow_assets = lambda y: call_order.append("grow")
        basic_model.add_inflation = lambda y: call_order.append("add_inflation")

        # Run the simulation for one year
        basic_model.run(duration=1)
        # Check if the methods were called in the correct order
        expected_call_order = [
            "balance",
            "invest_pre_tax",
            "tax_revenues",
            "balance",
            "distribute",
            "grow",
            "add_inflation",
        ]
        assert (
            call_order == expected_call_order
        ), f"Expected call order {expected_call_order}, but got {call_order}"


class TestApplyEvents:
    def test_apply_events(self):
        pass
