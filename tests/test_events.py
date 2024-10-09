import pytest

from spear.events import Action


class TestAction:
    """Test actions that don't require a year, which comes from Event."""

    def test_action_raises_error_with_invalid_parameters(self, sample_taxable_income):
        with pytest.raises(ValueError, match="Invalid parameters"):
            Action(target=sample_taxable_income, action="withdraw", params={"bad_param": 0})

    def test_action_raises_error_with_invalid_target(self, sample_taxable_income):
        with pytest.raises(ValueError, match=".*has no action.*"):
            Action(target=sample_taxable_income, action="bad_method", params={})

    def test_action_updates_cap_deposit(self, sample_pretax_asset_with_cap_deposit):
        Action(
            target=sample_pretax_asset_with_cap_deposit,
            action="update_cap_deposit",
            params={"cap_deposit": 0},
        ).apply()
        assert sample_pretax_asset_with_cap_deposit.cap_deposit == 0


class TestEvent:
    """Test events, and actions that require a year, which comes from Event."""

    def test_event_stops_taxable_income(
        self, sample_event_stop_taxable_income, sample_taxable_income
    ):
        """Stops recurring taxable income at start year, by zeroing it out."""
        action = sample_event_stop_taxable_income.actions[0]
        year = action.params["year"]
        duration = action.params["duration"]
        sample_event_stop_taxable_income.apply()
        for y in range(year, min(year + duration, len(sample_taxable_income.base_value))):
            assert sample_taxable_income.get_base_value(y) == 0

    def test_event_stop_investing_in_401k(
        self, sample_event_stop_investing_in_401k, sample_pretax_asset_with_cap_deposit
    ):
        """Stops investing in 401k after 2026, by setting cap_deposit to 0."""
        sample_event_stop_investing_in_401k.apply()
        assert sample_pretax_asset_with_cap_deposit.cap_deposit == 0

    def test_event_buy_house(self, sample_event_buy_house, sample_cash):
        """Withdraws from cash asset to buy a house."""
        year = sample_event_buy_house.year
        sample_event_buy_house.apply()
        assert sample_cash.get_base_value(year) == 495
