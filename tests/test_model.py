import pytest

from spear.model import FinancialModel


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


class TestRunOperations:
    @pytest.fixture(autouse=True)
    def setup(self, basic_model):
        self.basic_model = basic_model
        self.initial_cash_value = self.basic_model.get_asset("Test Cash").get_base_value(2024)
        self.initial_bond_value = self.basic_model.get_asset("Test Bond").get_base_value(2024)
        self.initial_stock_value = self.basic_model.get_asset("Test Stock").get_base_value(2024)

    def test_balance_cash_flow(self):
        """No cash flow in 2024 because revenues equal expenses."""
        assert self.basic_model._balance_cash_flow(2024) == 0

    def test_balance_positive_cash_flow(self, sample_revenue):
        """Add a revenue that creates 1_000 positive cash flow in 2024."""
        self.basic_model.revenues.append(sample_revenue)
        assert self.basic_model._balance_cash_flow(2024) == 1_000

    def test_balance_negative_cash_flow(self, sample_expense):
        """Add an expense that creates 1_000 negative cash flow in 2024."""
        self.basic_model.expenses.append(sample_expense)
        assert self.basic_model._balance_cash_flow(2024) == -1_000

    def test_withdraw_funds_from_cash(self):
        """Withdraw enough funds to impact cash only."""
        to_withdraw = 1_000
        self.basic_model._withdraw_funds(2024, to_withdraw, self.basic_model.assets)

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
        self.basic_model._withdraw_funds(2024, to_withdraw, self.basic_model.assets)

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
        self.basic_model._withdraw_funds(2024, to_withdraw, self.basic_model.assets)

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

    def test_invest(self):
        pass


class TestRun:
    def test_run_with_no_errors(self, basic_model):
        basic_model.run()

    def test_order_of_operations(self, basic_model):
        # Mock the methods to track their call order
        call_order = []
        basic_model._balance_cash_flow = lambda y: call_order.append("balance")
        basic_model._distribute_cash_flow = lambda y, f: call_order.append("distribute")
        basic_model._grow_assets = lambda y: call_order.append("grow")

        # Run the simulation for one year
        basic_model.run(duration=1)

        # Check if the methods were called in the correct order
        assert call_order == [
            "balance",
            "distribute",
            "grow",
        ], f"Expected call order 'balance', 'distribute', 'grow', but got {call_order}"


class TestApplyEvents:
    def test_apply_events(self):
        pass
