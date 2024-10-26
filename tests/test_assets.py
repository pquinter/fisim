import matplotlib.pyplot as plt
import numpy as np
import pytest


class TestAsset:
    def test_initialization_with_cap_and_allocation(self, sample_cash):
        assert sample_cash.cap_value == 1_500

    def test_deposit_less_than_cap(self, sample_cash):
        to_deposit = np.array([500])
        deposited = sample_cash.deposit(2024, to_deposit)
        assert deposited == 500
        assert sample_cash.get_base_values(2024) == 1500

    def test_deposit_more_than_cap(self, sample_cash):
        to_deposit = np.array([1_000])
        deposited = sample_cash.deposit(2024, to_deposit)
        assert deposited == 500
        assert sample_cash.get_base_values(2024) == 1_500

    def test_deposit_with_cap_deposit(self, sample_stock_with_cap_deposit):
        to_deposit = np.array([1_000])
        deposited = sample_stock_with_cap_deposit.deposit(2024, to_deposit)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_values(2024) == 2_000

    def test_deposit_more_than_cap_deposit(self, sample_stock_with_cap_deposit):
        to_deposit = np.array([2_000])
        deposited = sample_stock_with_cap_deposit.deposit(2024, to_deposit)
        assert deposited == 1_000
        assert sample_stock_with_cap_deposit.get_base_values(2024) == 2_000

    def test_validate_and_set_parameter(self, sample_stock):
        with pytest.raises(TypeError):
            sample_stock._validate_and_set_parameter("cap_deposit", 100_000, {"cap_deposit": 1_000})

    def test_plot_growth_rates(self, sample_stock):
        ax = sample_stock.plot_growth_rates()
        assert len(ax.get_lines()[0].get_xdata()) == sample_stock.duration
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_sample_growth_rates(self, sample_stock_with_growth_type):
        sample_stock_with_growth_type._sample_growth_rates()
        assert (
            len(sample_stock_with_growth_type.multipliers)
            == sample_stock_with_growth_type.number_of_simulations
        )
        assert sample_stock_with_growth_type.multipliers.shape == (
            sample_stock_with_growth_type.number_of_simulations,
            sample_stock_with_growth_type.duration,
        )


class TestTaxableAsset:
    @pytest.fixture(autouse=True)
    def setup(self, sample_taxable_stock):
        self.sample_taxable_stock = sample_taxable_stock
        for year in range(2024, 2031):
            self.sample_taxable_stock.grow(year)

    def test_get_cumulative_capital_gains(self):
        assert self.sample_taxable_stock.get_cumulative_capital_gains(2024) == 0
        assert self.sample_taxable_stock.get_cumulative_capital_gains(2030) == pytest.approx(
            154_312, rel=1_000
        )

    def test_calculate_gross_withdrawal_less_than_available(self):
        to_withdraw = 250_000
        (
            gross_withdrawn,
            net_withdrawn,
            capital_gains,
        ) = self.sample_taxable_stock._calculate_gross_withdrawal(2030, to_withdraw)
        assert gross_withdrawn == pytest.approx(
            267_477, rel=0.001
        ), "Gross withdrawn amount is incorrect"
        assert net_withdrawn == pytest.approx(
            250_000, rel=0.001
        ), "Net withdrawn amount is incorrect"
        assert capital_gains == pytest.approx(
            116_493, rel=0.001
        ), "Capital gains amount is incorrect"

    def test_calculate_gross_withdrawal_more_than_available(self):
        to_withdraw = 400_000
        (
            gross_withdrawn,
            net_withdrawn,
            capital_gains,
        ) = self.sample_taxable_stock._calculate_gross_withdrawal(2030, to_withdraw)
        assert gross_withdrawn == pytest.approx(
            354_312, rel=0.001
        ), "Gross withdrawn amount is incorrect"
        assert net_withdrawn == pytest.approx(
            331_165, rel=0.001
        ), "Net withdrawn amount is incorrect"
        assert capital_gains == pytest.approx(
            154_312, rel=0.001
        ), "Capital gains amount is incorrect"

    def test_withdraw(self):
        to_withdraw = 250_000
        net_withdrawn = self.sample_taxable_stock.withdraw(2030, to_withdraw)
        assert net_withdrawn == pytest.approx(250_000, rel=0.001)


class TestPretaxAsset:
    def test_calculate_gross_withdrawal_less_than_available_and_early_withdrawal_penalty(
        self, sample_pretax_asset
    ):
        to_withdraw = 100_000
        (
            gross_withdrawn,
            net_withdrawn,
        ) = sample_pretax_asset._calculate_gross_withdrawal(2024, to_withdraw)
        assert gross_withdrawn == pytest.approx(
            153_114, rel=0.001
        ), "Gross withdrawn amount is incorrect"
        assert net_withdrawn == pytest.approx(
            100_000, rel=0.001
        ), "Net withdrawn amount is incorrect"

    def test_calculate_gross_withdrawal_less_than_available_and_no_early_withdrawal_penalty(
        self, sample_pretax_asset
    ):
        sample_pretax_asset.age = 60
        to_withdraw = 100_000
        (
            gross_withdrawn,
            net_withdrawn,
        ) = sample_pretax_asset._calculate_gross_withdrawal(2024, to_withdraw)
        assert gross_withdrawn == pytest.approx(
            131_548, rel=0.001
        ), "Gross withdrawn amount is incorrect"
        assert net_withdrawn == pytest.approx(
            100_000, rel=0.001
        ), "Net withdrawn amount is incorrect"

    def test_withdraw_less_than_available_with_early_withdrawal_penalty(self, sample_pretax_asset):
        to_withdraw = 100_000
        net_withdrawn = sample_pretax_asset.withdraw(2024, to_withdraw)
        assert net_withdrawn == pytest.approx(to_withdraw, rel=0.001)

    def test_withdraw_more_than_available(self, sample_pretax_asset):
        to_withdraw = 300_000
        net_withdrawn = sample_pretax_asset.withdraw(2024, to_withdraw)
        assert net_withdrawn == pytest.approx(127_168, rel=0.001)

    def test_validate_withdrawal_parameters_without_age(self, sample_pretax_asset):
        sample_pretax_asset.age = None
        with pytest.raises(ValueError):
            sample_pretax_asset._validate_withdrawal_parameters()

    def test_validate_withdrawal_parameters_without_state(self, sample_pretax_asset):
        sample_pretax_asset.state = None
        with pytest.raises(ValueError):
            sample_pretax_asset._validate_withdrawal_parameters()


class TestPortfolio:
    def test_rebalancing_taxable_portfolio(self, sample_taxable_portfolio):
        multipliers = sample_taxable_portfolio.multipliers
        assert (
            np.mean(np.diff(np.mean(multipliers, axis=0))) < 0
        ), "Mean should decrease over time on average"
        assert (
            np.mean(np.diff(np.std(multipliers, axis=0))) < 0
        ), "Stdev should decrease over time on average"

    def test_rebalancing_pretax_portfolio(self, sample_pretax_portfolio):
        multipliers = sample_pretax_portfolio.multipliers
        assert (
            np.mean(np.diff(np.mean(multipliers, axis=0))) < 0
        ), "Mean should decrease over time on average"
        assert (
            np.mean(np.diff(np.std(multipliers, axis=0))) < 0
        ), "Stdev should decrease over time on average"

    def test_plot_pretax_portfolio(self, sample_pretax_portfolio):
        ax = sample_pretax_portfolio.plot()
        assert len(ax.get_lines()[0].get_xdata()) == sample_pretax_portfolio.duration
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_plot_pretax_portfolio_split(self, sample_pretax_portfolio):
        ax = sample_pretax_portfolio.plot(split=True)
        assert len(ax.get_lines()[0].get_xdata()) == sample_pretax_portfolio.duration
        assert len(ax.get_lines()) == 2
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_plot_taxable_portfolio(self, sample_taxable_portfolio):
        ax = sample_taxable_portfolio.plot()
        assert len(ax.get_lines()[0].get_xdata()) == sample_taxable_portfolio.duration
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)

    def test_plot_taxable_portfolio_split(self, sample_taxable_portfolio):
        ax = sample_taxable_portfolio.plot(split=True)
        assert len(ax.get_lines()[0].get_xdata()) == sample_taxable_portfolio.duration
        assert len(ax.get_lines()) == 2
        # Close figure to avoid messing with other plot tests
        plt.close(ax.figure)
