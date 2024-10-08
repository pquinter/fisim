import pytest

from spear.events import Action


class TestAction:
    def test_action_raises_error_with_invalid_parameters(self, sample_taxable_income):
        with pytest.raises(ValueError, match="Invalid parameters"):
            Action(target=sample_taxable_income, action="withdraw", params={"bad_param": 0})

    def test_action_updates_base_value_for_duration(
        self,
        sample_action_update_taxable_income,
        sample_taxable_income,
    ):
        start_year = sample_action_update_taxable_income.params["start_year"]
        duration = sample_action_update_taxable_income.params["duration"]
        new_base_value = sample_action_update_taxable_income.params["base_value"]
        sample_action_update_taxable_income.apply()
        for year in range(
            start_year, min(start_year + duration, len(sample_taxable_income.base_value))
        ):
            assert sample_taxable_income.get_base_value(year) == new_base_value

    def test_action_raises_error_with_invalid_target(self, sample_taxable_income):
        with pytest.raises(ValueError, match=".*has no action.*"):
            Action(target=sample_taxable_income, action="bad_method", params={})

    def test_action_withdraws_cash(self, sample_action_withdraw_cash, sample_cash):
        initial_cash = sample_cash.get_base_value(sample_action_withdraw_cash.params["year"])
        sample_action_withdraw_cash.apply()
        assert (
            sample_cash.get_base_value(sample_action_withdraw_cash.params["year"])
            == initial_cash - sample_action_withdraw_cash.params["amount"]
        )

    def test_action_updates_cap_deposit(
        self, sample_action_change_cap_deposit, sample_pretax_asset_with_cap_deposit
    ):
        sample_action_change_cap_deposit.apply()
        assert sample_pretax_asset_with_cap_deposit.cap_deposit == 0


class TestEvent:
    def test_event_stop_taxable_income(
        self, sample_event_stop_taxable_income, sample_taxable_income
    ):
        """Stops recurring taxable income at start year, by zeroing it out."""
        event_start_year = sample_event_stop_taxable_income.start_year
        sample_event_stop_taxable_income.apply()
        assert sample_taxable_income.get_base_value(event_start_year) == 0

    def test_event_stop_investing_in_401k(
        self, sample_event_stop_investing_in_401k, sample_pretax_asset_with_cap_deposit
    ):
        """Stops investing in 401k after 2026, by setting cap_deposit to 0."""
        sample_event_stop_investing_in_401k.apply()
        assert sample_pretax_asset_with_cap_deposit.cap_deposit == 0

    def test_event_buy_house(self, sample_event_buy_house, sample_cash):
        """Withdraws from cash asset to buy a house."""
        event_start_year = sample_event_buy_house.start_year
        sample_event_buy_house.apply()
        assert sample_cash.get_base_value(event_start_year) == 495
