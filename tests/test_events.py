import matplotlib.pyplot as plt
import numpy as np
import pytest

from fisi.events import Action


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

    def test_action_updates_base_values_with_duration(self, sample_revenue):
        Action(
            target=sample_revenue,
            action="update_base_values",
            params={"year": 2025, "new_base_values": 2_000, "duration": 5},
        ).apply()
        assert sample_revenue.get_base_values(2024) == 1_000
        assert sample_revenue.get_base_values(2025) == 2_000
        assert sample_revenue.get_base_values(2029) == 2_000
        assert sample_revenue.get_base_values(2030) == 1_000


class TestEvent:
    """Test events, and actions that require a year, which comes from Event."""

    def test_event_stops_taxable_income(
        self, sample_event_stop_taxable_income, sample_taxable_income
    ):
        """Stops recurring taxable income at start year, by zeroing it out."""
        action = sample_event_stop_taxable_income.actions[0]
        year = action.params["year"]
        sample_event_stop_taxable_income.apply()
        assert np.all(sample_taxable_income.base_values[year:] == 0)

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
        assert sample_cash.get_base_values(year) == 495

    def test_event_buy_house_with_mortgage(
        self, sample_event_buy_house_with_mortgage, sample_mortgage
    ):
        sample_event_buy_house_with_mortgage.apply()
        assert sample_mortgage.get_base_values(2029) == 0
        assert sample_mortgage.get_base_values(2030) == 1_000
        assert sample_mortgage.get_base_values(2039) == 1_000
        assert sample_mortgage.get_base_values(2040) == 0

    def test_event_plot(self, sample_event_buy_house):
        ax = sample_event_buy_house.plot()
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)
