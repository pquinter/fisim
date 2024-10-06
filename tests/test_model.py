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
    def test_balance_cash_flow(self, basic_model):
        assert basic_model._balance_cash_flow(2024) == 0

    def test_balance_positive_cash_flow(self, basic_model, sample_revenue):
        # This adds 1_000 to the cash flow in 2024
        basic_model.revenues.append(sample_revenue)
        assert basic_model._balance_cash_flow(2024) == 1_000

    def test_balance_negative_cash_flow(self, basic_model, sample_revenue):
        # This subtracts 1_000 from the cash flow in 2024
        basic_model.expenses.append(sample_revenue)
        assert basic_model._balance_cash_flow(2024) == -1_000

    def test_withdraw_funds_from_cash(self, basic_model):
        initial_cash_value = basic_model.get_asset("Test Cash").get_base_value(2024)
        initial_bond_value = basic_model.get_asset("Test Bond").get_base_value(2024)
        initial_stock_value = basic_model.get_asset("Test Stock").get_base_value(2024)

        to_withdraw = 1_000
        basic_model._withdraw_funds(2024, to_withdraw, basic_model.assets)

        assert (
            basic_model.get_asset("Test Cash").get_base_value(2024)
            == initial_cash_value - to_withdraw
        )
        assert basic_model.get_asset("Test Bond").get_base_value(2024) == initial_bond_value
        assert basic_model.get_asset("Test Stock").get_base_value(2024) == initial_stock_value

    def test_invest(self, basic_model):
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
